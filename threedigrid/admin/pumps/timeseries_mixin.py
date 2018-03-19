from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField


class PumpResultsMixin(ResultMixin):
    q_pump = TimeSeriesArrayField()
