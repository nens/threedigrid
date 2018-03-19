from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField


class NodeResultsMixin(ResultMixin):
    s1 = TimeSeriesArrayField()
    su = TimeSeriesArrayField()
    vol = TimeSeriesArrayField()
    rain = TimeSeriesArrayField()
