import os
import shutil
import tempfile
import unittest

import numpy as np
from osgeo import ogr
from pyproj import CRS

from threedigrid.admin.breaches.exporters import BreachesOgrExporter
from threedigrid.admin.constants import (
    NO_DATA_VALUE,
    SUBSET_1D_ALL,
    SUBSET_2D_OPEN_WATER,
)
from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.lines.exporters import LinesOgrExporter
from threedigrid.admin.nodes.exporters import CellsOgrExporter, NodesOgrExporter

test_file_dir = os.path.join(os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
grid_admin_h5_file = os.path.join(test_file_dir, "gridadmin_v2.h5")


class GridAdminTest(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)

    def test_get_from_meta(self):
        self.assertIsNotNone(self.parser.get_from_meta("n2dtot"))
        self.assertIsNone(self.parser.get_from_meta("doesnotexist"))

    def test_get_extent_subset_onedee(self):
        extent_1D = self.parser.get_extent_subset(subset_name=SUBSET_1D_ALL)
        # should contain values
        self.assertTrue(np.any(extent_1D != NO_DATA_VALUE))

    def test_get_extent_subset_reproject(self):
        extent_1D = self.parser.get_extent_subset(subset_name=SUBSET_1D_ALL)
        extent_1D_proj = self.parser.get_extent_subset(
            subset_name=SUBSET_1D_ALL, target_epsg_code="4326"
        )
        self.assertTrue(np.all(extent_1D != extent_1D_proj))

    def test_get_extent_subset_twodee(self):
        extent_2D = self.parser.get_extent_subset(subset_name=SUBSET_2D_OPEN_WATER)
        # should contain values
        self.assertTrue(np.any(extent_2D != NO_DATA_VALUE))

    def test_get_extent_subset_combi(self):
        extent_1D = self.parser.get_extent_subset(subset_name=SUBSET_1D_ALL)
        extent_2D = self.parser.get_extent_subset(subset_name=SUBSET_2D_OPEN_WATER)
        # should be different
        self.assertTrue(np.any(np.not_equal(extent_1D, extent_2D)))

    def test_get_model_extent(self):
        model_extent = self.parser.get_model_extent()
        np.testing.assert_almost_equal(
            model_extent,
            np.array([105427.6, 511727.0515702, 115887.0, 523463.3268483]),
            decimal=3,
        )

    def test_get_model_extent_extra_extent(self):
        onedee_extra = np.array([100000.0, 90000.0, 550000.0, 580000.0])

        extra_extent = {"extra_extent": [onedee_extra]}
        model_extent = self.parser.get_model_extent(**extra_extent)
        np.testing.assert_equal(
            model_extent, np.array([100000.0, 90000.0, 550000.0, 580000.0])
        )

    def test_get_model_extent_extra_extent2(self):
        onedee_extra = np.array([106666.6, 106666.6, 550000.0, 580000.0])

        extra_extent = {"extra_extent": [onedee_extra]}
        model_extent = self.parser.get_model_extent(**extra_extent)
        np.testing.assert_almost_equal(
            model_extent, np.array([105427.6, 106666.6, 550000.0, 580000.0]), decimal=3
        )

    def test_properties(self):
        self.assertTrue(hasattr(self.parser, "has_groundwater"))
        self.assertTrue(hasattr(self.parser, "has_levees"))
        self.assertTrue(hasattr(self.parser, "threedicore_version"))
        self.assertTrue(hasattr(self.parser, "has_1d"))
        self.assertTrue(hasattr(self.parser, "has_2d"))
        self.assertTrue(hasattr(self.parser, "epsg_code"))
        self.assertTrue(hasattr(self.parser, "revision_hash"))
        self.assertTrue(hasattr(self.parser, "revision_nr"))
        self.assertTrue(hasattr(self.parser, "model_slug"))

    def test_crs(self):
        crs = self.parser.crs
        assert isinstance(crs, CRS)
        assert crs.to_epsg() == 28992 or "28992" in crs.srs


class GridAdminLinesTest(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f = os.path.join(d, "test_lines.shp")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f))

    def test_fields(self):
        # Check dtype names
        assert set(self.parser.lines._meta.get_fields().keys()) == {
            "content_pk",
            "content_type",
            "id",
            "kcu",
            "lik",
            "line",
            "dpumax",
            "flod",
            "flou",
            "cross1",
            "cross2",
            "ds1d",
            "line_coords",
            "cross_pix_coords",
            "cross_weight",
            "discharge_coefficient_negative",
            "discharge_coefficient_positive",
            "line_geometries",
            "sewerage",
            "sewerage_type",
            "invert_level_start_point",
            "invert_level_end_point",
            "zoom_category",
            "ds1d_half",
        }

    def test_exporters(self):
        self.assertEqual(len(self.parser.lines._exporters), 1)
        self.assertIsInstance(self.parser.lines._exporters[0], LinesOgrExporter)

    def test_export_to_shape(self):
        self.parser.lines.to_shape(self.f)
        self.assertTrue(os.path.exists, self.f)
        s = ogr.Open(self.f)
        lyr = s.GetLayer()
        self.assertEqual(lyr.GetFeatureCount(), self.parser.lines.id.size - 1)


