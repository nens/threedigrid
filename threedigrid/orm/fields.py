# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np

from .base.fields import ArrayField
from threedigrid.numpy_utils import angle_in_degrees
from threedigrid.numpy_utils import get_bbox_by_point
from threedigrid.numpy_utils import reshape_flat_array
from threedigrid.numpy_utils import select_lines_by_bbox
from threedigrid.geo_utils import select_points_by_tile, \
    select_geoms_by_geometry, raise_import_exception
from threedigrid.geo_utils import select_lines_by_tile
from threedigrid.geo_utils import select_points_by_bbox
from threedigrid.geo_utils import transform_xys
from six.moves import map

try:
    from pyproj import Transformer
except ImportError:
    Transformer = None

try:
    import shapely
    from shapely.geometry import Polygon, Point, asLineString, asPolygon
except ImportError:
    shapely = None


class GeomArrayField(ArrayField):
    """
    Base geometry field
    """
    def reproject(self, values, source_epsg, target_epsg):
        raise NotImplementedError()

    def to_centroid(self, values):
        raise NotImplementedError()

    def get_mask_by_geometry(self, geometry, values):
        geoms = self._to_shapely_geom(values)

        selected_geoms = select_geoms_by_geometry(geoms, geometry)

        mask = np.zeros((len(values.T),), dtype=bool)
        for geom in selected_geoms:
            mask[geom.index] = True

        return mask

    def _to_shapely_geom(self, values):
        """Returns a list of shapely geometries created from values

        :param values: coordinates
        :return: list of shapely geometries
        """
        raise NotImplementedError()


class PointArrayField(GeomArrayField):
    def reproject(self, values, source_epsg, target_epsg):
        """
        Reproject the point coordinates: x_array=values[0], y_array=values[1]
        from source_epsg to target_epsg.
        """
        return transform_xys(
            values[0], values[1],
            source_epsg, target_epsg)

    def get_mask_by_bbox(self, bbox, values, include_intersections=False):
        """
        Return as boolean mask (np.array) for line/bbox in "values"
            x_array=values[0], y_array=values[1]
        within bbox (x1, y1, x2, y2)
        """
        # For points include_intersections can be ignored
        return select_points_by_bbox(values, bbox)

    def get_mask_by_tile(self, tile_xyz, target_epsg, values,
                         include_intersections=False):
        """
        Return as boolean mask (np.array) for points in "values"
        within tile_xyz bbox projected to target_epsg.
        """
        # For points include_intersections can be ignored
        return select_points_by_tile(
            tile_xyz, target_epsg, values)

    def to_centroid(self, values):
        """
        Returns: the centroid of the point coordinates:
                 x_array=values[0], y_array=values[1]
        """
        return values

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception('shapely')

        points = []
        for i, coord in enumerate(values.T):
            point = Point(coord[0], coord[1])
            point.index = i  # the index is used in get_mask_by_geometry
            points.append(point)
        return points


class LineArrayField(GeomArrayField):
    """
    Field which handles line/bbox geoms values:

        x1_array=values[0], y1_array=values[1],
        x2_array=values[2], y2_array=values[3]
    """

    def reproject(self, values, source_epsg, target_epsg):
        """
        Reproject the line/bbox coordinates:
            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]
        from source_epsg to target_epsg.
        """
        return np.vstack((
                transform_xys(
                    values[0], values[1],
                    source_epsg, target_epsg),
                transform_xys(
                    values[2], values[3],
                    source_epsg, target_epsg)))

    def get_mask_by_point(self, pnt, values):
        return get_bbox_by_point(pnt, values)

    def get_mask_by_bbox(self, bbox, values,
                         include_intersections=False):
        """
        Return as boolean mask (np.array) for line/bbox in "values"
            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]
        within bbox (x1, y1, x2, y2)
        """
        return select_lines_by_bbox(values, bbox, include_intersections)

    def get_mask_by_tile(self, tile_xyz, target_epsg, values,
                         include_intersections=False):
        """
        Return as boolean mask (np.array) for line/bbox in "values"
            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]
        within tile_xyz bbox projected to target_epsg.
        """
        return select_lines_by_tile(
            tile_xyz, target_epsg, values, include_intersections)

    def to_centroid(self, values):
        """
        :return: the centroid (float) for the line coordinates:
                    x1_array=values[0], y1_array=values[1],
                    x2_array=values[2], y2_array=values[3]
        """
        return np.array(
            ((values[0] + values[2]) / 2.0,
             (values[1] + values[3]) / 2.0))

    def get_angles_in_degrees(self, values):
        """
        Returns: the angles in degrees of the lines
        made up by the points:

            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]

        with the (horizontal) x-axis
        """
        return angle_in_degrees(
                values[0], values[1], values[2], values[3])

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception('shapely')

        lines = []
        for i, coords in enumerate(values.T):
            line = asLineString(coords.reshape((2, -1)))
            line.index = i  # the index is used in get_mask_by_geometry
            lines.append(line)
        return lines


class MultiLineArrayField(GeomArrayField):

    def reproject(self, values, source_epsg, target_epsg):
        """
        Reproject the line/bbox coordinates:
            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]
        from source_epsg to target_epsg.
        """
        reshaped_values = list(map(reshape_flat_array, values))

        # Pyproj has (a lot) more overhead
        # from 2.0.1 for reprojecting.
        # so created the Transform once
        # and reuse it.
        if Transformer is not None:
            # Only use the Transformer if it is present
            # in Python 3 it works well, however in Python 2.7
            # it seams to break
            transformer = Transformer.from_proj(
                int(source_epsg), int(target_epsg), always_xy=True
            )

            transform_values = [
                np.array(transformer.transform(x[0], x[1])).flatten()
                for x in reshaped_values
            ]
        else:
            transform_values = [
                transform_xys(x[0], x[1], source_epsg, target_epsg).flatten()
                for x in reshaped_values
            ]

        return np.array(transform_values, dtype=object)

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception('shapely')

        multilines = []
        for i, coords in enumerate(values):
            line = asLineString(coords.reshape((2, -1)).T)
            line.index = i  # the index is used in get_mask_by_geometry
            multilines.append(line)
        return multilines


class PolygonArrayField(GeomArrayField):
    """
    Field which handles line/bbox geoms values:

        x1_array=values[0], y1_array=values[1],
        x2_array=values[2], y2_array=values[3]

    """
    def get_mask_by_point(self, pnt, values):

        return get_bbox_by_point(pnt, values)

    def reproject(self, values, source_epsg, target_epsg):
        """
        Reproject the cell coordinates (lower left and
        upper right corners):
            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3],
        from source_epsg to target_epsg.
        """
        return np.vstack((
                np.array(transform_xys(
                    values[0], values[1],
                    source_epsg, target_epsg)
                ),
                np.array(transform_xys(
                    values[2], values[3],
                    source_epsg, target_epsg)
                ),
        ))

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception('shapely')

        polygons = []
        for i, coords in enumerate(values):
            polygon = asPolygon(coords.reshape((2, -1)).T)
            polygon.index = i  # the index is used in get_mask_by_geometry
            polygons.append(polygon)
        return polygons


class BboxArrayField(LineArrayField):

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception('shapely')

        polygons = []
        for i, coord in enumerate(values.T):
            # convert the bbox bottom-left and upper-right into a polygon
            polygon = Polygon(
                [
                    (coord[0], coord[1]),
                    (coord[0], coord[3]),
                    (coord[2], coord[3]),
                    (coord[2], coord[1])
                ]
            )
            polygon.index = i  # the index is used in get_mask_by_geometry
            polygons.append(polygon)
        return polygons
