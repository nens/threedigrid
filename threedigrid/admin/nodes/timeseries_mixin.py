# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
from typing import List

from threedigrid.orm.base.options import ModelMeta
from threedigrid.orm.base.timeseries_mixin import AggregateResultMixin, ResultMixin

BASE_COMPOSITE_FIELDS = {
    "s1": ["Mesh2D_s1", "Mesh1D_s1"],
    "vol": ["Mesh2D_vol", "Mesh1D_vol"],
    "su": ["Mesh2D_su", "Mesh1D_su"],
    "rain": ["Mesh2D_rain", "Mesh1D_rain"],
    "q_lat": ["Mesh2D_q_lat", "Mesh1D_q_lat"],
    "_mesh_id": ["Mesh2DNode_id", "Mesh1DNode_id"],
}

BASE_SUBSET_FIELDS = {
    "infiltration_rate_simple": {"2d_all": "Mesh2D_infiltration_rate_simple"},
    "ucx": {"2d_all": "Mesh2D_ucx"},
    "ucy": {"2d_all": "Mesh2D_ucy"},
    "leak": {"2d_all": "Mesh2D_leak"},
    "intercepted_volume": {"2d_all": "Mesh2D_intercepted_volume"},
    "q_sss": {"2d_all": "Mesh2D_q_sss"},
}


class NodesResultsMixin(ResultMixin):
    class Meta:
        # attributes for the given fields
        field_attrs = ["units", "long_name", "standard_name"]

        # values of *_COMPOSITE_FIELDS are the variables names as known in
        # the result netCDF file. They are split into 1D and 2D subsets.
        # As threedigrid has its own subsection ecosystem they are merged
        # into a single field (e.g. the keys of *_COMPOSITE_FIELDS).

        # N.B. # fields starting with '_' are private and will not be added to
        # fields property
        composite_fields = BASE_COMPOSITE_FIELDS
        subset_fields = BASE_SUBSET_FIELDS

        lookup_fields = ("id", "_mesh_id")

    def __init__(self, **kwargs):
        """Instantiate a node with netcdf results.

        Variables stored in the netcdf and related to nodes are dynamically
        added as attributes as TimeSeriesCompositeArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super().__init__(**kwargs)


class NodesAggregateResultsMixin(AggregateResultMixin):
    class Meta(metaclass=ModelMeta):
        base_composition = BASE_COMPOSITE_FIELDS
        base_subset_fields = BASE_SUBSET_FIELDS

        # attributes for the given fields
        field_attrs = ["units", "long_name"]

        # extra vars that will be combined with the
        # composite fields, e.g.
        # s1 --> s1_min [Mesh2D_s1_min + Mesh1D_s1_min]
        #    --> s1_max  [Mesh2D_s1_max + Mesh1D_s1_max]
        composition_vars = {
            "s1": ["min", "max", "avg"],
            "vol": ["min", "max", "avg", "sum", "current"],
            "su": ["min", "max", "avg"],
            "rain": ["min", "max", "avg", "cum", "cum_positive", "cum_negative"],
            "q_lat": ["min", "max", "avg", "cum", "cum_positive", "cum_negative"],
            "infiltration_rate_simple": [
                "min",
                "max",
                "avg",
                "cum",
                "cum_positive",
                "cum_negative",
            ],
            "ucx": ["min", "max", "avg"],
            "ucy": ["min", "max", "avg"],
            "leak": ["min", "max", "avg", "cum", "cum_positive", "cum_negative"],
            "intercepted_volume": ["min", "max", "avg", "cum", "current"],
            "q_sss": ["min", "max", "avg", "cum", "cum_positive", "cum_negative"],
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


class NodeSubstanceResultMixinBase(ResultMixin):
    def __init__(self, **kwargs):
        """Instantiate a node with netcdf results.

        Variables stored in the netcdf and related to nodes are dynamically
        added as attributes as TimeSeriesCompositeArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super().__init__(**kwargs)


