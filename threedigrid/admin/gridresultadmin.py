# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import logging
from collections import defaultdict

from netCDF4 import Dataset
from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.breaches.timeseries_mixin import BreachResultsMixin
from threedigrid.admin.constants import DEFAULT_CHUNK_TIMESERIES
from threedigrid.admin.h5py_datasource import H5pyResultGroup
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.lines.timeseries_mixin import LineResultsMixin
from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.nodes.timeseries_mixin import NodeResultsMixin
from threedigrid.admin.pumps.models import Pumps
from threedigrid.admin.pumps.timeseries_mixin import PumpResultsMixin
from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.orm.models import Model

logger = logging.getLogger(__name__)


class GridH5ResultAdmin(GridH5Admin):
    """
    Admin interface for threedicore result queries.
    """
    _field_model_dict = defaultdict(list)

    def __init__(self, h5_file_path, netcdf_file_path, file_modus='r'):
        """

        :param h5_file_path: path to the hdf5 gridadmin file
        :param netcdf_file_path: path to the netcdf result file (usually
            called subgrid_map.nc)
        :param file_modus: modus in which to open the files
        """
        super(GridH5ResultAdmin, self).__init__(h5_file_path, file_modus)
        self.netcdf_file = Dataset(netcdf_file_path)
        self.set_timeseries_chunk_size(DEFAULT_CHUNK_TIMESERIES.stop)
        self._check_threedicore_version()

    def set_timeseries_chunk_size(self, new_chunk_size):
        """
        overwrite the default chunk size for timeseries queries.
        :param new_chunk_size <int> or <slice>: new chunk size for
            timeseries queries
        :raises ValueError when the given value is less than 1
        """
        _chunk_size = int(new_chunk_size)
        if _chunk_size < 1:
            raise ValueError('Chunk size must be greater than 0')
        self._timeseries_chunk_size = slice(0, _chunk_size)
        logger.info(
            'New chunk for timeseries size has been set to %d',
            new_chunk_size
        )
        self._grid_kwargs.update(
            {'timeseries_chunk_size': self._timeseries_chunk_size}
        )

    @property
    def timeseries_chunk_size(self):
        return self._timeseries_chunk_size.stop

    @property
    def time_units(self):
        return self.netcdf_file.variables['time'].getncattr('units')

    @property
    def lines(self):
        return Lines(
            H5pyResultGroup(self.h5py_file, 'lines', self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': LineResultsMixin}))

    @property
    def nodes(self):
        return Nodes(
            H5pyResultGroup(self.h5py_file, 'nodes', self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': NodeResultsMixin}))

    @property
    def breaches(self):
        return Breaches(
            H5pyResultGroup(self.h5py_file, 'breaches', self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': BreachResultsMixin}))

    @property
    def pumps(self):
        return Pumps(
            H5pyResultGroup(self.h5py_file, 'pumps', self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': PumpResultsMixin}))

    def _check_threedicore_version(self):
        try:
            threedicore_version = self.netcdf_file.getncattr(
                'threedicore_version'
            )
        except AttributeError:
            logger.error(
                'Attribute threedicore_version could not be found in result file')  # noqa
            return ''
        if threedicore_version != self.threedicore_version:
            logger.warning(
                '[!] threedicore version differ! \n'
                'Version result file has been created with: %s\n'
                'Version gridadmin file has been created with: %s',
                threedicore_version, self.threedicore_version
            )

    @property
    def __field_model_map(self):
        """
        :return: a dict of {<field name>: [model name, ...]}
        """
        if self._field_model_dict:
            return self._field_model_dict

        model_names = set()
        for attr_name in dir(self):
            # skip private attrs
            if any([attr_name.startswith('__'),
                    attr_name.startswith('_')]):
                continue
            attr = getattr(self, attr_name)
            if not issubclass(type(attr), Model):
                continue
            model_names.add(attr_name)

        for model_name in model_names:
            for x in getattr(self, model_name)._meta.get_fields(
                    only_names=True):
                self._field_model_dict[x].append(model_name)
        return self._field_model_dict

    def get_model_instance_by_field_name(self, field_name):
        """
        :param field_name: name of a models field
        :return: instance of the model the field belongs to
        :raises IndexError if the field name is not unique across models
        """
        model_name = self.__field_model_map.get(field_name)
        cnt = len(model_name)
        if cnt != 1:
            raise IndexError(
                'Ambiguous result. Field name {} yields {} model(s)'.format(
                    field_name, cnt)
            )
        return getattr(self, model_name[0])
