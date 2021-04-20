# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Models
++++++
In the threedicore lines are called flow lines and represent links between
calculation points. They can exist between 1d and 2d points, between surface
and groundwater nodes etc. The line type is described by the kcu attribute
For an overview of the kcu types see :ref:`kcu-label`.
"""

from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np

from threedigrid.admin.lines import exporters
from threedigrid.orm.models import Model
from threedigrid.orm.fields import (
    ArrayField, LineArrayField, MultiLineArrayField)
from threedigrid.orm.base.fields import IndexArrayField, MappedSubsetArrayField
from threedigrid.admin.lines import subsets


LINE_SUBSETS = {
    'kcu__in': subsets.KCU__IN_SUBSETS
}


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
    kcu = ArrayField()
    lik = ArrayField()
    line = IndexArrayField(to='Nodes')
    content_pk = ArrayField()
    content_type = ArrayField()
    zoom_category = ArrayField()
    cross_pix_coords = LineArrayField()
    line_coords = LineArrayField()
    line_geometries = MultiLineArrayField()
    SUBSETS = LINE_SUBSETS

    def __init__(self, *args,  **kwargs):
        super(Lines, self).__init__(*args, **kwargs)

        self._exporters = [
            exporters.LinesOgrExporter(self),
        ]

    @property
    def pipes(self):
        return self._filter_as(Pipes, content_type='v2_pipe')

    @property
    def weirs(self):
        return self._filter_as(Weirs, content_type='v2_weir')

    @property
    def orifices(self):
        return self._filter_as(Orifices, content_type='v2_orifice')

    @property
    def channels(self):
        return self._filter_as(Channels, content_type='v2_channel')

    @property
    def culverts(self):
        return self._filter_as(Culverts, content_type='v2_culvert')

    @property
    def breaches(self):
        return self._filter_as(Breaches, kcu=55)

    @property
    def line_nodes(self):
        return np.dstack(self.line)[0]


class Pipes(Lines):
    display_name = ArrayField()
    invert_level_start_point = ArrayField()
    invert_level_end_point = ArrayField()
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
        content_type = self._datasource['content_type'][:]
        line_content_pk = self._datasource['content_pk'][:]
        pk_mask = np.isin(line_content_pk, self.content_pk)
        raw_values = self._datasource['line_coords'][:][
            :, (content_type == b'v2_weir') & pk_mask]

        return self._get_field('line_coords').get_angles_in_degrees(
            raw_values)


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
    invert_level_start_point = ArrayField()
    invert_level_end_point = ArrayField()
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
        array_to_map='breaches.id',
        map_from_array='breaches.levl', map_to_array='lines.id',
        subset_filter={
            'lines.kcu': subsets.KCU__IN_SUBSETS['POTENTIAL_BREACH'][0]})

    content_pk = MappedSubsetArrayField(
        array_to_map='breaches.content_pk',
        map_from_array='breaches.levl', map_to_array='lines.id',
        subset_filter={
            'lines.kcu': subsets.KCU__IN_SUBSETS['POTENTIAL_BREACH'][0]})

    levbr = MappedSubsetArrayField(
        array_to_map='breaches.levbr',
        map_from_array='breaches.levl', map_to_array='lines.id',
        subset_filter={
            'lines.kcu': subsets.KCU__IN_SUBSETS['POTENTIAL_BREACH'][0]})

    levmat = MappedSubsetArrayField(
        array_to_map='breaches.levmat',
        map_from_array='breaches.levl', map_to_array='lines.id',
        subset_filter={
            'lines.kcu': subsets.KCU__IN_SUBSETS['POTENTIAL_BREACH'][0]})

    coordinates = MappedSubsetArrayField(
        array_to_map='breaches.coordinates',
        map_from_array='breaches.levl', map_to_array='lines.id',
        subset_filter={
            'lines.kcu': subsets.KCU__IN_SUBSETS['POTENTIAL_BREACH'][0]})
