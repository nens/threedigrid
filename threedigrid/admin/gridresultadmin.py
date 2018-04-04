from netCDF4 import Dataset
from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.breaches.timeseries_mixin import BreachAggregateResultsMixin
from threedigrid.admin.h5py_datasource import H5pyResultGroup
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.lines.timeseries_mixin import LineAggregateResultsMixin
from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.nodes.timeseries_mixin import NodeAggregateResultsMixin
from threedigrid.admin.pumps.models import Pumps
from threedigrid.admin.pumps.timeseries_mixin import PumpAggregateResultsMixin
from threedigrid.admin.gridadmin import GridH5Admin


class GridH5ResultAdmin(GridH5Admin):
    def __init__(self, h5_file_path, netcdf_file_path, file_modus='r'):
        super(GridH5ResultAdmin, self).__init__(h5_file_path, file_modus)
        self.netcdf_file = Dataset(netcdf_file_path)

    @property
    def lines(self):
        return Lines(
            H5pyResultGroup(self.h5py_file, 'lines', self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': LineAggregateResultsMixin}))

    @property
    def nodes(self):
        return Nodes(
            H5pyResultGroup(self.h5py_file, 'nodes', self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': NodeAggregateResultsMixin}))

    @property
    def breaches(self):
        return Breaches(
            H5pyResultGroup(self.h5py_file, 'breaches', self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': BreachAggregateResultsMixin}))

    @property
    def pumps(self):
        return Pumps(
            H5pyResultGroup(self.h5py_file, 'pumps', self.netcdf_file),
            **dict(self._grid_kwargs, **{'mixin': PumpAggregateResultsMixin}))
