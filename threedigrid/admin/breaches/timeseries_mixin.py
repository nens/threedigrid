# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from threedigrid.admin.utils import combine_vars
from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.orm.constants import AGGREGATION_OPTIONS
from threedigrid.orm.constants import BREACH_VARIABLES


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
        fields = {v: TimeSeriesArrayField() for v in variables}
        self._meta.add_fields(fields, hide_private=True)
