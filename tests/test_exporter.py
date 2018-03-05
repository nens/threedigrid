from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import unittest
import tempfile
import shutil

import ogr

from threedigrid.admin.gridadmin import GridH5Admin

from threedigrid.admin.lines.exporters import LinesOgrExporter


test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
grid_admin_h5_file = os.path.join(test_file_dir, "gridadmin.h5")


class ExporterTestShp(unittest.TestCase):

    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f_shp = os.path.join(d, "exporter_test_lines.shp")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f_shp))

    def test_export_by_extension(self):
        line_2d_open_water_wgs84 = self.parser.lines.subset(
            '2D_OPEN_WATER').reproject_to('4326')
        exporter = LinesOgrExporter(line_2d_open_water_wgs84)
        exporter.save(self.f_shp, line_2d_open_water_wgs84.data, '4326')
        self.assertTrue(os.path.exists(self.f_shp))
        s = ogr.Open(self.f_shp)
        layer = s.GetLayer()
        self.assertEqual(
            layer.GetFeatureCount(), line_2d_open_water_wgs84.id.size)


class ExporterTestGpkg(unittest.TestCase):

    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f_gpkg = os.path.join(d, "exporter_test_lines.gpkg")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f_gpkg))

    def test_export_by_extension(self):
        line_2d_open_water_wgs84 = self.parser.lines.subset(
            '2D_OPEN_WATER').reproject_to('4326')
        exporter = LinesOgrExporter(line_2d_open_water_wgs84)
        exporter.save(self.f_gpkg, line_2d_open_water_wgs84.data, '4326')
        self.assertTrue(os.path.exists(self.f_gpkg))
        s = ogr.Open(self.f_gpkg)
        layer = s.GetLayer()
        self.assertEqual(
            layer.GetFeatureCount(), line_2d_open_water_wgs84.id.size)
