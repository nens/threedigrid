# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
Models
++++++
In the threedicore lines are called flow lines and represent links between
calculation points. They can exist between 1d and 2d points, between surface
and groundwater nodes etc. The line type is described by the kcu attribute
For an overview of the kcu types see :ref:`kcu-label`.
"""


import warnings

import numpy as np

from threedigrid.admin.lines import exporters, subsets
from threedigrid.orm.base.fields import IndexArrayField, MappedSubsetArrayField
from threedigrid.orm.fields import ArrayField, LineArrayField, MultiLineArrayField
from threedigrid.orm.models import Model

LINE_SUBSETS = {"kcu__in": subsets.KCU__IN_SUBSETS}


class Lines(Model):
    """
    fields originating from threedicore:

        - kcu (line type)
        - lik ()
        - line (index of node representing start/end point)

    added fields from spatialite database:

        - content_pk (primary key database)
        - content_type (type of object as stored in
          database, e.g v2_channel, v2_weir etc)

    custom fields
        - line_coords (coordinate pairs start/end point)
        - line_geometries (geometries from content_type)

    """

    kcu = ArrayField(type=int)
    lik = ArrayField(type=int)
    line = IndexArrayField(to="Nodes")
    dpumax = ArrayField(type=float)
    flod = ArrayField(type=float)
    flou = ArrayField(type=float)
    cross1 = IndexArrayField(to="CrossSections")
    cross2 = IndexArrayField(to="CrossSections")
    ds1d = ArrayField(type=float)
    ds1d_half = ArrayField(type=float)
    cross_weight = ArrayField(type=float)
    invert_level_start_point = ArrayField(type=float)
    invert_level_end_point = ArrayField(type=float)
    content_pk = ArrayField(type=int)
    content_type = ArrayField(type=str)
    zoom_category = ArrayField(type=int)
    cross_pix_coords = LineArrayField(type=float)
    line_coords = LineArrayField()
    line_geometries = MultiLineArrayField()
    SUBSETS = LINE_SUBSETS

    GPKG_DEFAULT_FIELD_MAP = {
        "id": "id",
        "flou": "discharge_coefficient_positive",
        "flod": "discharge_coefficient_negative",
        "kcu": "line_type",
        "content_type": "source_table",
        "content_pk": "source_table_id",
        "invert_level_start_point": "invert_level_start_point",
        "invert_level_end_point": "invert_level_end_point",
        "dpumax": "exchange_level",
        "line__0": "calculation_node_id_start",
        "line__1": "calculation_node_id_end",
        "line_geometries": "the_geom",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._exporters = [
            exporters.LinesOgrExporter(self),
        ]

    @property
    def pipes(self):
        return self._filter_as(Pipes, content_type="v2_pipe")

    @property
    def weirs(self):
        return self._filter_as(Weirs, content_type="v2_weir")

    @property
    def orifices(self):
        return self._filter_as(Orifices, content_type="v2_orifice")

    @property
    def channels(self):
        return self._filter_as(Channels, content_type="v2_channel")

    @property
    def culverts(self):
        return self._filter_as(Culverts, content_type="v2_culvert")

    @property
    def breaches(self):
        warnings.warn(
            "lines.breaches is going to be removed "
            " in the near future, please use the root breaches instead",
            UserWarning,
        )
        return self._filter_as(Breaches, kcu=55)

    @property
    def line_nodes(self):
        return np.dstack(self.line)[0]


class Pipes(Lines):
    display_name = ArrayField()
    friction_type = ArrayField()
    friction_value = ArrayField()
    material = ArrayField()
    cross_section_height = ArrayField()
    cross_section_width = ArrayField()
    cross_section_shape = ArrayField()
    sewerage_type = ArrayField()
    calculation_type = ArrayField()
    connection_node_start_pk = ArrayField()
    connection_node_end_pk = ArrayField()
    discharge_coefficient = ArrayField()


class Channels(Lines):
    code = ArrayField()
    calculation_type = ArrayField()
    dist_calc_points = ArrayField()
    connection_node_start_pk = ArrayField()
    connection_node_end_pk = ArrayField()
    discharge_coefficient = ArrayField()


class Weirs(Lines):
    code = ArrayField()
    display_name = ArrayField()
    discharge_coefficient_negative = ArrayField()
    discharge_coefficient_positive = ArrayField()
    sewerage = ArrayField()
    friction_type = ArrayField()
    friction_value = ArrayField()
    crest_type = ArrayField()
    crest_level = ArrayField()
    connection_node_start_pk = ArrayField()
    connection_node_end_pk = ArrayField()
    cross_section_height = ArrayField()
    cross_section_width = ArrayField()
    cross_section_shape = ArrayField()

    @property
    def line_coord_angles(self):
        # Filter raw values with content_type and content_pk
        # to always get the raw (metric) values
        # and not the reprojected ones to calculate
        # the angles with.
        content_type = self._datasource["content_type"][:]
        line_content_pk = self._datasource["content_pk"][:]
        pk_mask = np.isin(line_content_pk, self.content_pk)
        raw_values = self._datasource["line_coords"][:][
            :, (content_type == b"v2_weir") & pk_mask
        ]

        return self._get_field("line_coords").get_angles_in_degrees(raw_values)


class Culverts(Lines):
    display_name = ArrayField()
    code = ArrayField()
    calculation_type = ArrayField()
    dist_calc_points = ArrayField()
    cross_section_height = ArrayField()
    cross_section_width = ArrayField()
    cross_section_shape = ArrayField()
    friction_type = ArrayField()
    friction_value = ArrayField()
    discharge_coefficient_negative = ArrayField()
    discharge_coefficient_positive = ArrayField()
    connection_node_start_pk = ArrayField()
    connection_node_end_pk = ArrayField()


class Orifices(Lines):
    display_name = ArrayField()
    sewerage = ArrayField()
    friction_type = ArrayField()
    friction_value = ArrayField()
    crest_type = ArrayField()
    crest_level = ArrayField()
    discharge_coefficient_negative = ArrayField()
    discharge_coefficient_positive = ArrayField()
    connection_node_start_pk = ArrayField()
    connection_node_end_pk = ArrayField()


class Breaches(Lines):
    breach_id = MappedSubsetArrayField(
        array_to_map="breaches.id",
        map_from_array="breaches.levl",
        map_to_array="lines.id",
        subset_filter={"lines.kcu": subsets.KCU__IN_SUBSETS["POTENTIAL_BREACH"][0]},
    )

    content_pk = MappedSubsetArrayField(
        array_to_map="breaches.content_pk",
        map_from_array="breaches.levl",
        map_to_array="lines.id",
        subset_filter={"lines.kcu": subsets.KCU__IN_SUBSETS["POTENTIAL_BREACH"][0]},
    )

    levbr = MappedSubsetArrayField(
        array_to_map="breaches.levbr",
        map_from_array="breaches.levl",
        map_to_array="lines.id",
        subset_filter={"lines.kcu": subsets.KCU__IN_SUBSETS["POTENTIAL_BREACH"][0]},
    )

    levmat = MappedSubsetArrayField(
        array_to_map="breaches.levmat",
        map_from_array="breaches.levl",
        map_to_array="lines.id",
        subset_filter={"lines.kcu": subsets.KCU__IN_SUBSETS["POTENTIAL_BREACH"][0]},
    )

    levl = MappedSubsetArrayField(
        array_to_map="breaches.levl",
        map_from_array="breaches.levl",
        map_to_array="lines.id",
        subset_filter={"lines.kcu": subsets.KCU__IN_SUBSETS["POTENTIAL_BREACH"][0]},
    )

    coordinates = MappedSubsetArrayField(
        array_to_map="breaches.coordinates",
        map_from_array="breaches.levl",
        map_to_array="lines.id",
        subset_filter={"lines.kcu": subsets.KCU__IN_SUBSETS["POTENTIAL_BREACH"][0]},
    )

    discharge_coefficient_positive = ArrayField()
    discharge_coefficient_negative = ArrayField()
