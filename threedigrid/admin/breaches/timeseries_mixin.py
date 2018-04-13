from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS
from threedigrid.admin.constants import BREACH_VARIABLES
from threedigrid.admin.utils import combine_vars


class BreachResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys, **kwargs):
        """Instantiate a breach with netcdf results.

        Variables stored in the netcdf and related to breaches are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(BreachResultsMixin, self).__init__(**kwargs)

        possible_vars = combine_vars(BREACH_VARIABLES, AGGREGATION_OPTIONS)
        possible_vars += BREACH_VARIABLES
        variables = set(possible_vars).intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
        self.update_field_names(variables, exclude_private=True)
