from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS
from threedigrid.admin.constants import PUMP_VARIABLES
from threedigrid.admin.utils import combine_vars


class PumpResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys, **kwargs):
        """Instantiate a pump with netcdf results.

        Variables stored in the netcdf and related to pumps are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(PumpResultsMixin, self).__init__(**kwargs)

        possible_vars = combine_vars(PUMP_VARIABLES, AGGREGATION_OPTIONS)
        possible_vars += PUMP_VARIABLES
        variables = set(possible_vars).intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
