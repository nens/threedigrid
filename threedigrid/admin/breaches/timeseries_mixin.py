# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.options import ModelMeta


class BreachesResultsMixin(ResultMixin):

    class Meta:
        __metaclass__ = ModelMeta

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'standard_name']

        # customize field names
        composite_fields = {
            'breach_depth': ['Mesh1D_breach_depth'],
            'breach_width': ['Mesh1D_breach_width']}

    def __init__(self, **kwargs):
        """Instantiate a breach with netcdf results.

        Variables stored in the netcdf and related to breaches are dynamically
        added as attributes as TimeSeriesArrayField.

        :param kwargs:
        """
        super(BreachesResultsMixin, self).__init__(**kwargs)

class BreachesAggregateResultsMixin(ResultMixin):

    class Meta:
        __metaclass__ = ModelMeta

        # attributes for the given fields
        field_attrs = ['units', 'long_name']

        base_composition = {
            'breach_depth': ['Mesh1D_breach_depth'],
            'breach_width': ['Mesh1D_breach_width']
        }
        composition_vars = {
            'breach_depth': ['avg', 'min', 'max'],
            'breach_width': ['avg', 'min', 'max'],
        }

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(BreachesAggregateResultsMixin, self).__init__(**kwargs)
