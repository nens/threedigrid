# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import geojson
import json
import numpy as np

from threedigrid.admin.lines.models import Channels
from threedigrid.admin.lines.models import Culverts
from threedigrid.admin.lines.models import Pipes
from threedigrid.admin.lines.models import Orifices
from threedigrid.admin.lines.models import Weirs
from threedigrid.admin import constants
from threedigrid.orm.base.encoder import NumpyEncoder
from six.moves import range

FRICTION_CHEZY = 1
FRICTION_MANNING = 2

PIPE_FRICTION_FORMATS = {
    FRICTION_CHEZY: 'Chezy, %0.0f [m(1/2)/s]',
    FRICTION_MANNING: 'Manning, %0.3f s/[m1/3]'
}

SHAPE_RECTANGLE = 1
SHAPE_CIRCLE = 2
SHAPE_EGG = 3
SHAPE_TABULATED_RECTANGLE = 5
SHAPE_TABULATED_TRAPEZIUM = 6


def format_to_str(value, empty_value='--', format_string='%0.2f'):
    """
    Format value with format_string when evaluated as True
    else return the empty value
    """
    if not value:
        return empty_value
    return format_string % value


def friction_str(friction_value, friction_type):
    if friction_type not in PIPE_FRICTION_FORMATS:
        return 'unknown type=%d value=%f' % (friction_type, friction_value)

    return PIPE_FRICTION_FORMATS[friction_type] % friction_value


def cross_section_str(width, height, shape):
    if shape == SHAPE_TABULATED_RECTANGLE:
        return 'tabulated rect %s-%s' % (width, height)
    if shape == SHAPE_TABULATED_TRAPEZIUM:
        return 'tabulated trap %s-%s' % (width, height)

    if not width:
        width = 'NOT GIVEN'
    if not height:
        height = 'NOT GIVEN'

    lookup = {
        SHAPE_RECTANGLE: 'rectangle wxh={}mx{}m'.format(
            width, height),
        SHAPE_CIRCLE: 'circle dia={}m'.format(width),
        SHAPE_EGG: 'egg wxh={}mx{}m'.format(width, height),
    }

    return lookup[shape]


class ChannelsGeoJsonSerializer():
    def __init__(self, channels=None, data=None, indent=None):
        if channels:
            assert isinstance(channels, Channels)
        self._data = data
        self._channels = channels
        self._indent = indent

    @property
    def geos(self):
        if self._channels:
            selection = self._channels.to_dict()
        else:
            selection = self._data

        geos = []
        if 'line_geometries' not in selection:
            raise ValueError(
                "Can't return data as geojson "
                "for selection without geometries")

        for i in range(selection['id'].shape[-1]):
            # Pack line_coords as [[x1, y1], [x2, y2]]
            # rounded with LONLAT_DIGITS
            lines = geojson.LineString(
                    np.round(selection['line_geometries'][i].reshape(
                        (2, -1)).T, constants.LONLAT_DIGITS).tolist())

            cn_meta = [
                ['object type', constants.TYPE_V2_CHANNEL],
                ['code', selection['code'][i]],
                ['calculation type',
                    constants.CALCULATION_TYPES.get(
                        selection['calculation_type'][i],
                        'unknown [%s]' % selection['calculation_type'][i]
                    )
                 ],
                ['calculation node distance',
                    selection['dist_calc_points'][i] or '--'],
                ['connection node start',
                    selection['connection_node_start_pk'][i] or '--'],
                ['connection node end',
                    selection['connection_node_end_pk'][i] or '--'],
                ['line index', selection['id'][i]],
            ]
            cn_props = dict(
                line_idx=selection['id'][i],
                id=selection['id'][i],
                object_type=constants.TYPE_V2_CHANNEL,
                props={},
                zoom_category=selection['zoom_category'][i],
                meta=cn_meta,
                )
            feat = geojson.Feature(
                geometry=lines,
                properties=cn_props,
                )
            geos.append(feat)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps({
            'type': 'FeatureCollection',
            'features': geos,
        }, indent=self._indent, cls=NumpyEncoder)


