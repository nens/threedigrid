from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.orm.constants import AGGREGATION_OPTIONS
from threedigrid.orm.constants import PUMPS_VARIABLES
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

        possible_vars = combine_vars(PUMPS_VARIABLES, AGGREGATION_OPTIONS)
        possible_vars += PUMPS_VARIABLES
        variables = set(possible_vars).intersection(netcdf_keys)
        fields = {v: TimeSeriesArrayField() for v in variables}
        self._meta.add_fields(fields, hide_private=True)
