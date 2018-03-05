# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import logging

import h5py
import numpy as np

from threedigrid.orm.utils import transform_xys

from threedigrid.admin.lines.models import Lines
from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.nodes.models import Cells
from threedigrid.admin.nodes.models import Grid
from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.pumps.models import Pumps
from threedigrid.admin.levees.models import Levees
from threedigrid.admin.h5py_datasource import H5pyGroup
import constants

logger = logging.getLogger(__name__)


class GridH5Admin(object):

    def __init__(self, h5_file_path, file_modus='r'):

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
        return self.h5py_file.attrs['revision_hash']

    @property
    def revision_nr(self):
        return self.h5py_file.attrs['revision_nr']

    @property
    def model_name(self):
        return self.h5py_file.attrs['model_name']

    @property
    def epsg_code(self):
        return self.h5py_file.attrs['epsg_code']

    def get_extent_subset(self, subset_name, target_epsg_code=''):
        """

        :param subset_name: name of the node subset for which the extent
            should be calculated.
            Valid input: '1D_all', '2D_groundwater'
        :param target_epsg_code: string representation of the desired
            output epsg code
        :returns numpy array of xy-min/xy-max pairs
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
            extent = transform_xys(
                extent[::2], extent[1::2], self.epsg_code, target_epsg_code,
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
        :returns numpy array of xy-min/xy-max pairs
        """
        max_extent = np.zeros((2, 2))
        bbox = kwargs.get('extra_extent', [])
        for k in constants.SUBSET_NAME_H5_ATTR_MAP.keys():
            sub_extent = self.get_extent_subset(
                subset_name=k, target_epsg_code=target_epsg_code)
            if sub_extent is None:
                continue
            bbox.append(sub_extent)

        merged_pnts = np.concatenate(bbox)
        max_extent[0] = np.min(merged_pnts, axis=0)
        max_extent[1] = np.max(merged_pnts, axis=0)
        return max_extent

    @property
    def model_slug(self):
        return self.h5py_file.attrs['model_slug']

    @property
    def has_groundwater(self):
        # TODO threedicore will provide info, change accordingly
        return self.nodes.has_groundwater

    def _set_props(self):
        for prop, value in self.h5py_file.attrs.iteritems():
            if prop and prop.startswith('has_'):
                setattr(self, prop, bool(value))

    @property
    def has_levees(self):
        return hasattr(self, "levees")

    @property
    def threedicore_version(self):
        return self.h5py_file.attrs['threedicore_version']

    def get_from_meta(self, prop_name):
        if prop_name not in self.h5py_file['meta'].keys():
            return None

        return self.h5py_file['meta'][prop_name].value

    def __enter__(self):
        return self.h5py_file

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        self.h5py_file.flush()
        self.h5py_file.close()
