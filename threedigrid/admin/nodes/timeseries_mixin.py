# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.admin.utils import combine_vars


class MetaMixin(type):

    def __new__(metacls, name, bases, namespace, **kwds):
        result = type.__new__(metacls, name, bases, dict(namespace))
        result.composite_fields = {}
        aggr_vars = namespace.get('aggregation_vars')
        parent = namespace.get('__super_meta__')
        if not aggr_vars:
            return result

        for k, v in aggr_vars.iteritems():
            c_field = parent.composite_fields.get(k)
            for p in v:
                new_key = k + '_' + p
                agg_fields = combine_vars(c_field, {p})
                result.composite_fields[new_key] = agg_fields
        return result


class NodeResultsMixinTemp(ResultMixin):

    class Meta:

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'standard_name']

        # values of *_COMPOSITE_FIELDS are the variables names as known in
        # the result netCDF file. They are split into 1D and 2D subsets.
        # As threedigrid has its own subsection ecosystem they are merged
        # into a single field (e.g. the keys of *_COMPOSITE_FIELDS).

        # N.B. # fields starting with '_' are private and will not be added to
        # fields property
        composite_fields = {
            's1': ['Mesh2D_s1', 'Mesh1D_s1'],
            'vol': ['Mesh2D_vol', 'Mesh1D_vol'],
            'su': ['Mesh2D_su', 'Mesh1D_su'],
            'rain': ['Mesh2D_rain', 'Mesh1D_rain'],
            'q_lat': ['Mesh2D_q_lat', 'Mesh1D_q_lat'],
            '_mesh_id': ['Mesh2DNode_id', 'Mesh1DNode_id'],  # private
        }

        lookup_fields = ('id', '_mesh_id')


    def __init__(self, **kwargs):
        """Instantiate a node with netcdf results.

        Variables stored in the netcdf and related to nodes are dynamically
        added as attributes as TimeSeriesCompositeArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(NodeResultsMixinTemp, self).__init__(**kwargs)


class NodeResultsMixin(NodeResultsMixinTemp):

    class Meta:
        __metaclass__ = MetaMixin
        __super_meta__ = NodeResultsMixinTemp.Meta

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'standard_name']

        aggregation_vars = {
            's1': ['min', 'max'],
            'vol': ['max', 'cum'],
            'su': ['min'],
            'rain': ['avg'],
            'q_lat': ['cum'],
        }

        lookup_fields = ('id', '_mesh_id')


    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(NodeResultsMixin, self).__init__(**kwargs)
