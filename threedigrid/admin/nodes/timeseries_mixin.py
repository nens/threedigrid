# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.timeseries_mixin import AggregateResultMixin
from threedigrid.orm.base.options import ModelMeta


BASE_COMPOSITE_FIELDS = {
    's1': ['Mesh2D_s1', 'Mesh1D_s1'],
    'vol': ['Mesh2D_vol', 'Mesh1D_vol'],
    'su': ['Mesh2D_su', 'Mesh1D_su'],
    'rain': ['Mesh2D_rain', 'Mesh1D_rain'],
    'q_lat': ['Mesh2D_q_lat', 'Mesh1D_q_lat'],
    'infiltration_rate_simple': ['Mesh2D_infiltration_rate_simple'],
    'ucx': ['Mesh2D_ucx'],
    'ucy': ['Mesh2D_ucy'],
    'leak': ['Mesh2D_leak'],
    '_mesh_id': ['Mesh2DNode_id', 'Mesh1DNode_id'],  # private
}


class NodesResultsMixin(ResultMixin):

    class Meta:

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'standard_name']

        # values of *_COMPOSITE_FIELDS are the variables names as known in
        # the result netCDF file. They are split into 1D and 2D subsets.
        # As threedigrid has its own subsection ecosystem they are merged
        # into a single field (e.g. the keys of *_COMPOSITE_FIELDS).

        # N.B. # fields starting with '_' are private and will not be added to
        # fields property
        composite_fields = BASE_COMPOSITE_FIELDS

        lookup_fields = ('id', '_mesh_id')

    def __init__(self, **kwargs):
        """Instantiate a node with netcdf results.

        Variables stored in the netcdf and related to nodes are dynamically
        added as attributes as TimeSeriesCompositeArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(NodesResultsMixin, self).__init__(**kwargs)


class NodesAggregateResultsMixin(AggregateResultMixin):

    class Meta:
        __metaclass__ = ModelMeta

        base_composition = BASE_COMPOSITE_FIELDS

        # attributes for the given fields
        field_attrs = ['units', 'long_name']

        # extra vars that will be combined with the
        # composite fields, e.g.
        # s1 --> s1_min [Mesh2D_s1_min + Mesh1D_s1_min]
        #    --> s1_max  [Mesh2D_s1_max + Mesh1D_s1_max]
        composition_vars = {
            's1': ['min', 'max', 'avg'],
            'vol': ['min', 'max', 'avg', 'sum'],
            'su': ['min', 'max', 'avg'],
            'rain': ['min', 'max', 'avg', 'cum', 'cum_positive', 'cum_negative'],
            'q_lat': ['min', 'max', 'avg', 'cum', 'cum_positive', 'cum_negative'],
            'infiltration_rate_simple': ['min', 'max', 'avg', 'cum', 'cum_positive', 'cum_negative'],
            'ucx': ['min', 'max', 'avg'],
            'ucy': ['min', 'max', 'avg'],
            'leak': ['min', 'max', 'avg', 'cum', 'cum_positive', 'cum_negative'],
        }

        lookup_fields = ('id', '_mesh_id')


    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(NodesAggregateResultsMixin, self).__init__(**kwargs)
