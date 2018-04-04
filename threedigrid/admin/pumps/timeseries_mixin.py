from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS, PUMP_VARIABLES
from itertools import product


class PumpResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys):
        super(ResultMixin, self).__init__()

        variables = PUMP_VARIABLES.intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())


class PumpAggregateResultsMixin(PumpResultsMixin):

    def __init__(self, dynamic_keys):
        super(PumpAggregateResultsMixin, self).__init__()

        possible_vars = map(lambda x: x[0] + '_' + x[1],
            product(PUMP_VARIABLES, AGGREGATION_OPTIONS))
        variables = set(possible_vars).intersection(dynamic_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
