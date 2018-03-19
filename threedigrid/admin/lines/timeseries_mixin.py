from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField


class LineResultsMixin(ResultMixin):
    u1 = TimeSeriesArrayField()
    au = TimeSeriesArrayField()
    q = TimeSeriesArrayField()