class PipesGeoJsonSerializer():
    def __init__(self, pipes=None, data=None, indent=None):
        if pipes:
            assert isinstance(pipes, Pipes)
        self._data = data
        self._pipes = pipes
        self._indent = indent

    @property
    def geos(self):
        if self._pipes:
            selection = self._pipes.to_dict()
        else:
            selection = self._data

        geos = []
        if 'line_coords' not in selection:
            raise ValueError(
                "Can't return data as geojson "
                "for selection without geometries")

        for i in range(selection['id'].shape[-1]):
            # Pack line_coords as [[x1, y1], [x2, y2]]
            # rounded with LONLAT_DIGITS
            lines = geojson.LineString(
                    np.round(selection['line_coords'][:, i].reshape(
                        (2, -1)), constants.LONLAT_DIGITS).tolist())

            invert_level_start_point_str = format_to_str(
                -selection['invert_level_start_point'][i])
            invert_level_end_point_str = format_to_str(
                -selection['invert_level_end_point'][i])

            cross_section = cross_section_str(
                selection['cross_section_width'][i],
                selection['cross_section_height'][i],
                selection['cross_section_shape'][i])

            cn_meta = [
                ['object type', constants.TYPE_V2_PIPE],
                ['display name', selection['display_name'][i]],
                ['invert level start point',
                    '%s [m MSL]' % invert_level_start_point_str],
                ['invert level end point',
                    '%s [m MSL]' % invert_level_end_point_str],
                ['friction', friction_str(
                    selection['friction_value'][i],
                    selection['friction_type'][i])],
                ['cross section', cross_section],
                ['sewerage type', constants.SEWERAGE_TYPES.get(
                    selection['sewerage_type'][i], None)],
                ['calculation type',
                    constants.CALCULATION_TYPES.get(
                        selection['calculation_type'][i],
                        'unknown [%s]' % selection['calculation_type'][i]
                    )
                 ],
                ['connection node start',
                    selection['connection_node_start_pk'][i] or '--'],
                ['connection node end',
                    selection['connection_node_end_pk'][i] or '--'],
                ['line index', selection['id'][i]],
            ]
            cn_props = dict(
                line_idx=selection['id'][i],
                id=selection['id'][i],
                object_type=constants.TYPE_V2_PIPE,
                props=dict(
                    sewerage_type=selection['sewerage_type'][i],
                ),
                zoom_category=selection['zoom_category'][i],
                meta=cn_meta,
                )
            feat = geojson.Feature(
                geometry=lines,
                properties=cn_props,
                )
            geos.append(feat)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps({
            'type': 'FeatureCollection',
            'features': geos,
        }, indent=self._indent, cls=NumpyEncoder)


class WeirsGeoJsonSerializer():
    def __init__(self, weirs=None, data=None, indent=None):
        if weirs:
            assert isinstance(weirs, Weirs)
        self._data = data
        self._weirs = weirs
        self._indent = indent

    @property
    def geos(self):
        if self._weirs:
            selection = self._weirs.to_dict()
            line_coords_angles = self._weirs.line_coord_angles
            line_coords_centroids = self._weirs.to_centroid()['line_coords']
        else:
            selection = self._data
            line_coords_angles = self._data['line_coord_angles']
            line_coords_centroids = self._data['line_coords_centroids']

        geos = []

        for i in range(selection['id'].shape[-1]):
            # Pack line_coords as [[x1, y1], [x2, y2]]
            # rounded with LONLAT_DIGITS
            lines = geojson.Point(
                    line_coords_centroids[:, i].tolist())

            cn_meta = [
                ['object type', constants.TYPE_V2_WEIR],
                ['display name', selection['display_name'][i]],
                ['sewerage', str(selection['sewerage'][i] == 1)],
                ['discharge coeff. pos.',
                    "%0.1f" % selection['discharge_coefficient_positive'][i]
                    or '--'],
                ['discharge coeff. neg.',
                    "%0.1f" % selection['discharge_coefficient_negative'][i]
                    or '--'],
                ['friction', friction_str(
                    selection['friction_value'][i],
                    selection['friction_type'][i])],
                ['crest type', constants.CREST_TYPES.get(
                    selection['crest_type'][i], None)],
                ['crest level',
                    '-%0.2f [m MSL]' % selection['crest_level'][i]],
                ['connection node start',
                    selection['connection_node_start_pk'][i] or '--'],
                ['connection node end',
                    selection['connection_node_end_pk'][i] or '--'],
                ['line index', selection['id'][i]],
            ]
            cn_props = dict(
                line_idx=selection['id'][i],
                id=selection['id'][i],
                angle=line_coords_angles[i],
                object_type=constants.TYPE_V2_WEIR,
                zoom_category=selection['zoom_category'][i],
                meta=cn_meta,
                )
            feat = geojson.Feature(
                geometry=lines,
                properties=cn_props,
                )
            geos.append(feat)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps({
            'type': 'FeatureCollection',
            'features': geos,
        }, indent=self._indent, cls=NumpyEncoder)


