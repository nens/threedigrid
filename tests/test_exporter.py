import json
import os
from pathlib import Path

import pytest
from osgeo import ogr

from threedigrid.admin.exporters.geopackage import GeopackageExporter
from threedigrid.admin.exporters.geopackage.exporter import GpkgExporter
from threedigrid.admin.fragments.exporters import FragmentsOgrExporter
from threedigrid.admin.lines.exporters import LinesOgrExporter

test_file_dir = os.path.join(os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
grid_admin_h5_file = os.path.join(test_file_dir, "gridadmin.h5")


@pytest.mark.parametrize("extension", [".shp", ".json"])
def test_export_by_extension(ga, tmp_path, extension):
    path = str(tmp_path / ("exporter_test_lines" + extension))
    line_2d_open_water_wgs84 = ga.lines.subset("2D_OPEN_WATER").reproject_to("4326")
    exporter = LinesOgrExporter(line_2d_open_water_wgs84)
    exporter.save(path, line_2d_open_water_wgs84.data, "4326")
    assert os.path.exists(path)
    s = ogr.Open(path)
    layer = s.GetLayer()
    assert layer.GetFeatureCount() == line_2d_open_water_wgs84.id.size


def test_nodes_gpgk_export(ga, tmp_path):
    path = str(tmp_path / ("exporter_test_lines.gpkg"))
    nodes_2d_open_water = ga.nodes.subset("2D_OPEN_WATER")
    exporter = GpkgExporter(nodes_2d_open_water)
    exporter.save(path, "nodes", ga.nodes.GPKG_DEFAULT_FIELD_MAP)
    assert os.path.exists(path)
    s = ogr.Open(path)
    layer = s.GetLayer("nodes")
    assert layer.GetFeatureCount() == nodes_2d_open_water.id.size


def test_fragments_gpgk_export(ga_fragments, tmp_path):
    path = str(tmp_path / ("exporter_test_fragments.gpkg"))
    exporter = FragmentsOgrExporter(ga_fragments.fragments)
    exporter.save(path, "fragments", "4326")
    assert os.path.exists(path)
    s = ogr.Open(path)
    layer = s.GetLayer()
    assert layer.GetFeatureCount() == (
        ga_fragments.fragments.id.size - 1
    )  # minus dummy


def test_fragments_to_gpgk_export(ga_fragments, tmp_path):
    path = str(tmp_path / "only_fragment_export.gpkg")
    ga_fragments.fragments.to_gpkg(path, "fragments")
    s = ogr.Open(path)
    layer = s.GetLayer("fragments")
    assert layer.GetFeatureCount() == (
        ga_fragments.fragments.id.size - 1
    )  # minus dummy


def test_fragments_to_geojson_export(ga_fragments, tmp_path):
    path = str(tmp_path / "only_fragment_export.json")
    ga_fragments.fragments.to_geojson(path, use_ogr=True)
    s = ogr.Open(path)
    layer = s.GetLayer(Path(path).name)
    assert layer.GetFeatureCount() == (
        ga_fragments.fragments.id.size - 1
    )  # minus dummy
    with open(path) as file:
        data = json.load(file)
        assert len(data["features"][0]["properties"]) == 2
        assert "node_id" in data["features"][0]["properties"]

    path = str(tmp_path / "only_fragment_export_2.json")
    ga_fragments.fragments.to_geojson(path, use_ogr=False)
    s = ogr.Open(path)
    layer = s.GetLayer(Path(path).stem)
    # We export more properties and use different layer name
    assert layer.GetFeatureCount() == (
        ga_fragments.fragments.id.size - 1
    )  # minus dummy
    with open(path) as file:
        data = json.load(file)
        assert len(data["features"][0]["properties"]) == 3
        assert "node_id" in data["features"][0]["properties"]
        assert "model_type" in data["features"][0]["properties"]


def test_fragments_gpkg_conversion(ga_fragments, ga_fragment_path, tmp_path):
    exporter = GeopackageExporter(
        ga_fragment_path, str(tmp_path / "fragment_export.gpkg")
    )
    exporter.export()
    s = ogr.Open(str(tmp_path / "fragment_export.gpkg"))
    layer = s.GetLayer("fragment")
    assert layer.GetFeatureCount() == (
        ga_fragments.fragments.id.size - 1
    )  # minus dummy


def test_meta_data_gpgk_export(ga, tmp_path):
    path = str(tmp_path / ("exporter_meta.gpkg"))
    exporter = GpkgExporter(ga)
    exporter.add_meta_data(path, "meta")
    assert os.path.exists(path)
    s = ogr.Open(path)
    layer = s.GetLayer("meta")
    assert layer.GetFeatureCount() == 1


def test_export_specify_fields_as_dict(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")

    ga.lines.pipes.filter(content_pk=17).to_geojson(
        path, use_ogr=False, fields={"display_name": "str", "calculation_type": "str"}
    )
    with open(path) as file:
        data = json.load(file)
        assert len(data["features"][0]["properties"]) == 3
        assert "display_name" in data["features"][0]["properties"]
        assert "calculation_type" in data["features"][0]["properties"]
        assert "model_type" in data["features"][0]["properties"]


def test_export_specify_fields_as_list(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")
    ga.lines.pipes.filter(content_pk=17).to_geojson(
        path, use_ogr=False, fields=["display_name", "calculation_type"]
    )
    with open(path) as file:
        data = json.load(file)
        assert len(data["features"][0]["properties"]) == 3
        assert "display_name" in data["features"][0]["properties"]
        assert "calculation_type" in data["features"][0]["properties"]
        assert "model_type" in data["features"][0]["properties"]


def test_export_specify_nested_fields(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")
    ga.lines.pipes.filter(content_pk=17).to_geojson(
        path,
        use_ogr=False,
        fields=[{"first": ["display_name", {"second": ["calculation_type"]}]}],
    )
    with open(path) as file:
        data = json.load(file)
        assert len(data["features"][0]["properties"]) == 2
        assert "first" in data["features"][0]["properties"]
        assert "model_type" in data["features"][0]["properties"]
        assert "display_name" in data["features"][0]["properties"]["first"]
        assert (
            "calculation_type" in data["features"][0]["properties"]["first"]["second"]
        )


def test_export_filter(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")
    ga.lines.pipes.filter(content_pk=17).to_geojson(path, use_ogr=False)
    with open(path) as file:
        data = json.load(file)
        assert len(data["features"]) == 1


def test_export_reproject(ga, tmp_path):
    path = str(tmp_path / "exporter_test_lines.json")
    ga.lines.reproject_to("4326").to_geojson(path, use_ogr=False)
    with open(path) as file:
        data = json.load(file)
        p1, _ = data["features"][1]["geometry"]["coordinates"]
        x, y = p1
        # Should be somewhere in the Netherlands
        assert 4.18 < x < 5.66
        assert 52.10 < y < 52.92


def test_export_null(ga, tmp_path):
    path = str(tmp_path / "exporter_test_null.json")
    ga.nodes.manholes.filter(content_pk=12).to_geojson(path, use_ogr=False)
    with open(path) as file:
        data = json.load(file)
        assert data["features"][0]["properties"]["drain_level"] is None


@pytest.mark.parametrize(
    "export_method,expected_filename",
    [
        ("2d_groundwater_lines", "lines_2D_groundwater"),
        ("2d_openwater_lines", "lines_2D_open_water"),
        ("2d_vertical_infiltration_lines", "lines_2D_vertical_infiltration"),
        ("levees", "levees"),
        ("breaches", "breaches"),
        ("channels", "channels"),
        ("pipes", "pipes"),
        ("weirs", "weirs"),
        ("culverts", "culverts"),
        # ("orifices", "orifices"),  no orifices in test file
        ("manholes", "manholes"),
        ("nodes", "nodes_1D_all"),
        ("pumps", "pumps"),
        ("grid", "grid_2D_open_water"),
        ("grid", "grid_2D_groundwater"),
        ("flowlines", "flowlines"),
        ("fragments", "fragments"),
    ],
)
def test_export_method(ga_export, export_method, expected_filename):
    getattr(ga_export, "export_" + export_method)()
    assert os.path.exists(os.path.join(ga_export._dest, expected_filename + ".json"))


def test_cross_section_export(ga_export):
    ga_export.export_channels()
    with open(os.path.join(ga_export._dest, "channels.json"), "r") as file:
        data = json.load(file)

    assert data["features"][0]["properties"]["cross_section_type_1"] is None
    assert data["features"][0]["properties"]["cross_section_table_1"] == [[], []]
    assert data["features"][0]["properties"]["cross_section_type_2"] is None
    assert data["features"][0]["properties"]["cross_section_table_2"] == [[], []]
    assert data["features"][0]["properties"]["cross_section_weight"] is None
