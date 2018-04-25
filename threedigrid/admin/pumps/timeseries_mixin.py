# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
"""

from __future__ import unicode_literals
from __future__ import print_function

from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.timeseries_mixin import AggregateResultMixin

from threedigrid.orm.base.options import ModelMeta


class PumpsResultsMixin(ResultMixin):

    class Meta:
        __metaclass__ = ModelMeta

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'standard_name']

        composite_fields = {'q_pump': ['Mesh1D_q_pump']}

    def __init__(self, **kwargs):
        """Instantiate a breach with netcdf results.

        Variables stored in the netcdf and related to breaches are dynamically
        added as attributes as TimeSeriesArrayField.

        :param kwargs:
        """
        super(PumpsResultsMixin, self).__init__(**kwargs)


class PumpsAggregateResultsMixin(AggregateResultMixin):

    class Meta:
        __metaclass__ = ModelMeta

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'time_units']

        model_attr = 'timestamp'

        base_composition = {'q_pump': ['Mesh1D_q_pump']}
        composition_vars = {
            'q_pump': ['avg', 'min', 'max', 'cum'],
        }

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(PumpsAggregateResultsMixin, self).__init__(**kwargs)
