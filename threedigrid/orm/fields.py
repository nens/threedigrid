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
from threedigrid.geo_utils import select_points_by_tile
from threedigrid.geo_utils import select_lines_by_tile
from threedigrid.geo_utils import select_points_by_bbox
from threedigrid.geo_utils import transform_xys
from six.moves import map


class GeomArrayField(ArrayField):
    """
    Base geometry field
    """
    def reproject(self, values, source_epsg, target_epsg):
        raise NotImplementedError()

    def to_centroid(self, values):
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


class MultiLineArrayField(GeomArrayField):

    def reproject(self, values, source_epsg, target_epsg):
        """
        Reproject the line/bbox coordinates:
            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]
        from source_epsg to target_epsg.
        """
        reshaped_values = list(map(reshape_flat_array, values))
        transform_values = [
            transform_xys(x[0], x[1], source_epsg, target_epsg).flatten()
            for x in reshaped_values
        ]

        return np.array(transform_values)


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


class BboxArrayField(LineArrayField):
    """
    For now handled same as lines.
    """
    pass
