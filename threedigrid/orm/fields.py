# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

import numpy as np

from threedigrid.geo_utils import (
    get_transformer,
    raise_import_exception,
    select_geoms_by_geometry,
    select_lines_by_tile,
    select_points_by_bbox,
    select_points_by_tile,
    transform_xys,
)
from threedigrid.numpy_utils import (
    angle_in_degrees,
    get_bbox_by_point,
    reshape_flat_array,
    select_lines_by_bbox,
)

from .base.fields import ArrayField

try:
    import shapely
    from shapely.geometry import LineString, Point, Polygon
except ImportError:
    shapely = None


NULL_VALUE = -9999.0


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

        intersects_i = select_geoms_by_geometry(geoms, geometry)

        mask = np.zeros((len(values.T),), dtype=bool)
        mask[np.array(intersects_i, dtype=int)] = True
        return mask

    def _to_shapely_geom(self, values):
        """Returns a list of shapely geometries created from values

        :param values: coordinates
        :return: list of shapely geometries
        """
        raise NotImplementedError()


class PointArrayField(GeomArrayField):
    type = "point"

    def reproject(self, values, source_epsg, target_epsg):
        """
        Reproject the point coordinates: x_array=values[0], y_array=values[1]
        from source_epsg to target_epsg.
        """
        return transform_xys(values[0], values[1], source_epsg, target_epsg)

    def get_mask_by_bbox(self, bbox, values, include_intersections=False):
        """
        Return as boolean mask (np.array) for line/bbox in "values"
            x_array=values[0], y_array=values[1]
        within bbox (x1, y1, x2, y2)
        """
        # For points include_intersections can be ignored
        return select_points_by_bbox(values, bbox)

    def get_mask_by_tile(
        self, tile_xyz, target_epsg, values, include_intersections=False
    ):
        """
        Return as boolean mask (np.array) for points in "values"
        within tile_xyz bbox projected to target_epsg.
        """
        # For points include_intersections can be ignored
        return select_points_by_tile(tile_xyz, target_epsg, values)

    def to_centroid(self, values):
        """
        Returns: the centroid of the point coordinates:
                 x_array=values[0], y_array=values[1]
        """
        return values

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception("shapely")

        points = []
        for coord in values.T:
            if np.isnan(coord).all():
                coord = np.full_like(coord, fill_value=NULL_VALUE)

            point = Point(coord[0], coord[1])
            points.append(point)

        return points


class LineArrayField(GeomArrayField):
    type = "line"

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
        return np.vstack(
            (
                transform_xys(values[0], values[1], source_epsg, target_epsg),
                transform_xys(values[2], values[3], source_epsg, target_epsg),
            )
        )

    def get_mask_by_point(self, pnt, values):
        return get_bbox_by_point(pnt, values)

    def get_mask_by_bbox(self, bbox, values, include_intersections=False):
        """
        Return as boolean mask (np.array) for line/bbox in "values"
            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]
        within bbox (x1, y1, x2, y2)
        """
        return select_lines_by_bbox(values, bbox, include_intersections)

    def get_mask_by_tile(
        self, tile_xyz, target_epsg, values, include_intersections=False
    ):
        """
        Return as boolean mask (np.array) for line/bbox in "values"
            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]
        within tile_xyz bbox projected to target_epsg.
        """
        return select_lines_by_tile(
            tile_xyz, target_epsg, values, include_intersections
        )

    def to_centroid(self, values):
        """
        :return: the centroid (float) for the line coordinates:
                    x1_array=values[0], y1_array=values[1],
                    x2_array=values[2], y2_array=values[3]
        """
        return np.array(((values[0] + values[2]) / 2.0, (values[1] + values[3]) / 2.0))

    def get_angles_in_degrees(self, values):
        """
        Returns: the angles in degrees of the lines
        made up by the points:

            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]

        with the (horizontal) x-axis
        """
        if np.isnan(values).all():
            values = np.full_like(values, fill_value=NULL_VALUE)

        return angle_in_degrees(values[0], values[1], values[2], values[3])

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception("shapely")

        lines = []
        for coords in values.T:
            if np.isnan(coords).all():
                coords = np.full_like(coords, fill_value=NULL_VALUE)
            line = LineString(coords.reshape((2, -1)))
            lines.append(line)
        return lines


class MultiLineArrayField(GeomArrayField):
    type = "multiline"

    def reproject(self, values, source_epsg, target_epsg):
        """
        Reproject the line/bbox coordinates:
            x1_array=values[0], y1_array=values[1],
            x2_array=values[2], y2_array=values[3]
        from source_epsg to target_epsg.
        """
        reshaped_values = list(map(reshape_flat_array, values))

        transformer = get_transformer(source_epsg, target_epsg)
        transform_values = [
            np.array(transformer.transform(x[0], x[1])).flatten()
            for x in reshaped_values
        ]
        return np.array(transform_values, dtype=object)

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception("shapely")

        multilines = []
        for coords in values:
            if np.isnan(coords).all():
                coords = np.full_like(coords, fill_value=NULL_VALUE)

            line = LineString(coords.reshape((2, -1)).T)
            multilines.append(line)
        return multilines


class PolygonArrayField(GeomArrayField):
    """
    Field which handles line/bbox geoms values:

        x1_array=values[0], y1_array=values[1],
        x2_array=values[2], y2_array=values[3]

    """

    type = "polygon"

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
        return np.vstack(
            (
                np.array(transform_xys(values[0], values[1], source_epsg, target_epsg)),
                np.array(transform_xys(values[2], values[3], source_epsg, target_epsg)),
            )
        )

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception("shapely")

        polygons = []
        for coords in values:
            if np.isnan(coords).all():
                coords = np.full_like(coords, fill_value=NULL_VALUE)
            polygon = Polygon(coords.reshape((2, -1)).T)
            polygons.append(polygon)
        return polygons


class BboxArrayField(LineArrayField):
    type = "bbox"

    def _to_shapely_geom(self, values):
        if shapely is None:
            raise_import_exception("shapely")

        polygons = []
        for coord in values.T:
            if np.isnan(coord).all():
                coord = np.full_like(coord, fill_value=NULL_VALUE)

            # convert the bbox bottom-left and upper-right into a polygon
            polygon = Polygon(
                [
                    (coord[0], coord[1]),
                    (coord[0], coord[3]),
                    (coord[2], coord[3]),
                    (coord[2], coord[1]),
                ]
            )
            polygons.append(polygon)
        return polygons
