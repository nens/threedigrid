# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS
from threedigrid.admin.constants import LINE_VARIABLES
from threedigrid.admin.utils import combine_vars


class LineResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(LineResultsMixin, self).__init__(**kwargs)

        possible_vars = combine_vars(LINE_VARIABLES, AGGREGATION_OPTIONS)
        possible_vars += LINE_VARIABLES
        variables = set(possible_vars).intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
