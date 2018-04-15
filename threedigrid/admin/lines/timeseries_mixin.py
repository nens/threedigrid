# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from threedigrid.orm.base.timeseries_mixin import ResultMixin


class LineResultsMixin(ResultMixin):

    class Meta:

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'standard_name']

        composite_fields = {
            'au': ['Mesh2D_au', 'Mesh1D_au'],
            'u1': ['Mesh2D_u1', 'Mesh1D_u1'],
            'q': ['Mesh2D_q', 'Mesh1D_q'],
            '_mesh_id': ['Mesh2DLine_id', 'Mesh1DLine_id'],  # private
        }

    def __init__(self, netcdf_keys, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(LineResultsMixin, self).__init__(**kwargs)
