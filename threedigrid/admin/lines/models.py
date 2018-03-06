# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np

from threedigrid.admin.lines import exporters
from threedigrid.orm.models import Model
from threedigrid.orm.fields import (
    ArrayField, LineArrayField, MultiLineArrayField)
from threedigrid.orm.base.fields import IndexArrayField
from threedigrid.admin.lines import subsets


LINE_SUBSETS = {
    'kcu__in': subsets.KCU__IN_SUBSETS
}


class Lines(Model):
    kcu = ArrayField()
    lik = ArrayField()
    line = IndexArrayField(to='Nodes')
    content_pk = ArrayField()
    content_type = ArrayField()
    zoom_category = ArrayField()
    line_coords = LineArrayField()
    line_geometries = MultiLineArrayField()
    SUBSETS = LINE_SUBSETS

    def __init__(self, *args,  **kwargs):
        super(Lines, self).__init__(*args, **kwargs)

        self._exporters = [
            exporters.LinesOgrExporter(self),
        ]

    @property
    def v2_channels(self):
        return self.filter(content_type='v2_channel')

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
    def line_nodes(self):
        return np.dstack(self.line)[0]


class Pipes(Lines):
    display_name = ArrayField()
    invert_level_start_point = ArrayField()
    invert_level_end_point = ArrayField()
    friction_type = ArrayField()
    friction_value = ArrayField()
    cross_section_height = ArrayField()
    cross_section_width = ArrayField()
    cross_section_shape = ArrayField()
    sewerage_type = ArrayField()
    calculation_type = ArrayField()
    connection_node_start_pk = ArrayField()
    connection_node_end_pk = ArrayField()


class Channels(Lines):
    code = ArrayField()
    calculation_type = ArrayField()
    dist_calc_points = ArrayField()
    connection_node_start_pk = ArrayField()
    connection_node_end_pk = ArrayField()


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

    @property
    def line_coord_angles(self):
        # Filter raw values with content_type and content_pk
        # to always get the raw (metric) values
        # and not the reprojected ones to calculate
        # the angles with.
        content_type = self._datasource['content_type'].value
        line_content_pk = self._datasource['content_pk'].value
        pk_mask = np.isin(line_content_pk, self.content_pk)
        raw_values = self._datasource['line_coords'].value[
            :, (content_type == 'v2_weir') & pk_mask]

        return self.get_field('line_coords').get_angles_in_degrees(
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
    max_capacity = ArrayField()
    friction_type = ArrayField()
    friction_value = ArrayField()
    crest_type = ArrayField()
    crest_level = ArrayField()
    discharge_coefficient_negative = ArrayField()
    discharge_coefficient_positive = ArrayField()
    connection_node_start_pk = ArrayField()
    connection_node_end_pk = ArrayField()
