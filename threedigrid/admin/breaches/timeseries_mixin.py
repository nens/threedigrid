from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField


class BreachResultsMixin(ResultMixin):
    breach_depth = TimeSeriesArrayField()
    breach_width = TimeSeriesArrayField()