class GridAdminGridTest(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        self.grid = self.parser.grid

    def test_fields(self):
        assert set(self.grid._meta.get_fields().keys()) == {
            "id",
            "nodk",
            "nodm",
            "nodn",
            "ip",
            "jp",
        }

    def test_dx(self):
        expected = np.array([20.0, 40.0, 80.0, 160.0])
        np.testing.assert_almost_equal(self.grid.dx, expected)
        np.testing.assert_almost_equal(self.grid.filter(id=1).dx, expected)

    def test_n2dtot(self):
        expected = 5374
        self.assertEqual(self.grid.n2dtot, expected)
        self.assertEqual(self.grid.filter(id=1).n2dtot, expected)

    def test_transform(self):
        self.assertEqual(self.grid.transform, (0.5, 0.0, 106314.0, 0.0, 0.5, 514912.0))

    @unittest.skip("TODO")
    def test_get_pixel_map(self):
        self.parser.grid.get_pixel_map()


class GridAdminNodeTest(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f = os.path.join(d, "test_nodes.shp")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f))

    def test_fields(self):
        # Check fields
        assert set(self.parser.nodes._meta.get_fields(only_names=True)) == {
            "cell_coords",
            "content_pk",
            "coordinates",
            "id",
            "node_type",
            "calculation_type",
            "seq_id",
            "zoom_category",
            "is_manhole",
            "sumax",
            "drain_level",
            "storage_area",
            "dmax",
            "initial_waterlevel",
            "dimp",
        }

    def test_locations_2d(self):
        self.assertGreater(len(self.parser.nodes.locations_2d), 0)
        frst = self.parser.nodes.locations_2d[0]
        # should contain three elements
        self.assertEqual(len(frst), 3)

    def test_exporters(self):
        self.assertEqual(len(self.parser.nodes._exporters), 1)
        self.assertIsInstance(self.parser.nodes._exporters[0], NodesOgrExporter)

    def test_export_to_shape(self):
        self.parser.nodes.to_shape(self.f)
        self.assertTrue(os.path.exists, self.f)
        s = ogr.Open(self.f)
        lyr = s.GetLayer()
        self.assertEqual(lyr.GetFeatureCount(), self.parser.nodes.id.size - 1)


class GridAdminBreachTest(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f = os.path.join(d, "test_breaches.shp")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f))

    def test_fields(self):
        # Check fields
        assert set(self.parser.breaches._meta.get_fields().keys()) == {
            "content_pk",
            "coordinates",
            "id",
            "kcu",
            "levbr",
            "levl",
            "levmat",
            "line_geometries",
            "seq_ids",
            "code",
            "display_name",
        }

    def test_exporters(self):
        self.assertEqual(len(self.parser.breaches._exporters), 1)
        self.assertIsInstance(self.parser.breaches._exporters[0], BreachesOgrExporter)

    def test_export_to_shape(self):
        self.parser.breaches.to_shape(self.f)
        self.assertTrue(os.path.exists, self.f)
        s = ogr.Open(self.f)
        lyr = s.GetLayer()
        self.assertEqual(lyr.GetFeatureCount(), self.parser.breaches.id.size - 1)


