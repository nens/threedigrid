# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
"""


from threedigrid.orm.base.options import ModelMeta
from threedigrid.orm.base.timeseries_mixin import AggregateResultMixin, ResultMixin


class PumpsResultsMixin(ResultMixin):
    class Meta(metaclass=ModelMeta):
        field_attrs = ["units", "long_name", "standard_name"]

        composite_fields = {"q_pump": ["Mesh1D_q_pump"], "_mesh_id": ["Mesh1DPump_id"]}

    def __init__(self, **kwargs):
        """Instantiate a breach with netcdf results.

        Variables stored in the netcdf and related to breaches are dynamically
        added as attributes as TimeSeriesArrayField.

        :param kwargs:
        """
        super().__init__(**kwargs)


class PumpsAggregateResultsMixin(AggregateResultMixin):
    class Meta(metaclass=ModelMeta):
        field_attrs = ["units", "long_name"]

        model_attr = "timestamp"

        # ModelMeta will combine base_composition and composition_vars
        # to composite_fields attribute
        base_composition = {"q_pump": ["Mesh1D_q_pump"], "_mesh_id": ["Mesh1DPump_id"]}
        composition_vars = {
            "q_pump": ["min", "max", "avg", "cum", "cum_positive", "cum_negative"],
        }

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super().__init__(**kwargs)
