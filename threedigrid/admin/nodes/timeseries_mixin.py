from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.orm.base.fields import MappedSubsetTimeSeriesArrayField


class NodeResultsMixin(ResultMixin):
    s1 = TimeSeriesArrayField()
    su = TimeSeriesArrayField()
    vol = TimeSeriesArrayField()
    rain = TimeSeriesArrayField()
    ucx = MappedSubsetTimeSeriesArrayField(
        mapping=[{'source': 'ucx', 'subset': '2D_open_water'}])
    ucy = MappedSubsetTimeSeriesArrayField(
        mapping=[{'source': 'ucy', 'subset': '2D_open_water'}])
