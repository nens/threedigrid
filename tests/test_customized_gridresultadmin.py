from os.path import join

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from threedigrid.admin.gridresultadmin import CustomizedResultAdmin
from threedigrid.numpy_utils import create_np_lookup_index_for

from .conftest import test_file_dir


@pytest.fixture
def grc():
    grc = CustomizedResultAdmin(
        join(test_file_dir, "bergen_with_boundaries/gridadmin.h5"),
        join(test_file_dir, "bergen_with_boundaries/customized_results_3di.nc"),
    )
    yield grc
    grc.close()


@pytest.fixture
def grc_breach():
    grc = CustomizedResultAdmin(
        join(test_file_dir, "breach_growth/gridadmin.h5"),
        join(test_file_dir, "breach_growth/customized_results_3di.nc"),
    )
    yield grc
    grc.close()


def test_overriden_grc_properties(grc: CustomizedResultAdmin):
    assert grc.levees is None
    assert grc.nodes_embedded is None
    assert grc.cross_sections is None
    assert grc.cells is None


def test_grc_areas(grc: CustomizedResultAdmin):
    assert grc.areas == ["area1", "area2"]


def test_grc_root_node_ids(grc: CustomizedResultAdmin):
    assert_array_equal(
        grc.nodes.id,
        [0, 2077, 2078, 2091, 2092, 7730, 7731, 7744, 7745, 12064, 12311, 12545],
    )
    assert_array_equal(
        grc.nodes.subset("2D_ALL").id,
        [2077, 2078, 2091, 2092, 7730, 7731, 7744, 7745],
    )
    assert_array_equal(
        grc.nodes.subset("1D_ALL").id,
        [12064, 12311, 12545],
    )


@pytest.mark.parametrize("field", ["s1", "vol", "su", "rain", "q_lat"])
def test_grc_root_node_results_composites(grc: CustomizedResultAdmin, field):
    """Check composite fields for base nodes attribute"""
    assert_array_equal(
        getattr(grc.nodes, field)[:, 1:],
        np.concatenate(
            (
                grc.netcdf_file[f"Mesh2D_{field}"][:10],
                grc.netcdf_file[f"Mesh1D_{field}"][:10],
            ),
            axis=1,
        ),
    )
    assert_array_equal(
        getattr(grc.nodes.subset("2D_ALL"), field),
        grc.netcdf_file[f"Mesh2D_{field}"][:10],
    )
    assert_array_equal(
        getattr(grc.nodes.subset("1D_ALL"), field),
        grc.netcdf_file[f"Mesh1D_{field}"][:10],
    )


@pytest.mark.parametrize("field", ["ucx", "ucy", "q_sss"])
def test_grc_root_node_results_subsets(grc: CustomizedResultAdmin, field):
    """Check subset fields for base nodes attribute"""
    assert_array_equal(
        getattr(grc.nodes, field)[:, 1:],
        np.concatenate(
            (
                grc.netcdf_file[f"Mesh2D_{field}"][:10],
                np.zeros((10, 3), dtype=np.float32),
            ),
            axis=1,
        ),
    )
    assert_array_equal(
        getattr(grc.nodes.subset("2D_ALL"), field),
        grc.netcdf_file[f"Mesh2D_{field}"][:10],
    )


def test_grc_area1_node_ids(grc: CustomizedResultAdmin):
    assert_array_equal(
        grc.area1.nodes.id,
        [0, 2078, 2092, 7731, 7745, 12064, 12311, 12545],
    )
    assert_array_equal(
        grc.area1.nodes.subset("2D_ALL").id,
        [2078, 2092, 7731, 7745],
    )
    assert_array_equal(
        grc.area1.nodes.subset("1D_ALL").id,
        [12064, 12311, 12545],
    )


