# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import logging
import os

from netCDF4 import Dataset
from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.constants import DEFAULT_CHUNK_TIMESERIES
from threedigrid.admin.h5py_datasource import H5pyResultGroup
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.pumps.models import Pumps
from threedigrid import admin
from threedigrid.admin.nodes import timeseries_mixin
from threedigrid.admin.lines import timeseries_mixin
from threedigrid.admin.breaches import timeseries_mixin

from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.gridadmin import GridH5Admin

logger = logging.getLogger(__name__)


def get_result_mixin(model_name, result_type=''):
    """

    :param model_name:
    :param result_type:
    :return:
    """
    s = '{model_name} {result_type} Results Mixin'.format(
        model_name=model_name,
        result_type=result_type).title().replace(' ', '')

    _model_module_ = getattr(admin, model_name)
        _timeseries_mixin = getattr(_model_module_, 'timeseries_mixin')
    try:
        return getattr(_timeseries_mixin, s)
    except AttributeError:
    return None


class GridH5ResultAdmin(GridH5Admin):
    """
    Admin interface for threedicore result queries.
    """

    def __init__(self, h5_file_path, netcdf_file_path, file_modus='r'):
        """

        :param h5_file_path: path to the hdf5 gridadmin file
        :param netcdf_file_path: path to the netcdf result file (usually
            called subgrid_map.nc)
        :param file_modus: modus in which to open the files
        """
        self._netcdf_file_path = netcdf_file_path
        super(GridH5ResultAdmin, self).__init__(h5_file_path, file_modus)
        self.netcdf_file = Dataset(netcdf_file_path)
        self.set_timeseries_chunk_size(DEFAULT_CHUNK_TIMESERIES.stop)
        self._check_threedicore_version()

    @property
    def result_type(self):
        return 'aggregate' if 'aggregate' in os.path.basename(self._netcdf_file_path) else ''

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
        model_name = 'lines'
        mixin = get_result_mixin(
            model_name=model_name, result_type=self.result_type
        )
        return Lines(
            H5pyResultGroup(self.h5py_file, model_name, self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': mixin}))

    @property
    def nodes(self):
        model_name = 'nodes'
        mixin = get_result_mixin(
            model_name=model_name, result_type=self.result_type
        )
        return Nodes(
            H5pyResultGroup(self.h5py_file, 'nodes', self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': mixin}))

    @property
    def breaches(self):
        model_name = 'breaches'
        mixin = get_result_mixin(
            model_name=model_name, result_type=self.result_type
        )
        return Breaches(
            H5pyResultGroup(self.h5py_file, model_name, self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': mixin}))

    @property
    def pumps(self):
        model_name = 'pumps'
        mixin = get_result_mixin(
            model_name=model_name, result_type=self.result_type
        )
        return Pumps(
            H5pyResultGroup(self.h5py_file, model_name, self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': mixin}))

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
