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
            'depth': ['Mesh1D_breach_depth'],
            'width': ['Mesh1D_breach_width']}


    def __init__(self, **kwargs):
        """Instantiate a breach with netcdf results.

        Variables stored in the netcdf and related to breaches are dynamically
        added as attributes as TimeSeriesArrayField.

        :param kwargs:
        """
        super(BreachesResultsMixin, self).__init__(**kwargs)
        # field_names = ['Mesh1D_breach_depth', 'Mesh1D_breach_width']
        # fields = {v: TimeSeriesArrayField() for v in field_names}
        # self._meta.add_fields(fields, hide_private=True)


class BreachesAggregateResultsMixin(ResultMixin):

    class Meta:
        __metaclass__ = ModelMeta

        # attributes for the given fields
        field_attrs = ['units', 'long_name']

        base_composition = {
            'depth': ['Mesh1D_breach_depth'],
            'width': ['Mesh1D_breach_width']
        }
        composition_vars = {
            'depth': ['avg', 'min', 'max', 'cum'],
            'width': ['avg', 'min', 'max', 'cum'],
        }

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(BreachesAggregateResultsMixin, self).__init__(**kwargs)
        # field_names = combine_vars(self.field_names, self.Meta.composition_vars.values())
        # fields = {v: TimeSeriesArrayField() for v in field_names}
        # self._meta.add_fields(fields, hide_private=True)