def test_grc_area2_node_ids(grc: CustomizedResultAdmin):
    assert_array_equal(
        grc.area2.nodes.id,
        [0, 2077, 2091, 7730, 7744],
    )
    assert_array_equal(
        grc.area2.nodes.subset("2D_ALL").id,
        [2077, 2091, 7730, 7744],
    )
    assert_array_equal(
        grc.area2.nodes.subset("1D_ALL").id,
        [],
    )


@pytest.mark.parametrize("field", ["s1", "vol", "su", "rain", "q_lat"])
@pytest.mark.parametrize("area", ["area1", "area2"])
def test_grc_node_areas_results_composites(grc: CustomizedResultAdmin, field, area):
    """Check composite fields for areas nodes attribute"""
    subset_index_2d = create_np_lookup_index_for(
        getattr(grc, area).nodes.subset("2D_ALL").id,
        grc.nodes.subset("2D_ALL").id,
    )
    subset_index_1d = create_np_lookup_index_for(
        getattr(grc, area).nodes.subset("1D_ALL").id, grc.nodes.subset("1D_ALL").id
    )
    assert_array_equal(
        getattr(getattr(grc, area).nodes, field)[:, 1:],
        np.concatenate(
            (
                grc.netcdf_file[f"Mesh2D_{field}"][:10, subset_index_2d],
                grc.netcdf_file[f"Mesh1D_{field}"][:10, subset_index_1d],
            ),
            axis=1,
        ),
    )
    assert_array_equal(
        getattr(getattr(grc, area).nodes.subset("2D_ALL"), field),
        grc.netcdf_file[f"Mesh2D_{field}"][:10, subset_index_2d],
    )
    assert_array_equal(
        getattr(getattr(grc, area).nodes.subset("1D_ALL"), field),
        grc.netcdf_file[f"Mesh1D_{field}"][:10, subset_index_1d],
    )


@pytest.mark.parametrize("field", ["ucx", "ucy", "q_sss"])
@pytest.mark.parametrize("area", ["area1", "area2"])
def test_grc_node_area_results_subsets(grc: CustomizedResultAdmin, field, area):
    """Check subset fields for area nodes attribute"""
    subset_index_2d = create_np_lookup_index_for(
        getattr(grc, area).nodes.subset("2D_ALL").id,
        grc.nodes.subset("2D_ALL").id,
    )
    one_d_size = getattr(grc, area).nodes.subset("1D_ALL").count

    assert_array_equal(
        getattr(getattr(grc, area).nodes, field)[:, 1:],
        np.concatenate(
            (
                grc.netcdf_file[f"Mesh2D_{field}"][:10, subset_index_2d],
                np.zeros((10, one_d_size), dtype=np.float32),
            ),
            axis=1,
        ),
    )
    assert_array_equal(
        getattr(getattr(grc, area).nodes.subset("2D_ALL"), field),
        grc.netcdf_file[f"Mesh2D_{field}"][:10, subset_index_2d],
    )
    assert_array_equal(
        getattr(getattr(grc, area).nodes.subset("1D_ALL"), field),
        [],
    )


def test_grc_root_line_ids(grc: CustomizedResultAdmin):
    assert_array_equal(
        grc.lines.id,
        [0, 5418, 11150, 22635, 28367, 29085, 29629],
    )
    assert_array_equal(
        grc.lines.subset("2D_ALL").id,
        [5418, 11150, 22635, 28367],
    )
    assert_array_equal(
        grc.lines.subset("1D_ALL").id,
        [29085, 29629],
    )


def test_grc_area1_line_ids(grc: CustomizedResultAdmin):
    assert_array_equal(
        grc.area1.lines.id,
        [0, 28367, 29085, 29629],
    )
    assert_array_equal(
        grc.area1.lines.subset("2D_ALL").id,
        [28367],
    )
    assert_array_equal(
        grc.area1.lines.subset("1D_ALL").id,
        [29085, 29629],
    )


