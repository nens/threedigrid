from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import os
import unittest
import tempfile
import shutil

from osgeo import ogr

from threedigrid.admin import constants
from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.prepare import GridAdminH5Export

from threedigrid.admin.lines.exporters import LinesOgrExporter


test_file_dir = os.path.join(os.getcwd(), "tests/test_files")

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
            "2D_OPEN_WATER"
        ).reproject_to("4326")
        exporter = LinesOgrExporter(line_2d_open_water_wgs84)
        exporter.save(self.f_shp, line_2d_open_water_wgs84.data, "4326")
        self.assertTrue(os.path.exists(self.f_shp))
        s = ogr.Open(self.f_shp)
        layer = s.GetLayer()
        self.assertEqual(
            layer.GetFeatureCount(), line_2d_open_water_wgs84.id.size
        )


class ExporterTestGpkg(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f_gpkg = os.path.join(d, "exporter_test_lines.gpkg")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f_gpkg))

    def test_export_by_extension(self):
        line_2d_open_water_wgs84 = self.parser.lines.subset(
            "2D_OPEN_WATER"
        ).reproject_to("4326")
        exporter = LinesOgrExporter(line_2d_open_water_wgs84)
        exporter.save(self.f_gpkg, line_2d_open_water_wgs84.data, "4326")
        self.assertTrue(os.path.exists(self.f_gpkg))
        s = ogr.Open(self.f_gpkg)
        layer = s.GetLayer()
        self.assertEqual(
            layer.GetFeatureCount(), line_2d_open_water_wgs84.id.size
        )


class ExporterTestGeojson(unittest.TestCase):
    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)
        d = tempfile.mkdtemp()
        self.f_geojson = os.path.join(d, "exporter_test_lines.json")

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.f_geojson))

    def test_export_by_extension(self):
        # .json extension automatically uses geojson exporter
        line_2d_open_water_wgs84 = self.parser.lines.subset(
            "2D_OPEN_WATER"
        ).reproject_to("4326")
        exporter = LinesOgrExporter(line_2d_open_water_wgs84)
        exporter.save(self.f_geojson, line_2d_open_water_wgs84.data, "4326")
        self.assertTrue(os.path.exists(self.f_geojson))
        s = ogr.Open(self.f_geojson)
        layer = s.GetLayer()
        self.assertEqual(
            layer.GetFeatureCount(), line_2d_open_water_wgs84.id.size
        )

    def test_export_specify_fields_as_dict(self):
        self.parser.lines.pipes.filter(id=27449).to_geojson(
            self.f_geojson,
            use_ogr=False,
            fields={'display_name': 'str', 'calculation_type': 'str'}
        )
        with open(self.f_geojson) as file:
            data = json.load(file)
            self.assertEqual(len(data['features'][0]['properties']), 3)
            self.assertTrue(
                'display_name' in data['features'][0]['properties']
            )
            self.assertTrue(
                'calculation_type' in data['features'][0]['properties']
            )
            self.assertTrue(
                'model_type' in data['features'][0]['properties']
            )

    def test_export_specify_fields_as_list(self):
        self.parser.lines.pipes.filter(id=27449).to_geojson(
            self.f_geojson,
            use_ogr=False,
            fields=['display_name', 'calculation_type']
        )
        with open(self.f_geojson) as file:
            data = json.load(file)
            self.assertEqual(len(data['features'][0]['properties']), 3)
            self.assertTrue(
                'display_name' in data['features'][0]['properties']
            )
            self.assertTrue(
                'calculation_type' in data['features'][0]['properties']
            )
            self.assertTrue(
                'model_type' in data['features'][0]['properties']
            )

    def test_export_specify_nested_fields(self):
        self.parser.lines.pipes.filter(id=27449).to_geojson(
            self.f_geojson,
            use_ogr=False,
            fields=[
                {
                    'first': [
                        'display_name',
                        {'second': ['calculation_type']}
                    ]
                }
            ]
        )
        with open(self.f_geojson) as file:
            data = json.load(file)
            self.assertEqual(len(data['features'][0]['properties']), 2)
            self.assertTrue(
                'first' in data['features'][0]['properties']
            )
            self.assertTrue(
                'model_type' in data['features'][0]['properties']
            )
            self.assertTrue(
                'display_name' in data['features'][0]['properties']['first']
            )
            self.assertTrue(
                'calculation_type' in
                data['features'][0]['properties']['first']['second']
            )

    def test_export_filter(self):
        self.parser.lines.pipes.filter(id=27449).to_geojson(
            self.f_geojson, use_ogr=False
        )
        with open(self.f_geojson) as file:
            data = json.load(file)
            self.assertEqual(len(data['features']), 1)

    def test_export_reproject(self):
        self.parser.lines.reproject_to("4326").to_geojson(
            self.f_geojson, use_ogr=False
        )
        with open(self.f_geojson) as file:
            data = json.load(file)
            p1, _ = data['features'][1]['geometry']['coordinates']
            x, y = p1
            # Should be somewhere in the Netherlands
            self.assertTrue(4.185791 < x < 5.663452)
            self.assertTrue(52.109879 < y < 52.912215)


class GridadminH5ExportTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.exporter = GridAdminH5Export(grid_admin_h5_file)
        self.exporter._dest = self.d

    def tearDown(self):
        shutil.rmtree(self.d)

    def test_export_2d_groundwater(self):
        self.exporter.export_2d_groundwater_lines()
        result = os.path.join(
            self.d, constants.GROUNDWATER_LINES + self.exporter._extension
        )
        self.assertTrue(os.path.exists(result))

    def test_export_2d_openwater_lines(self):
        self.exporter.export_2d_openwater_lines()
        result = os.path.join(
            self.d, constants.OPEN_WATER_LINES + self.exporter._extension
        )
        self.assertTrue(os.path.exists(result))

    def test_export_2d_vertical_infiltration_lines(self):
        self.exporter.export_2d_vertical_infiltration_lines()
        result = os.path.join(
            self.d,
            constants.VERTICAL_INFILTRATION_LINES + self.exporter._extension
        )
        self.assertTrue(os.path.exists(result))

    def test_export_levees(self):
        self.exporter.export_levees()
        result = os.path.join(
            self.d, constants.LEVEES + self.exporter._extension
        )
        self.assertTrue(os.path.exists(result))
