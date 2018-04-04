from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS, NODE_VARIABLES
from itertools import product


class NodeResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys, **kwargs):
        super(NodeResultsMixin, self).__init__(**kwargs)

        possible_vars = map(lambda x: x[0] + '_' + x[1],
                            product(NODE_VARIABLES, AGGREGATION_OPTIONS))
        possible_vars += NODE_VARIABLES
        variables = set(possible_vars).intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
