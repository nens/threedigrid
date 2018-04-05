from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS
from threedigrid.admin.constants import NODE_VARIABLES
from threedigrid.admin.utils import combine_vars


class NodeResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys, **kwargs):
        """Instantiate a node with netcdf results.

        Variables stored in the netcdf and related to nodes are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(NodeResultsMixin, self).__init__(**kwargs)

        possible_vars = combine_vars(NODE_VARIABLES, AGGREGATION_OPTIONS)
        possible_vars += NODE_VARIABLES
        variables = set(possible_vars).intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
