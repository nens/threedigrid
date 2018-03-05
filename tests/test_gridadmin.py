from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import unittest
import tempfile
import shutil

import numpy as np
import ogr

from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.nodes.exporters import CellsOgrExporter
from threedigrid.admin.nodes.exporters import NodesOgrExporter
from threedigrid.admin.lines.exporters import LinesOgrExporter
from threedigrid.admin.breaches.exporters import BreachesOgrExporter
from threedigrid.admin.constants import SUBSET_1D_ALL
from threedigrid.admin.constants import SUBSET_2D_OPEN_WATER
from threedigrid.admin.constants import NO_DATA_VALUE
from threedigrid.admin.lines.serializers import ChannelsGeoJsonSerializer

test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
grid_admin_h5_file = os.path.join(test_file_dir, "gridadmin.h5")


class GridAdminTest(unittest.TestCase):

    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)

    def test_get_from_meta(self):
        self.assertIsNotNone(self.parser.get_from_meta('n2dtot'))
        self.assertIsNone(self.parser.get_from_meta('doesnotexist'))

    def test_get_extent_subset_onedee(self):
        extent_1D = self.parser.get_extent_subset(
            subset_name=SUBSET_1D_ALL)
        # should contain values
        self.assertTrue(np.any(extent_1D != NO_DATA_VALUE))

    def test_get_extent_subset_reproject(self):
        extent_1D = self.parser.get_extent_subset(
            subset_name=SUBSET_1D_ALL)
        extent_1D_proj = self.parser.get_extent_subset(
            subset_name=SUBSET_1D_ALL, target_epsg_code='4326')
        self.assertTrue(np.all(extent_1D != extent_1D_proj))

    def test_get_extent_subset_twodee(self):
        extent_2D = self.parser.get_extent_subset(
        subset_name=SUBSET_2D_OPEN_WATER)
        # should contain values
        self.assertTrue(np.any(extent_2D != NO_DATA_VALUE))

    def test_get_extent_subset_combi(self):
        extent_1D = self.parser.get_extent_subset(
            subset_name=SUBSET_1D_ALL)
        extent_2D = self.parser.get_extent_subset(
        subset_name=SUBSET_2D_OPEN_WATER)
        # should be different
        self.assertTrue(
            np.any(np.not_equal(extent_1D, extent_2D))
        )

    def test_get_model_extent(self):
        model_extent = self.parser.get_model_extent()
        np.testing.assert_almost_equal(
            model_extent,
            np.array([
                [105427.6, 105427.6],
                [523463.32684827, 523463.32684827]
            ])
        )

    def test_get_model_extent_extra_extent(self):
        onedee_extra = np.array([
            100000.0, 90000.0, 550000.0, 580000.0]
        )

        extra_extent = {'extra_extent': [onedee_extra]}
        model_extent = self.parser.get_model_extent(**extra_extent)
        np.testing.assert_equal(
            model_extent,
            np.array([[ 90000.,  90000.],
                      [580000., 580000.]
            ])
        )

    def test_get_model_extent_extra_extent2(self):
        onedee_extra = np.array([
            106666.6, 106666.6, 550000.0, 580000.0]
        )

        extra_extent = {'extra_extent': [onedee_extra]}
        model_extent = self.parser.get_model_extent(**extra_extent)
        np.testing.assert_almost_equal(
            model_extent,
            np.array([[105427.6, 105427.6],
                      [580000., 580000.]
            ])
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


class GridAdminLinesTest(unittest.TestCase):

    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f = os.path.join(d, "test_lines.shp")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f))

    def test_fields(self):
        # Check dtype names
        self.assertEqual(self.parser.lines.fields, [
            'content_pk', 'content_type', 'id', 'kcu',
            'lik', 'line', 'line_coords', 'line_geometries',
            'zoom_category'
        ])

    def test_exporters(self):
        self.assertEqual(len(self.parser.lines._exporters), 1)
        self.assertIsInstance(
            self.parser.lines._exporters[0],
            LinesOgrExporter
        )

    def test_export_to_shape(self):
        self.parser.lines.to_shape(self.f)
        self.assertTrue(os.path.exists, self.f)
        s = ogr.Open(self.f)
        l = s.GetLayer()
        self.assertEqual(l.GetFeatureCount(), self.parser.lines.id.size)


