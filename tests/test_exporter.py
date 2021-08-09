from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import os
import pytest

from osgeo import ogr

from threedigrid.admin import constants

from threedigrid.admin.lines.exporters import LinesOgrExporter


test_file_dir = os.path.join(os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
grid_admin_h5_file = os.path.join(test_file_dir, "gridadmin.h5")


@pytest.mark.parametrize("extension", [".shp", ".gpkg", ".json"])
def test_export_by_extension(ga, tmp_path, extension):
    path = str(tmp_path / ("exporter_test_lines" + extension))
    line_2d_open_water_wgs84 = ga.lines.subset(
        "2D_OPEN_WATER"
    ).reproject_to("4326")
    exporter = LinesOgrExporter(line_2d_open_water_wgs84)
    exporter.save(path, line_2d_open_water_wgs84.data, "4326")
    assert os.path.exists(path)
    s = ogr.Open(path)
    layer = s.GetLayer()
    assert layer.GetFeatureCount() == line_2d_open_water_wgs84.id.size


def test_export_specify_fields_as_dict(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")

    ga.lines.pipes.filter(content_pk=17).to_geojson(
        path,
        use_ogr=False,
        fields={'display_name': 'str', 'calculation_type': 'str'}
    )
    with open(path) as file:
        data = json.load(file)
        assert len(data['features'][0]['properties']) == 3
        assert 'display_name' in data['features'][0]['properties']
        assert 'calculation_type' in data['features'][0]['properties']
        assert 'model_type' in data['features'][0]['properties']


def test_export_specify_fields_as_list(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")
    ga.lines.pipes.filter(content_pk=17).to_geojson(
        path,
        use_ogr=False,
        fields=['display_name', 'calculation_type']
    )
    with open(path) as file:
        data = json.load(file)
        assert len(data['features'][0]['properties']) == 3
        assert 'display_name' in data['features'][0]['properties']
        assert 'calculation_type' in data['features'][0]['properties']
        assert 'model_type' in data['features'][0]['properties']


def test_export_specify_nested_fields(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")
    ga.lines.pipes.filter(content_pk=17).to_geojson(
        path,
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
    with open(path) as file:
        data = json.load(file)
        assert len(data['features'][0]['properties']) == 2
        assert 'first' in data['features'][0]['properties']
        assert 'model_type' in data['features'][0]['properties']
        assert 'display_name' in data['features'][0]['properties']['first']
        assert 'calculation_type' in data['features'][0]['properties']['first']['second']


def test_export_filter(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")
    ga.lines.pipes.filter(content_pk=17).to_geojson(
        path, use_ogr=False
    )
    with open(path) as file:
        data = json.load(file)
        assert len(data['features']) == 1


def test_export_reproject(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")
    ga.lines.reproject_to("4326").to_geojson(
        path, use_ogr=False
    )
    with open(path) as file:
        data = json.load(file)
        p1, _ = data['features'][1]['geometry']['coordinates']
        x, y = p1
        # Should be somewhere in the Netherlands
        assert 4.18 < x < 5.66
        assert 52.10 < y < 52.92


def test_export_2d_groundwater(ga_export):
    ga_export.export_2d_groundwater_lines()
    result = os.path.join(
        ga_export._dest, constants.GROUNDWATER_LINES + ga_export._extension
    )
    assert os.path.exists(result)


def test_export_2d_openwater_lines(ga_export):
    ga_export.export_2d_openwater_lines()
    result = os.path.join(
        ga_export._dest, constants.OPEN_WATER_LINES + ga_export._extension
    )
    assert os.path.exists(result)


def test_export_2d_vertical_infiltration_lines(ga_export):
    ga_export.export_2d_vertical_infiltration_lines()
    result = os.path.join(
        ga_export._dest,
        constants.VERTICAL_INFILTRATION_LINES + ga_export._extension
    )
    assert os.path.exists(result)

def test_export_levees(ga_export):
    if ga_export.ga.grid_file.endswith("gridadmin_v2.h5"):
        pytest.skip("No levees yet in new gridadmin")
    ga_export.export_levees()
    result = os.path.join(
        ga_export._dest, constants.LEVEES + ga_export._extension
    )
    assert os.path.exists(result)
