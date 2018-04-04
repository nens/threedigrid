from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS, NODE_VARIABLES
from itertools import product


class NodeResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys):
        super(ResultMixin, self).__init__()

        variables = NODE_VARIABLES.intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())


class NodeAggregateResultsMixin(NodeResultsMixin):

    def __init__(self, netcdf_keys):
        super(NodeAggregateResultsMixin, self).__init__(netcdf_keys)

        possible_vars = map(lambda x: x[0] + '_' + x[1],
            product(NODE_VARIABLES, AGGREGATION_OPTIONS))
        variables = set(possible_vars).intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