def get_substance_result_mixin(substance_name: str):
    class NodeSubstanceResultMixin(NodeSubstanceResultMixinBase):
        class Meta:
            # attributes for the given fields
            field_attrs = ["long_name"]

            # values of *_COMPOSITE_FIELDS are the variables names as known in
            # the result netCDF file. They are split into 1D and 2D subsets.
            # As threedigrid has its own subsection ecosystem they are merged
            # into a single field (e.g. the keys of *_COMPOSITE_FIELDS).

            # N.B. # fields starting with '_' are private and will not be added to
            # fields property
            composite_fields = {
                "concentration": [f"{substance_name}_2D", f"{substance_name}_1D"],
                "_mesh_id": ["Mesh2DNode_id", "Mesh1DNode_id"],
            }
            subset_fields = {}

            lookup_fields = ("id", "_mesh_id")

    return NodeSubstanceResultMixin


def get_nodes_customized_results_mixin(fields: List[str], area: str):
    def construct_node_customized_base_composite_fields(fields: List[str], area: str):
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
        if "Mesh2DNode_id" in fields:
            composite_fields["id"] += ["Mesh2DNode_id"]
        if "Mesh1DNode_id" in fields:
            composite_fields["id"] += ["Mesh1DNode_id"]

        composite_fields["node_type"] = []
        if "Mesh2DNode_type" in fields:
            composite_fields["node_type"] += ["Mesh2DNode_type"]
        if "Mesh1DNode_type" in fields:
            composite_fields["node_type"] += ["Mesh1DNode_type"]

        return composite_fields

    def construct_node_customized_base_subset_fields(fields: List[str]):
        subset_fields = {}
        for key, value in BASE_SUBSET_FIELDS.items():
            if value["2d_all"] in fields:
                subset_fields[key] = {"2d_all": value["2d_all"]}

        return subset_fields

    composites = construct_node_customized_base_composite_fields(fields, area)
    subsets = construct_node_customized_base_subset_fields(fields)

    class NodesCustomizedResultsMixin(ResultMixin):
        class Meta:
            field_attrs = ["units", "long_name", "standard_name"]

            composite_fields = composites
            composite_fields_skip_timeseries_filter = ["id", "_mesh_id", "node_type"]
            subset_fields = subsets
            lookup_fields = ("_mesh_id", "id")
            is_customized_mixin = True

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    return NodesCustomizedResultsMixin


def get_nodes_customized_water_quality_results_mixin(
    substance_name: str, fields: List[str], area: str
):
    composites = {}
    composites["id"] = []
    if "Mesh2DNode_id" in fields:
        composites["id"] += ["Mesh2DNode_id"]
    if "Mesh1DNode_id" in fields:
        composites["id"] += ["Mesh1DNode_id"]

    composites["_mesh_id"] = []
    if f"Mesh2DNode_id{area}" in fields:
        composites["_mesh_id"] += [f"Mesh2DNode_id{area}"]
    if f"Mesh1DNode_id{area}" in fields:
        composites["_mesh_id"] += [f"Mesh1DNode_id{area}"]

    composites["node_type"] = []
    if "Mesh2DNode_type" in fields:
        composites["node_type"] += ["Mesh2DNode_type"]
    if "Mesh1DNode_type" in fields:
        composites["node_type"] += ["Mesh1DNode_type"]

    composites["concentration"] = []
    if f"{substance_name}_2D" in fields:
        composites["concentration"] += [f"{substance_name}_2D"]
    if f"{substance_name}_1D" in fields:
        composites["concentration"] += [f"{substance_name}_1D"]

    class NodesCustomizedWaterQualityResultsMixin(ResultMixin):
        class Meta:
            field_attrs = ["units", "long_name", "standard_name"]

            composite_fields = composites
            composite_fields_skip_timeseries_filter = ["id", "_mesh_id", "node_type"]

            subset_fields = {}
            lookup_fields = ("_mesh_id", "id")
            is_customized_mixin = True

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    return NodesCustomizedWaterQualityResultsMixin
