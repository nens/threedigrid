# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.admin.constants import AGGREGATION_OPTIONS, LINE_VARIABLES
from itertools import product


class LineResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys, **kwargs):
        super(LineResultsMixin, self).__init__(**kwargs)

        possible_vars = map(lambda x: x[0] + '_' + x[1],
                            product(LINE_VARIABLES, AGGREGATION_OPTIONS))
        possible_vars += LINE_VARIABLES
        variables = set(possible_vars).intersection(netcdf_keys)
        for var in variables:
            setattr(self, var, TimeSeriesArrayField())
