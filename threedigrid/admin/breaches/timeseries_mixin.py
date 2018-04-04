from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS, BREACH_VARIABLES
from itertools import product


class BreachResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys, **kwargs):
        super(BreachResultsMixin, self).__init__(**kwargs)

        possible_vars = map(lambda x: x[0] + '_' + x[1],
                            product(BREACH_VARIABLES, AGGREGATION_OPTIONS))
        possible_vars += BREACH_VARIABLES
        variables = set(possible_vars).intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
