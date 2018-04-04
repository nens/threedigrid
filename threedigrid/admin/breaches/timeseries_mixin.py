from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS, BREACH_VARIABLES
from itertools import product


class BreachResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys):
        super(ResultMixin, self).__init__()

        variables = BREACH_VARIABLES.intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())


class BreachAggregateResultsMixin(BreachResultsMixin):

    def __init__(self, dynamic_keys):
        super(BreachAggregateResultsMixin, self).__init__()

        possible_vars = map(lambda x: x[0] + '_' + x[1],
            product(BREACH_VARIABLES, AGGREGATION_OPTIONS))
        variables = set(possible_vars).intersection(dynamic_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
