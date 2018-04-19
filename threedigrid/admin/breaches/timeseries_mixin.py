# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from threedigrid.admin.utils import combine_vars
from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.orm.constants import AGGREGATION_OPTIONS
from threedigrid.orm.constants import BREACH_VARIABLES


class BreachesResultsMixin(ResultMixin):

    class Meta:

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'standard_name']

        #lookup_fields = ('id', '_mesh_id')


    def __init__(self, **kwargs):
        """Instantiate a breach with netcdf results.

        Variables stored in the netcdf and related to breaches are dynamically
        added as attributes as TimeSeriesArrayField.

        :param kwargs:
        """
        super(BreachesResultsMixin, self).__init__(**kwargs)
        field_names = ['Mesh1D_breach_depth', 'Mesh1D_breach_width']
        fields = {v: TimeSeriesArrayField() for v in field_names}
        self._meta.add_fields(fields, hide_private=True)
