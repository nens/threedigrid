# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Main entry point for threedigrid applications.
"""
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import logging

import h5py
import numpy as np

from threedigrid.geo_utils import transform_bbox

from threedigrid.admin.lines.models import Lines
from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.nodes.models import Cells
from threedigrid.admin.nodes.models import Grid
from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.pumps.models import Pumps
from threedigrid.admin.levees.models import Levees
from threedigrid.admin.h5py_datasource import H5pyGroup
from . import constants
import six

logger = logging.getLogger(__name__)


class GridH5Admin(object):
    """
    Parses the hdf5 gridadmin file and exposes the model instances, e.g.::

        >>> ga = GridH5Admin(file_path)
        >>> ga.nodes
        >>> ga.lines
        >>> ...
    """

    def __init__(self, h5_file_path, file_modus='r'):
        """
        :param h5_file_path: path to the gridadmin file
        :param file_modus: mode with which to open the file
            (defaults to r=READ)
        """

        self.grid_file = h5_file_path
        self.h5py_file = h5py.File(h5_file_path, file_modus)
        self._set_props()

        self._grid_kwargs = {
            'has_1d': self.has_1d
        }

    @property
    def grid(self):
        kwargs = self._grid_kwargs.copy()
        kwargs['n2dtot'] = self.get_from_meta('n2dtot')
        kwargs['dx'] = self.h5py_file['grid_coordinate_attributes']['dx'].value
        return Grid(
            H5pyGroup(self.h5py_file, 'grid_coordinate_attributes'), **kwargs
        )

    @property
    def levees(self):
        return Levees(
            H5pyGroup(self.h5py_file, 'levees'), **self._grid_kwargs)

    @property
    def nodes(self):
        return Nodes(
            H5pyGroup(self.h5py_file, 'nodes'), **self._grid_kwargs)

    @property
    def lines(self):
        return Lines(
            H5pyGroup(self.h5py_file, 'lines'), **self._grid_kwargs)

    @property
    def pumps(self):
        return Pumps(
            H5pyGroup(self.h5py_file, 'pumps'), **self._grid_kwargs)

    @property
    def breaches(self):
        return Breaches(
            H5pyGroup(self.h5py_file, 'breaches'), **self._grid_kwargs)

    @property
    def cells(self):
        # treated as nodes
        return Cells(
            H5pyGroup(self.h5py_file, 'nodes'), **self._grid_kwargs)

    @property
    def revision_hash(self):
        """mercurial revision hash of the model"""
        return self._to_str(self.h5py_file.attrs['revision_hash'])

    @property
    def revision_nr(self):
        """mercurial revision nr or id of the model"""
        return self._to_str(self.h5py_file.attrs['revision_nr'])

    @property
    def model_name(self):
        """name of the model the gridadmin file belongs to"""
        return self._to_str(self.h5py_file.attrs['model_name'])

    @property
    def epsg_code(self):
        return self._to_str(self.h5py_file.attrs['epsg_code'])

    @property
    def model_slug(self):
        return self._to_str(self.h5py_file.attrs['model_slug'])

    @property
    def threedicore_version(self):
        return self._to_str(self.h5py_file.attrs['threedicore_version'])

    @property
    def threedi_version(self):
        return self._to_str(self.h5py_file.attrs['threedi_version'])

    @property
    def has_levees(self):
        if not hasattr(self, "levees"):
            return False
        return bool(self.levees.id.size)

    def get_extent_subset(self, subset_name, target_epsg_code=''):
        """

        :param subset_name: name of the node subset for which the extent
            should be calculated.
            Valid input: '1D_all', '2D_groundwater'
        :param target_epsg_code: string representation of the desired
            output epsg code
        :return: numpy array of xy-min/xy-max pairs
        """
        attr_name = constants.SUBSET_NAME_H5_ATTR_MAP.get(subset_name.upper())
        extent = self.h5py_file.attrs.get(attr_name, None)
        if extent is None:
            raise AttributeError(
                "The grid admin file %s does not have %s attribute" % (
                    self.grid_file, attr_name)
            )
        if attr_name == constants.EXTENT_1D_KEY and not self.has_1d:
            logger.info(
                '[*] The model has no 1D returning...'
            )
            return
        if attr_name == constants.EXTENT_2D_KEY and not self.has_2d:
            logger.info(
                '[*] The model has no 2D returning...'
            )
            return

        if target_epsg_code and target_epsg_code != self.epsg_code:
            extent = transform_bbox(
                extent, self.epsg_code, target_epsg_code,
            )
        return extent

    def get_model_extent(self, target_epsg_code='', **kwargs):
        """
        get the extent of the model. Combines the extent of 1d and 2d node
        coordinates. If target_epsg_code is different from the models epsg
        code it projects the coordinates to projection of the given
        target epsg code.

        :param target_epsg_code: string representation of the desired
            output epsg code
        :param kwargs:
            extra_extent: list of xy-min/xy-max pairs that need to be
            taken into account in the model extent calculation

        :return: numpy array of xy-min/xy-max pairs

        """
        bbox = kwargs.get('extra_extent', [])
        for k in constants.SUBSET_NAME_H5_ATTR_MAP.keys():
            sub_extent = self.get_extent_subset(
                subset_name=k, target_epsg_code=target_epsg_code)
            if sub_extent is None:
                continue
            bbox.append(sub_extent)

        x = np.array(bbox)[:, [0, 2]]
        y = np.array(bbox)[:, [1, 3]]

        return np.array([np.min(x), np.min(y), np.max(x), np.max(y)])

    def _set_props(self):
        for prop, value in six.iteritems(self.h5py_file.attrs):
            if prop and prop.startswith('has_'):
                try:
                    setattr(self, prop, bool(value))
                except AttributeError:
                    logger.warning(
                        'Can not set property {}, already exists'.format(prop)
                    )
                    pass

    def get_from_meta(self, prop_name):
        if prop_name not in list(self.h5py_file['meta'].keys()):
            return None

        return self.h5py_file['meta'][prop_name].value

    @staticmethod
    def _to_str(x):
        try:
            return x.decode('utf-8')
        except AttributeError:
            return x

    def __enter__(self):
        return self.h5py_file

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.h5py_file.flush()
        self.h5py_file.close()
