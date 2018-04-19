from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField

from threedigrid.orm.base.options import MetaMixin


class PumpsResultsMixin(ResultMixin):

    class Meta:

        # attributes for the given fields
        field_attrs = ['units', 'long_name', 'standard_name']


    def __init__(self, **kwargs):
        """Instantiate a breach with netcdf results.

        Variables stored in the netcdf and related to breaches are dynamically
        added as attributes as TimeSeriesArrayField.

        :param kwargs:
        """
        super(PumpsResultsMixin, self).__init__(**kwargs)
        field_names = ['Mesh1D_q_pump']
        fields = {v: TimeSeriesArrayField() for v in field_names}
        self._meta.add_fields(fields, hide_private=True)


class PumpsAggregateResultsMixin(ResultMixin):

    class Meta:
        __metaclass__ = MetaMixin

        # attributes for the given fields
        field_attrs = ['units', 'long_name']

        composition_vars = {
            'q_pump': ['avg', 'min', 'max', 'cum'],
        }

    def __init__(self, netcdf_keys, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(PumpsAggregateResultsMixin, self).__init__(**kwargs)
