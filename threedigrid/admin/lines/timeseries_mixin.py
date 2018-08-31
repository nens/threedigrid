# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.timeseries_mixin import AggregateResultMixin
from threedigrid.orm.base.options import ModelMeta
import six


BASE_COMPOSITE_FIELDS = {
    'au': ['Mesh2D_au', 'Mesh1D_au'],
    'u1': ['Mesh2D_u1', 'Mesh1D_u1'],
    'q': ['Mesh2D_q', 'Mesh1D_q'],
    'qp': ['Mesh2D_qp'],
    'up1': ['Mesh2D_up1'],
    '_mesh_id': ['Mesh2DLine_id', 'Mesh1DLine_id'],  # private
}

BASE_SUBSET_FIELDS = {
    'qp': {'2d_all': 'Mesh2D_qp'},
    'up1':
        {'2d_all': 'Mesh2D_up1'},
}


class LinesResultsMixin(ResultMixin):

    class Meta:

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'standard_name']

        composite_fields = BASE_COMPOSITE_FIELDS
        subset_fields = BASE_SUBSET_FIELDS

        lookup_fields = ('id', '_mesh_id')

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(LinesResultsMixin, self).__init__(**kwargs)


class LinesAggregateResultsMixin(AggregateResultMixin):

    class Meta(six.with_metaclass(ModelMeta)):
        field_attrs = ['units', 'long_name']

        base_composition = BASE_COMPOSITE_FIELDS
        base_subset_fields = BASE_SUBSET_FIELDS

        composition_vars = {
            'au': ['min', 'max', 'avg'],
            'u1': ['min', 'max', 'avg'],
            'q': ['min', 'max', 'avg', 'cum', 'cum_positive', 'cum_negative'],
            'up1': ['min', 'max', 'avg'],
            'qp': ['min', 'max', 'avg', 'cum', 'cum_positive', 'cum_negative'],
        }

        lookup_fields = ('id', '_mesh_id')

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(LinesAggregateResultsMixin, self).__init__(**kwargs)