class GridAdminGridTest(unittest.TestCase):

    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)

    def test_fields(self):
        self.assertEqual(
            self.parser.grid.fields,
            ['id', 'nodk', 'nodm', 'nodn']
        )

    @unittest.skip('TODO')
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
        self.assertEqual(
            self.parser.nodes.fields,
            ['cell_coords', 'content_pk', 'coordinates', 'id', 'node_type',
             'seq_id', 'zoom_category'])

    def test_locations_2d(self):
        self.assertGreater(len(self.parser.nodes.locations_2d), 0)
        frst = self.parser.nodes.locations_2d[0]
        # should contain three elements
        self.assertEqual(len(frst), 3)

    def test_exporters(self):
        self.assertEqual(len(self.parser.nodes._exporters), 1)
        self.assertIsInstance(
            self.parser.nodes._exporters[0],
            NodesOgrExporter
        )

    def test_export_to_shape(self):
        self.parser.nodes.to_shape(self.f)
        self.assertTrue(os.path.exists, self.f)
        s = ogr.Open(self.f)
        l = s.GetLayer()
        self.assertEqual(l.GetFeatureCount(), self.parser.nodes.id.size)


class GridAdminBreachTest(unittest.TestCase):

    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f = os.path.join(d, "test_breaches.shp")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f))

    def test_fields(self):
        # Check fields
        self.assertEqual(
            self.parser.breaches.fields,
            ['content_pk', 'coordinates', 'id', 'kcu',
             'levbr', 'levl', 'levmat', 'seq_ids']
        )

    def test_exporters(self):
        self.assertEqual(len(self.parser.breaches._exporters), 1)
        self.assertIsInstance(
            self.parser.breaches._exporters[0],
            BreachesOgrExporter
        )

    def test_export_to_shape(self):
        self.parser.breaches.to_shape(self.f)
        self.assertTrue(os.path.exists, self.f)
        s = ogr.Open(self.f)
        l = s.GetLayer()
        self.assertEqual(l.GetFeatureCount(), self.parser.breaches.id.size)


class GridAdminCellsTest(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f = os.path.join(d, "test_cells.shp")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f))

    def test_fields(self):
        # should have also z_coordinate
        self.assertEqual(
            self.parser.cells.fields,
            ['cell_coords', 'content_pk', 'coordinates', 'id', 'node_type',
             'seq_id', 'z_coordinate', 'zoom_category']
        )

    def test_get_id_from_xy(self):

        self.assertIsNone(self.parser.cells.get_id_from_xy(1.,2.))
        # first coordinate pair + some offset
        x = self.parser.cells.coordinates[0][1] + 0.5
        y = self.parser.cells.coordinates[1][1] + 0.5
        self.assertEqual(self.parser.cells.get_id_from_xy(x,y), 1)

    def test_exporters(self):
        self.assertEqual(len(self.parser.cells._exporters), 1)
        self.assertIsInstance(
            self.parser.cells._exporters[0],
            CellsOgrExporter
        )

    def test_export_to_shape(self):
        self.parser.cells.to_shape(self.f)
        self.assertTrue(os.path.exists, self.f)