class GridAdminCellsTest(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f = os.path.join(d, "test_cells.shp")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f))

    def test_fields(self):
        # should have also z_coordinate
        assert set(self.parser.cells._meta.get_fields().keys()) == {
            "cell_coords",
            "content_pk",
            "coordinates",
            "id",
            "calculation_type",
            "node_type",
            "seq_id",
            "z_coordinate",
            "zoom_category",
            "is_manhole",
            "sumax",
            "pixel_width",
            "pixel_coords",
            "drain_level",
            "storage_area",
            "dmax",
            "initial_waterlevel",
            "has_dem_averaged",
            "dimp",
        }

    def test_get_id_from_xy(self):
        # should yield tow ids, one for 2d, one for groundwater
        self.assertListEqual(self.parser.cells.get_id_from_xy(1.0, 2.0), [])
        # first coordinate pair + some offset
        x = self.parser.cells.coordinates[0][1] + 0.5
        y = self.parser.cells.coordinates[1][1] + 0.5
        self.assertListEqual(self.parser.cells.get_id_from_xy(x, y), [1, 5375])

    def test_get_id_from_xy_2d_open_water(self):
        self.assertListEqual(
            self.parser.cells.get_id_from_xy(1.0, 2.0, subset_name="2d_open_water"),
            [],
        )
        # first coordinate pair + some offset
        x = self.parser.cells.coordinates[0][1] + 0.5
        y = self.parser.cells.coordinates[1][1] + 0.5
        self.assertEqual(
            self.parser.cells.get_id_from_xy(x, y, subset_name="2d_open_water"),
            [1],
        )

    def test_get_id_from_xy_groundwater(self):
        self.assertListEqual(
            self.parser.cells.get_id_from_xy(1.0, 2.0, subset_name="groundwater_all"),
            [],
        )
        # first coordinate pair + some offset
        x = self.parser.cells.coordinates[0][1] + 0.5
        y = self.parser.cells.coordinates[1][1] + 0.5
        self.assertEqual(
            self.parser.cells.get_id_from_xy(x, y, subset_name="groundwater_all"),
            [5375],
        )

    def test_get_extent_pixels(self):
        cells = self.parser.cells
        assert cells.get_extent_pixels() == (0, 0, 9600, 9920)

    def test_iter_by_tile(self):
        cells = self.parser.cells.subset("2D_OPEN_WATER")
        w, h = 320 * 50, 1280
        tiles = list(cells.iter_by_tile(w, h))
        assert len(tiles) == 8  # ceil(9920/1280)
        total = 0
        for i, (bbox, cells) in enumerate(tiles):
            assert bbox == (0, i * h, w, (i + 1) * h)
            assert np.all(cells.pixel_coords[1] >= i * h)
            assert np.all(cells.pixel_coords[1] < (i + 1) * h)
            total += cells.count
        assert total == self.parser.cells.subset("2D_OPEN_WATER").count

    def test_iter_by_tile_subset_y(self):
        cells = self.parser.cells.subset("2D_OPEN_WATER").filter(
            pixel_coords__in_bbox=(0, 2000, 9600, 3000)
        )
        w, h = 320 * 50, 1280
        tiles = list(cells.iter_by_tile(w, h))
        assert len(tiles) == 2  # 1280 - 2560 and 2560 - 3840
        assert tiles[0][0] == (0, 1280, w, 1280 * 2)
        assert tiles[1][0] == (0, 1280 * 2, w, 1280 * 3)
        assert cells.count == (tiles[0][1].count + tiles[1][1].count)

    def test_iter_by_tile_subset_x(self):
        cells = self.parser.cells.subset("2D_OPEN_WATER").filter(
            pixel_coords__in_bbox=(2000, 0, 3000, 9920)
        )
        w, h = 1280, 320 * 50
        tiles = list(cells.iter_by_tile(w, h))
        assert len(tiles) == 2  # 1280 - 2560 and 2560 - 3840
        assert tiles[0][0] == (1280, 0, 1280 * 2, h)
        assert tiles[1][0] == (1280 * 2, 0, 1280 * 3, h)
        assert cells.count == (tiles[0][1].count + tiles[1][1].count)

    def test_iter_by_tile_should_match(self):
        cells = self.parser.cells.subset("2D_OPEN_WATER")
        for tile in ((321, 1280), (160, 1280), (500, 1280), (1280, 500)):
            with self.assertRaises(ValueError):
                list(cells.iter_by_tile(*tile))

    def test_exporters(self):
        self.assertEqual(len(self.parser.cells._exporters), 1)
        self.assertIsInstance(self.parser.cells._exporters[0], CellsOgrExporter)

    def test_export_to_shape(self):
        self.parser.cells.to_shape(self.f)
        self.assertTrue(os.path.exists, self.f)


