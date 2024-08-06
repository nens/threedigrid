# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
from typing import List

from threedigrid.orm.base.options import ModelMeta
from threedigrid.orm.base.timeseries_mixin import ResultMixin


class BreachesResultsMixin(ResultMixin):
    class Meta(metaclass=ModelMeta):
        field_attrs = ["units", "long_name", "standard_name"]

        # customize field names
        composite_fields = {
            "breach_depth": ["Mesh1D_breach_depth"],
            "breach_width": ["Mesh1D_breach_width"],
        }

    def __init__(self, **kwargs):
        """Instantiate a breach with netcdf results.

        Variables stored in the netcdf and related to breaches are dynamically
        added as attributes as TimeSeriesArrayField.

        :param kwargs:
        """
        super().__init__(**kwargs)


class BreachesAggregateResultsMixin(ResultMixin):
    class Meta(metaclass=ModelMeta):
        field_attrs = ["units", "long_name"]

        base_composition = {
            "breach_depth": ["Mesh1D_breach_depth"],
            "breach_width": ["Mesh1D_breach_width"],
        }
        composition_vars = {
            "breach_depth": ["avg", "min", "max"],
            "breach_width": ["avg", "min", "max"],
        }

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super().__init__(**kwargs)


def get_breaches_customized_result_mixin(fields: List[str], area: str):
    if f"Mesh1DLine_id{area}" not in fields:
        return

    composites = {}
    composites["id"] = [f"Mesh1DLine_id{area}"]
    if "Mesh1D_breach_depth" in fields:
        composites["breach_depth"] = ["Mesh1D_breach_depth"]
    if "Mesh1D_breach_width" in fields:
        composites["breach_width"] = ["Mesh1D_breach_width"]

    class BreachesResultsCustomizedResultMixin(BreachesResultsMixin):
        class Meta:
            field_attrs = ["units", "long_name", "standard_name"]

            # customize field names
            composite_fields = composites
            lookup_fields = ("id", "levl")
            is_customized_mixin = True

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    return BreachesResultsCustomizedResultMixin