def test_grc_area2_line_ids(grc: CustomizedResultAdmin):
    assert_array_equal(
        grc.area2.lines.id,
        [0, 5418, 11150, 22635],
    )
    assert_array_equal(
        grc.area2.lines.subset("2D_ALL").id,
        [5418, 11150, 22635],
    )
    assert_array_equal(
        grc.area2.lines.subset("1D_ALL").id,
        [],
    )


@pytest.mark.parametrize("field", ["u1", "q", "au"])
def test_grc_root_line_results_composites(grc: CustomizedResultAdmin, field):
    """Check composite fields for base lines attribute"""
    assert_array_equal(
        getattr(grc.lines, field)[:, 1:],
        np.concatenate(
            (
                grc.netcdf_file[f"Mesh2D_{field}"][:10],
                grc.netcdf_file[f"Mesh1D_{field}"][:10],
            ),
            axis=1,
        ),
    )
    assert_array_equal(
        getattr(grc.lines.subset("2D_ALL"), field),
        grc.netcdf_file[f"Mesh2D_{field}"][:10],
    )
    assert_array_equal(
        getattr(grc.lines.subset("1D_ALL"), field),
        grc.netcdf_file[f"Mesh1D_{field}"][:10],
    )


@pytest.mark.parametrize("field", ["breach_depth", "breach_width"])
def test_grc_root_line_results_subsets(grc: CustomizedResultAdmin, field):
    """Check subset fields for base lines attribute"""
    assert_array_equal(
        getattr(grc.lines, field)[:, 1:],
        np.concatenate(
            (
                np.zeros((10, 4), dtype=np.float32),
                grc.netcdf_file[f"Mesh1D_{field}"][:10],
            ),
            axis=1,
        ),
    )
    assert_array_equal(
        getattr(grc.lines.subset("2D_ALL"), field),
        np.zeros((10, 4), dtype=np.float32),
    )
    assert_array_equal(
        getattr(grc.lines.subset("1D_ALL"), field),
        grc.netcdf_file[f"Mesh1D_{field}"][:10],
    )


@pytest.mark.parametrize("field", ["u1", "q", "au"])
@pytest.mark.parametrize("area", ["area1", "area2"])
def test_grc_area_line_results_composites(grc: CustomizedResultAdmin, field, area):
    """Check composite fields for area lines attribute"""
    subset_index_2d = create_np_lookup_index_for(
        getattr(grc, area).lines.subset("2D_ALL").id,
        grc.lines.subset("2D_ALL").id,
    )
    subset_index_1d = create_np_lookup_index_for(
        getattr(grc, area).lines.subset("1D_ALL").id, grc.lines.subset("1D_ALL").id
    )
    assert_array_equal(
        getattr(getattr(grc, area).lines, field)[:, 1:],
        np.concatenate(
            (
                grc.netcdf_file[f"Mesh2D_{field}"][:10, subset_index_2d],
                grc.netcdf_file[f"Mesh1D_{field}"][:10, subset_index_1d],
            ),
            axis=1,
        ),
    )
    assert_array_equal(
        getattr(getattr(grc, area).lines.subset("2D_ALL"), field),
        grc.netcdf_file[f"Mesh2D_{field}"][:10, subset_index_2d],
    )
    assert_array_equal(
        getattr(getattr(grc, area).lines.subset("1D_ALL"), field),
        grc.netcdf_file[f"Mesh1D_{field}"][:10, subset_index_1d],
    )


@pytest.mark.parametrize("field", ["breach_depth", "breach_width"])
def test_grc_line_area1_1d_results(grc, field):
    """Check subset fields for base lines attribute"""
    subset_index_2d = create_np_lookup_index_for(
        grc.area1.lines.subset("2D_ALL").id,
        grc.lines.subset("2D_ALL").id,
    )
    subset_index_1d = create_np_lookup_index_for(
        grc.area1.lines.subset("1D_ALL").id, grc.lines.subset("1D_ALL").id
    )

    assert_array_equal(
        getattr(grc.area1.lines, field)[:, 1:],
        np.concatenate(
            (
                np.zeros((10, subset_index_2d.size), dtype=np.float32),
                grc.netcdf_file[f"Mesh1D_{field}"][:10, subset_index_1d],
            ),
            axis=1,
        ),
    )

    assert_array_equal(
        getattr(grc.area1.lines.subset("2D_ALL"), field),
        np.zeros((10, subset_index_2d.size), dtype=np.float32),
    )

    assert_array_equal(
        getattr(grc.area1.lines.subset("1D_ALL"), field),
        grc.netcdf_file[f"Mesh1D_{field}"][:10, subset_index_1d],
    ),


