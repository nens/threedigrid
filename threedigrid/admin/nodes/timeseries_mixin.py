# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from threedigrid.orm.base.timeseries_mixin import ResultMixin


class NodeResultsMixin(ResultMixin):

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


    def __init__(self, netcdf_keys, **kwargs):
        """Instantiate a node with netcdf results.

        Variables stored in the netcdf and related to nodes are dynamically
        added as attributes as TimeSeriesCompositeArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(NodeResultsMixin, self).__init__(**kwargs)
