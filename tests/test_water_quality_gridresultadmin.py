from os.path import join

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from threedigrid.admin.gridresultadmin import (
    CustomizedWaterQualityResultAdmin,
    GridH5WaterQualityResultAdmin,
)

from .conftest import test_file_dir


@pytest.fixture
def wqa():
    return GridH5WaterQualityResultAdmin(
        join(test_file_dir, "water_quality/gridadmin.h5"),
        join(test_file_dir, "water_quality/water_quality_results_3di.nc"),
    )


@pytest.fixture
def cwqa():
    return CustomizedWaterQualityResultAdmin(
        join(test_file_dir, "water_quality/gridadmin.h5"),
        join(test_file_dir, "water_quality/customized_water_quality_results_3di.nc"),
    )


def test_concentration_values(wqa):
    assert_array_equal(
        wqa.substance1.concentration[:, 1:], wqa.netcdf_file["substance1_1D"][:]
    )
    assert_array_equal(
        wqa.substance2.concentration[:, 1:], wqa.netcdf_file["substance2_1D"][:]
    )
    assert_array_equal(
        wqa.substance3.concentration[:, 1:], wqa.netcdf_file["substance3_1D"][:]
    )


def test_substance_names(wqa):
    assert wqa.substance1.name == "test1"
    assert wqa.substance2.name == "test2"
    assert wqa.substance3.name == "test3"


def test_units(wqa):
    assert wqa.substance1.units == ""
    assert wqa.substance2.units == "kg/m3"
    assert wqa.substance3.units == "g/ml"


def test_overriden_properties(cwqa: CustomizedWaterQualityResultAdmin):
    assert cwqa.nodes is None
    assert cwqa.lines is None
    assert cwqa.breaches is None
    assert cwqa.pumps is None
    assert cwqa.levees is None
    assert cwqa.nodes_embedded is None
    assert cwqa.cross_sections is None
    assert cwqa.cells is None


def test_substance_names_customized(cwqa: CustomizedWaterQualityResultAdmin):
    assert cwqa.substance1.name == "test1"
    assert cwqa.substance2.name == "test2"
    assert cwqa.substance3.name == "test3"
    assert cwqa.area1.substance1.name == "test1"
    assert cwqa.area1.substance2.name == "test2"
    assert cwqa.area1.substance3.name == "test3"
    assert cwqa.area2.substance1.name == "test1"
    assert cwqa.area2.substance2.name == "test2"
    assert cwqa.area2.substance3.name == "test3"


def test_substance_units_customized(cwqa: CustomizedWaterQualityResultAdmin):
    assert cwqa.substance1.units == ""
    assert cwqa.substance2.units == "kg/m3"
    assert cwqa.substance3.units == "g/ml"
    assert cwqa.area1.substance1.units == ""
    assert cwqa.area1.substance2.units == "kg/m3"
    assert cwqa.area1.substance3.units == "g/ml"
    assert cwqa.area2.substance1.units == ""
    assert cwqa.area2.substance2.units == "kg/m3"
    assert cwqa.area2.substance3.units == "g/ml"


def test_areas_list(cwqa: CustomizedWaterQualityResultAdmin):
    assert cwqa.areas == ["area1", "area2"]


def test_node_ids(cwqa: CustomizedWaterQualityResultAdmin):
    assert_array_equal(cwqa.substance1.id, np.array([0, 1, 2, 3, 301, 303]))
    assert_array_equal(cwqa.area1.substance2.id, np.array([0, 1, 3, 303]))
    assert_array_equal(cwqa.area2.substance3.id, np.array([0, 2, 301, 303]))


def test_concentration_values_customized(cwqa: CustomizedWaterQualityResultAdmin):
    cwqa.set_timeseries_chunk_size(20)
    assert_array_equal(
        cwqa.substance1.concentration[:, 1:], cwqa.netcdf_file["substance1_1D"][:20]
    )
    assert_array_equal(
        cwqa.substance2.concentration[:, 1:], cwqa.netcdf_file["substance2_1D"][:20]
    )
    assert_array_equal(
        cwqa.substance3.concentration[:, 1:], cwqa.netcdf_file["substance3_1D"][:20]
    )

    cwqa.set_timeseries_chunk_size(30)
    assert_array_equal(
        cwqa.area1.substance1.concentration[:, 1:],
        np.take(cwqa.netcdf_file["substance1_1D"][:30], [0, 2, 4], axis=1),
    )
    assert_array_equal(
        cwqa.area1.substance2.concentration[:, 1:],
        np.take(cwqa.netcdf_file["substance2_1D"][:30], [0, 2, 4], axis=1),
    )
    assert_array_equal(
        cwqa.area1.substance3.concentration[:, 1:],
        np.take(cwqa.netcdf_file["substance3_1D"][:30], [0, 2, 4], axis=1),
    )

    assert_array_equal(
        cwqa.area2.substance1.concentration[:, 1:],
        np.take(cwqa.netcdf_file["substance1_1D"][:30], [1, 3, 4], axis=1),
    )
    assert_array_equal(
        cwqa.area2.substance2.concentration[:, 1:],
        np.take(cwqa.netcdf_file["substance2_1D"][:30], [1, 3, 4], axis=1),
    )
    assert_array_equal(
        cwqa.area2.substance3.concentration[:, 1:],
        np.take(cwqa.netcdf_file["substance3_1D"][:30], [1, 3, 4], axis=1),
    )
