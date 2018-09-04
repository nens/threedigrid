# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
"""

from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.timeseries_mixin import AggregateResultMixin

from threedigrid.orm.base.options import ModelMeta
import six


class PumpsResultsMixin(ResultMixin):

    class Meta(six.with_metaclass(ModelMeta)):
        field_attrs = ['units', 'long_name', 'standard_name']

        composite_fields = {'q_pump': ['Mesh1D_q_pump'],
                            '_mesh_id': ['Mesh1DPump_id']}

    def __init__(self, **kwargs):
        """Instantiate a breach with netcdf results.

        Variables stored in the netcdf and related to breaches are dynamically
        added as attributes as TimeSeriesArrayField.

        :param kwargs:
        """
        super(PumpsResultsMixin, self).__init__(**kwargs)


class PumpsAggregateResultsMixin(AggregateResultMixin):

    class Meta(six.with_metaclass(ModelMeta)):
        field_attrs = ['units', 'long_name']

        model_attr = 'timestamp'

        # ModelMeta will combine base_composition and composition_vars
        # to composite_fields attribute
        base_composition = {'q_pump': ['Mesh1D_q_pump'],
                            '_mesh_id': ['Mesh1DPump_id']}
        composition_vars = {
            'q_pump':
                ['min', 'max', 'avg', 'cum', 'cum_positive', 'cum_negative'],
        }

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(PumpsAggregateResultsMixin, self).__init__(**kwargs)
