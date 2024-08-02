# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from typing import List

from threedigrid.admin.constants import NO_DATA_VALUE
from threedigrid.orm.base.options import ModelMeta
from threedigrid.orm.base.timeseries_mixin import AggregateResultMixin, ResultMixin

BASE_COMPOSITE_FIELDS = {
    "au": ["Mesh2D_au", "Mesh1D_au"],
    "u1": ["Mesh2D_u1", "Mesh1D_u1"],
    "q": ["Mesh2D_q", "Mesh1D_q"],
    "qp": ["Mesh2D_qp"],
    "up1": ["Mesh2D_up1"],
    "_mesh_id": ["Mesh2DLine_id", "Mesh1DLine_id"],  # private
}

BASE_SUBSET_FIELDS = {
    "qp": {"2d_all": "Mesh2D_qp"},
    "up1": {"2d_all": "Mesh2D_up1"},
    "breach_depth": {"1d_all": "Mesh1D_breach_depth"},
    "breach_width": {"1d_all": "Mesh1D_breach_width"},
}


def construct_line_base_composite_fields(fields: List[str]):
    composite_fields = {
        "au": [],
        "u1": [],
        "q": [],
        "qp": [],
        "up1": [],
        "_mesh_id": [],
    }

    for field in fields:
        for key, values in BASE_COMPOSITE_FIELDS.items():
            if field in values:
                composite_fields[key].append(field)

    return composite_fields


class LinesResultsMixin(ResultMixin):
    class Meta:
        # attributes for the given fields
        field_attrs = ["units", "long_name", "standard_name"]

        composite_fields = BASE_COMPOSITE_FIELDS
        subset_fields = BASE_SUBSET_FIELDS

        lookup_fields = ("id", "_mesh_id")

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super().__init__(**kwargs)


class LinesAggregateResultsMixin(AggregateResultMixin):
    class Meta(metaclass=ModelMeta):
        field_attrs = ["units", "long_name"]

        base_composition = BASE_COMPOSITE_FIELDS
        base_subset_fields = BASE_SUBSET_FIELDS

        composition_vars = {
            "au": ["min", "max", "avg"],
            "u1": ["min", "max", "avg"],
            "q": ["min", "max", "avg", "cum", "cum_positive", "cum_negative"],
            "up1": ["min", "max", "avg"],
            "qp": ["min", "max", "avg", "cum", "cum_positive", "cum_negative"],
        }

        lookup_fields = ("id", "_mesh_id")

    def __init__(self, **kwargs):
        """Instantiate a line with netcdf results.

        Variables stored in the netcdf and related to lines are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super().__init__(**kwargs)


def get_customized_lines_result_mixin(fields: List[str], area: str):
    def construct_line_customized_base_composite_fields(fields: List[str], area: str):
        """ID is added as a composite field as it is not equal to the grid ids"""
        composite_fields = {}
        for field in fields:
            for key, values in BASE_COMPOSITE_FIELDS.items():
                if field in values:
                    if key not in composite_fields:
                        composite_fields[key] = [field]
                    else:
                        # Sort just to be sure 2D is before 1D
                        composite_fields[key].insert(0, field)
                        composite_fields[key].sort(reverse=True)

        if "_mesh_id" in composite_fields:
            for i, v in enumerate(composite_fields["_mesh_id"]):
                composite_fields["_mesh_id"][i] = f"{v}{area}"

        composite_fields["id"] = []
        if "Mesh2DLine_id" in fields:
            composite_fields["id"].insert(0, "Mesh2DLine_id")
        if "Mesh1DLine_id" in fields:
            composite_fields["id"].append("Mesh1DLine_id")

        composite_fields["kcu"] = []
        if "Mesh2DLine_type" in fields:
            composite_fields["kcu"].insert(0, "Mesh2DLine_type")
        if "Mesh1DLine_type" in fields:
            composite_fields["kcu"].append("Mesh1DLine_type")

        return composite_fields

    def construct_line_customized_base_subset_fields(fields: List[str]):
        subset_fields = {}
        for key, value in BASE_SUBSET_FIELDS.items():
            subset = list(value.keys())[0]
            if value[subset] in fields:
                subset_fields[key] = {subset: value[subset]}

        return subset_fields

    composites = construct_line_customized_base_composite_fields(fields, area)
    subsets = construct_line_customized_base_subset_fields(fields)

    class CustomizedLinesResultsMixin(LinesResultsMixin):
        class Meta:
            field_attrs = ["units", "long_name", "standard_name"]

            composite_fields = composites
            subset_fields = subsets
            lookup_fields = ("_mesh_id", "id")
            is_customized_mixin = True
            composite_field_insert_values = {"kcu": int(NO_DATA_VALUE)}

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    return CustomizedLinesResultsMixin
