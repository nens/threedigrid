# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
Models
++++++
In the threedicore lines are called flow lines and represent links between
calculation points. They can exist between 1d and 2d points, between surface
and groundwater nodes etc. The line type is described by the kcu attribute
For an overview of the kcu types see :ref:`kcu-label`.
"""


import numpy as np

from threedigrid.admin.lines import exporters, subsets
from threedigrid.orm.base.fields import IndexArrayField
from threedigrid.orm.fields import ArrayField, LineArrayField, MultiLineArrayField
from threedigrid.orm.models import Model

LINE_SUBSETS = {"kcu__in": subsets.KCU__IN_SUBSETS}


def convert_pixel_coords(i, j, geo_transform):
    a, b, c, d, e, f = geo_transform
    x = a * i + b * j + c
    y = d * i + e * j + f
    return (x, y)


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
    cross_pix_coords = LineArrayField()
    line_coords = LineArrayField()
    line_geometries = MultiLineArrayField()
    discharge_coefficient_negative = ArrayField(type=float)
    discharge_coefficient_positive = ArrayField(type=float)
    sewerage = ArrayField(type=bool)
    sewerage_type = ArrayField(type=int)

    SUBSETS = LINE_SUBSETS

    GPKG_DEFAULT_FIELD_MAP = {
        "id": "id",
        "discharge_coefficient_positive": "discharge_coefficient_positive",
        "discharge_coefficient_negative": "discharge_coefficient_negative",
        "kcu": "line_type",
        "content_type": "source_table",
        "content_pk": "source_table_id",
        "invert_level_start_point": "invert_level_start_point",
        "invert_level_end_point": "invert_level_end_point",
        "dpumax": "exchange_level",
        "line__0": "calculation_node_id_start",
        "line__1": "calculation_node_id_end",
        "line_geometries": "the_geom",
        "sewerage": "sewerage",
        "sewerage_type": "sewerage_type",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._exporters = [
            exporters.LinesOgrExporter(self),
        ]

    def cross_pix_coords_transformed(self, geo_transform):
        """
        Get pix_coords transformed by geo_transform (=ga.grid.transform)

        >>> x = a * i + b * j + c
        >>> y = d * i + e * j + f

        """
        x, y = convert_pixel_coords(
            self.cross_pix_coords[0], self.cross_pix_coords[1], geo_transform
        )
        x2, y2 = convert_pixel_coords(
            self.cross_pix_coords[2], self.cross_pix_coords[3], geo_transform
        )
        return np.vstack([x, y, x2, y2])

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
    def line_nodes(self):
        return np.dstack(self.line)[0]


class Pipes(Lines):
    display_name = ArrayField(type=str)
    friction_type = ArrayField(type=int)
    friction_value = ArrayField(type=float)
    material = ArrayField(type=int)
    cross_section_height = ArrayField(type=float)
    cross_section_width = ArrayField(type=float)
    cross_section_shape = ArrayField(type=float)
    sewerage_type = ArrayField(type=int)
    calculation_type = ArrayField(type=int)
    connection_node_start_pk = ArrayField(type=int)
    connection_node_end_pk = ArrayField(type=int)
    discharge_coefficient = ArrayField(type=float)


class Channels(Lines):
    code = ArrayField(type=str)
    calculation_type = ArrayField(type=int)
    dist_calc_points = ArrayField(type=float)
    connection_node_start_pk = ArrayField(type=int)
    connection_node_end_pk = ArrayField(type=int)
    discharge_coefficient = ArrayField(type=float)


class Weirs(Lines):
    code = ArrayField(type=str)
    display_name = ArrayField(type=str)
    sewerage = ArrayField(type=int)
    friction_type = ArrayField(type=int)
    friction_value = ArrayField(type=float)
    crest_type = ArrayField(type=int)
    crest_level = ArrayField(type=float)
    connection_node_start_pk = ArrayField(type=int)
    connection_node_end_pk = ArrayField(type=int)
    cross_section_height = ArrayField(type=float)
    cross_section_width = ArrayField(type=float)
    cross_section_shape = ArrayField(type=float)

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
    display_name = ArrayField(type=str)
    code = ArrayField(type=str)
    calculation_type = ArrayField(type=int)
    dist_calc_points = ArrayField(type=float)
    cross_section_height = ArrayField(type=float)
    cross_section_width = ArrayField(type=float)
    cross_section_shape = ArrayField(type=float)
    friction_type = ArrayField(type=int)
    friction_value = ArrayField(type=float)
    connection_node_start_pk = ArrayField(type=int)
    connection_node_end_pk = ArrayField(type=int)


class Orifices(Lines):
    display_name = ArrayField(type=str)
    sewerage = ArrayField(type=int)
    friction_type = ArrayField(type=int)
    friction_value = ArrayField(type=float)
    crest_type = ArrayField(type=int)
    crest_level = ArrayField(type=float)
    connection_node_start_pk = ArrayField(type=int)
    connection_node_end_pk = ArrayField(type=int)