class CulvertsGeoJsonSerializer():
    def __init__(self, culverts=None, data=None, indent=None):
        if culverts:
            assert isinstance(culverts, Culverts)
        self._data = data
        self._culverts = culverts
        self._indent = indent

    @property
    def geos(self):
        if self._culverts:
            selection = self._culverts.to_dict()
        else:
            selection = self._data

        geos = []

        if 'line_geometries' not in selection:
            raise ValueError(
                "Can't return data as geojson "
                "for selection without geometries")

        for i in range(selection['id'].shape[-1]):
            # Pack line_coords as [[x1, y1], [x2, y2]]
            # rounded with LONLAT_DIGITS
            lines = geojson.LineString(
                    np.round(selection['line_geometries'][i].reshape(
                        (2, -1)).T, constants.LONLAT_DIGITS).tolist())

            invert_level_start_point_str = format_to_str(
                -selection['invert_level_start_point'][i])
            invert_level_end_point_str = format_to_str(
                -selection['invert_level_end_point'][i])

            cross_section = cross_section_str(
                selection['cross_section_width'][i],
                selection['cross_section_height'][i],
                selection['cross_section_shape'][i])

            cn_meta = [
                ['object type', constants.TYPE_V2_CULVERT],
                ['display name', selection['display_name'][i]],
                ['code', selection['code'][i]],
                ['calculation type',
                    constants.CALCULATION_TYPES.get(
                        selection['calculation_type'][i],
                        'unknown [%s]' % selection['calculation_type'][i]
                    )
                 ],
                ['calculation node distance',
                    selection['dist_calc_points'][i] or '--'],
                ['cross section', cross_section],
                ['friction', friction_str(
                    selection['friction_value'][i],
                    selection['friction_type'][i])],
                ['discharge coeff. pos.',
                    "%0.1f" % selection['discharge_coefficient_positive'][i]
                    or '--'],
                ['discharge coeff. neg.',
                    "%0.1f" % selection['discharge_coefficient_negative'][i]
                    or '--'],
                ['invert level start point',
                    '%s [m MSL]' % invert_level_start_point_str],
                ['invert level end point',
                    '%s [m MSL]' % invert_level_end_point_str],
                ['connection node start',
                    selection['connection_node_start_pk'][i] or '--'],
                ['connection node end',
                    selection['connection_node_end_pk'][i] or '--'],
                ['line index', selection['id'][i]],
            ]
            cn_props = dict(
                line_idx=selection['id'][i],
                id=selection['id'][i],
                object_type=constants.TYPE_V2_CULVERT,
                zoom_category=selection['zoom_category'][i],
                meta=cn_meta,
                )
            feat = geojson.Feature(
                geometry=lines,
                properties=cn_props,
                )
            geos.append(feat)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps({
            'type': 'FeatureCollection',
            'features': geos,
        }, indent=self._indent, cls=NumpyEncoder)


class OrificesGeoJsonSerializer():
    def __init__(self, orifices=None, data=None, indent=None):
        if orifices:
            assert isinstance(orifices, Orifices)
        self._data = data
        self._orifices = orifices
        self._indent = indent

    @property
    def geos(self):
        if self._orifices:
            selection = self._orifices.to_dict()
        else:
            selection = self._data

        geos = []

        for i in range(selection['id'].shape[-1]):
            # Pack line_coords as [[x1, y1], [x2, y2]]
            # rounded with LONLAT_DIGITS
            lines = geojson.LineString(
                    np.round(selection['line_coords'][:, i].reshape(
                        (2, -1)), constants.LONLAT_DIGITS).tolist())

            cn_meta = [
                ['object type', constants.TYPE_V2_ORIFICE],
                ['display name', selection['display_name'][i]],
                ['sewerage', str(selection['sewerage'][i] == 1)],
                ['max capacity', '%s [m3/s]' % str(
                    selection['max_capacity'][i] if
                    selection['max_capacity'][i] else '--')],
                ['discharge coeff. pos.',
                    "%0.1f" % selection['discharge_coefficient_positive'][i]
                    or '--'],
                ['discharge coeff. neg.',
                    "%0.1f" % selection['discharge_coefficient_negative'][i]
                    or '--'],
                ['friction', friction_str(
                    selection['friction_value'][i],
                    selection['friction_type'][i])],
                ['crest level',
                    '-%0.2f [m MSL]' % selection['crest_level'][i]],
                ['connection node start',
                    selection['connection_node_start_pk'][i] or '--'],
                ['connection node end',
                    selection['connection_node_end_pk'][i] or '--'],
                ['line index', selection['id'][i]],
            ]
            cn_props = dict(
                line_idx=selection['id'][i],
                id=None,
                object_type=constants.TYPE_V2_ORIFICE,
                zoom_category=selection['zoom_category'][i],
                meta=cn_meta,
                )
            feat = geojson.Feature(
                geometry=lines,
                properties=cn_props,
                )
            geos.append(feat)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps({
            'type': 'FeatureCollection',
            'features': geos,
        }, indent=self._indent, cls=NumpyEncoder)
