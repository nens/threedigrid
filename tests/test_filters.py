import unittest

import numpy as np
from shapely.geometry import LineString, Point, Polygon

from threedigrid.orm.base.fields import ArrayField
from threedigrid.orm.base.filters import (
    BaseCompareFilter,
    BaseFilter,
    EqualsFilter,
    get_filter,
    InFilter,
)
from threedigrid.orm.fields import (
    BboxArrayField,
    LineArrayField,
    MultiLineArrayField,
    PointArrayField,
    PolygonArrayField,
)
from threedigrid.orm.filters import FILTER_MAP, GeometryIntersectionFilter, PointFilter


class BasicFilterTests(unittest.TestCase):
    def setUp(self):
        self.field = ArrayField()

    def test_base_filter(self):
        b = BaseFilter()
        with self.assertRaises(NotImplementedError):
            b.filter("foo")

    def test_repr(self):
        f = BaseCompareFilter("in", self.field, [1, 2, 3])
        self.assertTrue(repr(f))

    def test_get_filter_eq(self):
        """Test that we get a default EqualsFilter without keys."""
        f = get_filter(["content_type"], self.field, 3)
        self.assertIsInstance(f, EqualsFilter)

        # also works when 'eq' is explicitly given
        f = get_filter(["content_type", "eq"], self.field, 3)
        self.assertIsInstance(f, EqualsFilter)

    def test_eq_filter(self):
        f = EqualsFilter("content_type", self.field, np.array([1, 2]))
        filtered = f.filter({"content_type": np.array([1, 2])})
        self.assertTrue(filtered.all())

        filtered = f.filter({"content_type": np.array([1, 3])})
        self.assertFalse(filtered.all())

    def test_get_filter_in(self):
        f = get_filter(["content_pk", "in"], self.field, [2])
        self.assertIsInstance(f, InFilter)

    def test_get_filter_error(self):
        """get_filter fails with malformed splitted keys."""
        with self.assertRaises(ValueError):
            get_filter(["content_pk", "in", "foo"], self.field, [2])

        with self.assertRaises(ValueError):
            get_filter([], self.field, [2])

    def test_get_nonexisting_filter(self):
        with self.assertRaises(ValueError):
            get_filter(["content_type", "not_a_filter"], self.field, 3)


class PointFilterTests(unittest.TestCase):
    def setUp(self):
        self.field = PolygonArrayField()

    def test_get_point_filter(self):
        f = get_filter(
            ["cell_coords", "contains_point"],
            self.field,
            [1, 5],
            filter_map=FILTER_MAP,
        )
        self.assertIsInstance(f, PointFilter)

    def test_point_filter(self):
        f = PointFilter("coord_cells", self.field, np.array([1, 5]))
        filtered = f.filter(
            {"coord_cells": np.array([[0, 2], [0, 2], [6, 6], [10, 11]])}
        )
        self.assertTrue(filtered[0])
        self.assertFalse(filtered[1])


class GeometryIntersectionFilterTest(unittest.TestCase):
    def setUp(self):
        self.geometry = Polygon([[0, 0], [0, 1], [1, 1], [0, 0]])
        self.field = BboxArrayField()

    def test_get_intersect_geometry_filter(self):
        f = get_filter(
            ["cell_coords", "intersects_geometry"],
            BboxArrayField(),
            self.geometry,
            filter_map=FILTER_MAP,
        )
        self.assertIsInstance(f, GeometryIntersectionFilter)

    def test_intersection_geometry_filter_bbox_array(self):
        f = GeometryIntersectionFilter("cell_coords", BboxArrayField(), self.geometry)
        filtered = f.filter({"cell_coords": np.array([[0, 0, 1, 1], [2, 2, 3, 3]]).T})
        self.assertTrue(filtered[0])
        self.assertFalse(filtered[1])

    def test_intersection_geometry_filter_bbox_array_line_bbox(self):
        # the BBOX of the line intersects all cells, but the line intersects
        # only 3 cells.
        line = LineString([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5)])
        values = np.array([[0, 0, 1, 1], [0, 1, 0, 1], [1, 1, 2, 2], [1, 2, 1, 2]])
        f = GeometryIntersectionFilter("cell_coords", BboxArrayField(), line)
        filtered = f.filter({"cell_coords": values})
        self.assertTrue(filtered[0])
        self.assertTrue(filtered[2])
        self.assertTrue(filtered[3])
        self.assertFalse(filtered[1])

    def test_intersection_geometry_filter_bbox_array_line_bbox_nan(self):
        # the BBOX of the line intersects all cells, but the line intersects
        # only 3 cells.
        line = LineString([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5)])
        values = np.array(
            [[np.nan, 0, 1, 1], [np.nan, 1, 0, 1], [np.nan, 1, 2, 2], [np.nan, 2, 1, 2]]
        )
        f = GeometryIntersectionFilter("cell_coords", BboxArrayField(), line)
        filtered = f.filter({"cell_coords": values})
        self.assertFalse(filtered[0])
        self.assertTrue(filtered[2])
        self.assertTrue(filtered[3])
        self.assertFalse(filtered[1])

    def test_intersection_geometry_filter_line_array(self):
        f = GeometryIntersectionFilter("line_coords", LineArrayField(), self.geometry)
        filtered = f.filter({"line_coords": np.array([[0, 0, 1, 1], [2, 2, 3, 3]]).T})
        self.assertTrue(filtered[0])
        self.assertFalse(filtered[1])

    def test_intersection_geometry_filter_point_array(self):
        f = GeometryIntersectionFilter("coordinates", PointArrayField(), self.geometry)
        filtered = f.filter({"coordinates": np.array([[0.5, 2], [0.5, 2]])})
        self.assertTrue(filtered[0])
        self.assertFalse(filtered[1])

    def test_intersection_geometry_filter_polygon_array(self):
        f = GeometryIntersectionFilter(
            "coordinates", PolygonArrayField(), self.geometry
        )
        filtered = f.filter(
            {
                "coordinates": np.array(
                    [  # + sign shows the split between x, y coords
                        np.array([0, 0, 2, 2] + [0, 2, 2, 0]),
                        np.array([5, 6, 6] + [5, 6, 5]),
                    ],
                    dtype=object,
                )
            }
        )
        self.assertTrue(filtered[0])
        self.assertFalse(filtered[1])

    def test_intersection_geometry_filter_multiline_array(self):
        f = GeometryIntersectionFilter("coords", MultiLineArrayField(), self.geometry)
        filtered = f.filter(
            {
                "coords": np.array(
                    [  # + sign shows the split between x, y coords
                        np.array([0, 0.5, 2, 2] + [0, 0.5, 2, 0]),
                        np.array([5, 6, 6] + [5, 6, 5]),
                    ],
                    dtype=object,
                )
            }
        )
        self.assertTrue(filtered[0])
        self.assertFalse(filtered[1])

    def test_intersection_geometry_filter_point_geom(self):
        geometry = Point(0.5, 0.5)
        f = GeometryIntersectionFilter("coordinates", PointArrayField(), geometry)
        filtered = f.filter({"coordinates": np.array([[0.5, 2], [0.5, 2]])})
        self.assertTrue(filtered[0])
        self.assertFalse(filtered[1])

    def test_intersection_geometry_filter_line_geom(self):
        geometry = LineString([(0.5, 0.5), (1.5, 1.5)])
        f = GeometryIntersectionFilter("cell_coords", BboxArrayField(), geometry)
        filtered = f.filter({"cell_coords": np.array([[0, 0, 1, 1], [2, 2, 3, 3]]).T})
        self.assertTrue(filtered[0])
        self.assertFalse(filtered[1])