class NodeFilterTests(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)

    def test_nodes_filter_id_eq(self):
        filtered = self.parser.nodes.filter(id=3).data['coordinates']
        trues, = np.where(self.parser.nodes.data['id'] == 3)
        expected = self.parser.nodes.data['coordinates'][:, trues]
        self.assertTrue((filtered == expected).all())

    def test_nodes_filter_id_ne(self):
        filtered = self.parser.nodes.filter(id__ne=3).data['coordinates']
        trues, = np.where(self.parser.nodes.data['id'] != 3)
        expected = self.parser.nodes.data['coordinates'][:, trues]
        self.assertTrue((filtered == expected).all())

    def test_nodes_filter_id_gt(self):
        filtered = self.parser.nodes.filter(id__gt=3).data['coordinates']
        trues, = np.where(self.parser.nodes.data['id'] > 3)
        expected = self.parser.nodes.data['coordinates'][:, trues]
        self.assertTrue((filtered == expected).all())

    def test_nodes_filter_id_gte(self):
        filtered = self.parser.nodes.filter(id__gte=3).data['coordinates']
        trues, = np.where(self.parser.nodes.data['id'] >= 3)
        expected = self.parser.nodes.data['coordinates'][:, trues]
        self.assertTrue((filtered == expected).all())

    def test_nodes_filter_id_lt(self):
        filtered = self.parser.nodes.filter(id__lt=3).data['coordinates']
        trues, = np.where(self.parser.nodes.data['id'] < 3)
        expected = self.parser.nodes.data['coordinates'][:, trues]
        self.assertTrue((filtered == expected).all())

    def test_nodes_filter_id_lte(self):
        filtered = self.parser.nodes.filter(id__lte=3).data['coordinates']
        trues, = np.where(self.parser.nodes.data['id'] <= 3)
        expected = self.parser.nodes.data['coordinates'][:, trues]
        self.assertTrue((filtered == expected).all())

    def test_nodes_filter_id_in(self):
        """Verify that 'in' filter returns the correct data."""
        filtered = self.parser.nodes.filter(
            id__in=range(3, 7)).data['coordinates']
        trues, = np.where(
            (self.parser.nodes.data['id'] >= 3) &
            (self.parser.nodes.data['id'] < 7))
        expected = self.parser.nodes.data['coordinates'][:, trues]
        self.assertTrue((filtered == expected).all())

    # TODO: fix this
    @unittest.skip(
        "This test should succeed, but in our code the reprojected tile "
        "bounds go out of bounds, which causes errors. TODO: fix this."
    )
    def test_nodes_filter_id_in_tile(self):
        # at z=0 we have a single base tile
        filtered = self.parser.nodes.filter(
            coordinates__in_tile=[0, 0, 0]).data['id']
        expected = self.parser.nodes.data['id']
        self.assertTrue(len(filtered) != 0)
        self.assertTrue((filtered == expected).all())

    # some special cases

    def test_nodes_filter_id_eq_chained(self):
        """Eq filter can be chained."""
        filtered = self.parser.nodes\
            .filter(id=3)\
            .filter(id=3)\
            .data['coordinates']
        trues, = np.where(self.parser.nodes.data['id'] == 3)
        expected = self.parser.nodes.data['coordinates'][:, trues]
        self.assertTrue((filtered == expected).all())

    def test_nodes_chained_same_filter_id_in(self):
        """In filters can be chained."""
        filtered = self.parser.nodes\
            .filter(id__in=range(1, 10))\
            .filter(id__in=range(1, 10))\
            .filter(id__in=range(1, 10))\
            .data['coordinates']
        expected = self.parser.nodes\
            .filter(id__in=range(1, 10))\
            .data['coordinates']
        self.assertTrue((filtered == expected).all())

    def test_nodes_chained_filter_id_in(self):
        filtered = self.parser.nodes\
            .filter(id__in=range(1, 8))\
            .filter(id__in=range(3, 7))\
            .data['coordinates']
        expected = self.parser.nodes\
            .filter(id__in=range(3, 7))\
            .data['coordinates']
        self.assertTrue((filtered == expected).all())

    def test_nodes_chained_filter_id_in_2(self):
        filtered = self.parser.nodes\
            .filter(id__in=range(1, 10))\
            .filter(id__in=range(5, 20))\
            .data['coordinates']
        expected = self.parser.nodes\
            .filter(id__in=range(5, 10))\
            .data['coordinates']
        self.assertTrue((filtered == expected).all())


class LineFilterTests(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)

    def test_lines_filter_id_eq(self):
        # from nose.tools import set_trace; set_trace()
        filtered = self.parser.lines.filter(id=3).data['line_coords']
        trues, = np.where(self.parser.lines.data['id'] == 3)
        expected = self.parser.lines.data['line_coords'][:, trues]
        self.assertTrue((filtered == expected).all())

    def test_lines_filter_id_in(self):
        filtered = self.parser.lines.filter(
            id__in=range(3, 7)).data['line_coords']
        trues, = np.where(
            (self.parser.lines.data['id'] >= 3) &
            (self.parser.lines.data['id'] < 7)
        )
        expected = self.parser.lines.data['line_coords'][:, trues]
        self.assertTrue((filtered == expected).all())