class GridAdminCrossSectionsTest(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f = os.path.join(d, "test_cross_sections.shp")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f))

    def test_fields(self):
        # Check dtype names
        assert set(self.parser.cross_sections._meta.get_fields().keys()) == {
            "id",
            "code",
            "shape",
            "content_pk",
            "width_1d",
            "offset",
            "count",
            "tables",
        }


class NodeFilterTests(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)

    def test_nodes_filter_id_eq(self):
        filtered = self.parser.nodes.filter(id=3).data["coordinates"]
        (trues,) = np.where(self.parser.nodes.data["id"] == 3)
        expected = self.parser.nodes.data["coordinates"][:, trues]
        np.testing.assert_equal(filtered, expected)

    def test_nodes_filter_id_ne(self):
        filtered = self.parser.nodes.filter(id__ne=3).data["coordinates"]
        (trues,) = np.where(self.parser.nodes.data["id"] != 3)
        expected = self.parser.nodes.data["coordinates"][:, trues]
        np.testing.assert_equal(filtered, expected)

    def test_nodes_filter_id_gt(self):
        filtered = self.parser.nodes.filter(id__gt=3).data["coordinates"]
        (trues,) = np.where(self.parser.nodes.data["id"] > 3)
        expected = self.parser.nodes.data["coordinates"][:, trues]
        np.testing.assert_equal(filtered, expected)

    def test_nodes_filter_id_gte(self):
        filtered = self.parser.nodes.filter(id__gte=3).data["coordinates"]
        (trues,) = np.where(self.parser.nodes.data["id"] >= 3)
        expected = self.parser.nodes.data["coordinates"][:, trues]
        np.testing.assert_equal(filtered, expected)

    def test_nodes_filter_id_lt(self):
        filtered = self.parser.nodes.filter(id__lt=3).data["coordinates"]
        (trues,) = np.where(self.parser.nodes.data["id"] < 3)
        expected = self.parser.nodes.data["coordinates"][:, trues]
        np.testing.assert_equal(filtered, expected)

    def test_nodes_filter_id_lte(self):
        filtered = self.parser.nodes.filter(id__lte=3).data["coordinates"]
        (trues,) = np.where(self.parser.nodes.data["id"] <= 3)
        expected = self.parser.nodes.data["coordinates"][:, trues]
        np.testing.assert_equal(filtered, expected)

    def test_nodes_filter_id_in(self):
        """Verify that 'in' filter returns the correct data."""
        filtered = self.parser.nodes.filter(id__in=list(range(3, 7))).data[
            "coordinates"
        ]
        (trues,) = np.where(
            (self.parser.nodes.data["id"] >= 3) & (self.parser.nodes.data["id"] < 7)
        )
        expected = self.parser.nodes.data["coordinates"][:, trues]
        np.testing.assert_equal(filtered, expected)

    # TODO: fix this
    @unittest.skip(
        "This test should succeed, but in our code the reprojected tile "
        "bounds go out of bounds, which causes errors. TODO: fix this."
    )
    def test_nodes_filter_id_in_tile(self):
        # at z=0 we have a single base tile
        filtered = self.parser.nodes.filter(coordinates__in_tile=[0, 0, 0]).data["id"]
        expected = self.parser.nodes.data["id"]
        self.assertTrue(len(filtered) != 0)
        np.testing.assert_equal(filtered, expected)

    # some special cases

    def test_nodes_filter_id_eq_chained(self):
        """Eq filter can be chained."""
        filtered = self.parser.nodes.filter(id=3).filter(id=3).data["coordinates"]
        (trues,) = np.where(self.parser.nodes.data["id"] == 3)
        expected = self.parser.nodes.data["coordinates"][:, trues]
        np.testing.assert_equal(filtered, expected)

    def test_nodes_chained_same_filter_id_in(self):
        """In filters can be chained."""
        filtered = (
            self.parser.nodes.filter(id__in=list(range(1, 10)))
            .filter(id__in=list(range(1, 10)))
            .filter(id__in=list(range(1, 10)))
            .data["coordinates"]
        )
        expected = self.parser.nodes.filter(id__in=list(range(1, 10))).data[
            "coordinates"
        ]
        np.testing.assert_equal(filtered, expected)

    def test_nodes_chained_filter_id_in(self):
        filtered = (
            self.parser.nodes.filter(id__in=list(range(1, 8)))
            .filter(id__in=list(range(3, 7)))
            .data["coordinates"]
        )
        expected = self.parser.nodes.filter(id__in=list(range(3, 7))).data[
            "coordinates"
        ]
        np.testing.assert_equal(filtered, expected)

    def test_nodes_chained_filter_id_in_2(self):
        filtered = (
            self.parser.nodes.filter(id__in=list(range(1, 10)))
            .filter(id__in=list(range(5, 20)))
            .data["coordinates"]
        )
        expected = self.parser.nodes.filter(id__in=list(range(5, 10))).data[
            "coordinates"
        ]
        np.testing.assert_equal(filtered, expected)

    def test_manhole_filter(self):
        non_manholes1 = self.parser.nodes.filter(is_manhole=False).count
        non_manholes2 = self.parser.nodes.filter(is_manhole=0).count
        non_manholes3 = self.parser.nodes.filter(is_manhole__eq=0).count
        non_manholes4 = self.parser.nodes.filter(is_manhole__eq=False).count
        non_manholes5 = self.parser.nodes.filter(is_manhole__ne=1).count
        non_manholes6 = self.parser.nodes.filter(is_manhole__ne=True).count
        self.assertEqual(non_manholes1, non_manholes2)
        self.assertEqual(non_manholes2, non_manholes3)
        self.assertEqual(non_manholes3, non_manholes4)
        self.assertEqual(non_manholes4, non_manholes5)
        self.assertEqual(non_manholes5, non_manholes6)

        manholes1 = self.parser.nodes.filter(is_manhole=True).count
        manholes2 = self.parser.nodes.filter(is_manhole=1).count
        manholes3 = self.parser.nodes.filter(is_manhole__eq=1).count
        manholes4 = self.parser.nodes.filter(is_manhole__eq=True).count
        manholes5 = self.parser.nodes.filter(is_manhole__ne=0).count
        manholes6 = self.parser.nodes.filter(is_manhole__ne=False).count
        self.assertEqual(manholes1, manholes2)
        self.assertEqual(manholes2, manholes3)
        self.assertEqual(manholes3, manholes4)
        self.assertEqual(manholes4, manholes5)
        self.assertEqual(manholes5, manholes6)

        self.assertEqual(manholes1 + non_manholes2, self.parser.nodes.count)

    def test_node_filter_keeps_has_1d(self):
        """Property has_1d doesn't disappear"""
        self.assertEqual(
            self.parser.nodes.has_1d, self.parser.nodes.filter(id=1).has_1d
        )


class LineFilterTests(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)

    def test_lines_filter_id_eq(self):
        # from nose.tools import set_trace; set_trace()
        filtered = self.parser.lines.filter(id=3).data["line_coords"]
        (trues,) = np.where(self.parser.lines.data["id"] == 3)
        expected = self.parser.lines.data["line_coords"][:, trues]
        np.testing.assert_equal(filtered, expected)

    def test_lines_filter_id_in(self):
        filtered = self.parser.lines.filter(id__in=list(range(3, 7))).data[
            "line_coords"
        ]
        (trues,) = np.where(
            (self.parser.lines.data["id"] >= 3) & (self.parser.lines.data["id"] < 7)
        )
        expected = self.parser.lines.data["line_coords"][:, trues]
        np.testing.assert_equal(filtered, expected)