@pytest.mark.parametrize("field", ["breach_depth", "breach_width"])
def test_grc_line_area2_1d_results(grc, field):
    """No area 2 1D"""
    assert_array_equal(getattr(grc.area2.lines, field)[:], [])

    assert_array_equal(
        getattr(grc.area2.lines.subset("2D_ALL"), field),
        [],
    )

    assert_array_equal(getattr(grc.area2.lines.subset("1D_ALL"), field), []),


def test_pumps_root(grc: CustomizedResultAdmin):
    assert_array_equal(
        grc.pumps.id,
        [0, 1, 2],
    )
    assert_array_equal(
        grc.pumps.q_pump[:, 1:],
        grc.netcdf_file["Mesh1D_q_pump"][:10],
    )


def test_pumps_area1(grc: CustomizedResultAdmin):
    assert_array_equal(
        grc.area1.pumps.id,
        [0, 1],
    )
    assert_array_equal(
        grc.area1.pumps.q_pump[:, 1:].flatten(),
        grc.netcdf_file["Mesh1D_q_pump"][:10, 0],
    )


def test_pumps_area2(grc: CustomizedResultAdmin):
    assert_array_equal(
        grc.area2.pumps.id,
        [0, 2],
    )
    assert_array_equal(
        grc.area2.pumps.q_pump[:, 1:].flatten(),
        grc.netcdf_file["Mesh1D_q_pump"][:10, 1],
    )


def test_breaches_root(grc_breach: CustomizedResultAdmin):
    grc_breach.set_timeseries_chunk_size(50)
    assert_array_equal(
        grc_breach.breaches.id,
        [0, 764, 765],
    )
    assert_array_equal(
        grc_breach.breaches.timestamps,
        grc_breach.netcdf_file["time"][:],
    )
    assert_array_equal(
        grc_breach.breaches.breach_depth[:, 1:],
        grc_breach.netcdf_file["Mesh1D_breach_depth"][:],
    )
    assert_array_equal(
        grc_breach.breaches.breach_width[:, 1:],
        grc_breach.netcdf_file["Mesh1D_breach_width"][:],
    )


def test_breaches_area1(grc_breach: CustomizedResultAdmin):
    grc_breach.set_timeseries_chunk_size(50)
    assert_array_equal(
        grc_breach.area1.breaches.id[1:],
        [764],
    )
    assert_array_equal(
        grc_breach.area1.breaches.breach_depth[:, 1:].flatten(),
        grc_breach.netcdf_file["Mesh1D_breach_depth"][:, 0],
    )
    assert_array_equal(
        grc_breach.area1.breaches.breach_width[:, 1:].flatten(),
        grc_breach.netcdf_file["Mesh1D_breach_width"][:, 0],
    )


def test_breaches_area2(grc_breach: CustomizedResultAdmin):
    grc_breach.set_timeseries_chunk_size(50)
    assert_array_equal(
        grc_breach.area2.breaches.id[1:],
        [765],
    )
    assert_array_equal(
        grc_breach.area2.breaches.breach_depth[:, 1:].flatten(),
        grc_breach.netcdf_file["Mesh1D_breach_depth"][:, 1],
    )
    assert_array_equal(
        grc_breach.area2.breaches.breach_width[:, 1:].flatten(),
        grc_breach.netcdf_file["Mesh1D_breach_width"][:, 1],
    )
