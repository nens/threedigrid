from os.path import join

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from threedigrid.admin.gridresultadmin import CustomizedResultsAdmin
from threedigrid.numpy_utils import create_np_lookup_index_for

from .conftest import test_file_dir


@pytest.fixture
def grc():
    grc = CustomizedResultsAdmin(
        join(test_file_dir, "bergen_with_boundaries/gridadmin.h5"),
        join(test_file_dir, "bergen_with_boundaries/customized_results_3di.nc"),
    )
    yield grc
    grc.close()


def test_grc_root_node_ids(grc: CustomizedResultsAdmin):
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
def test_grc_root_node_results_composites(grc: CustomizedResultsAdmin, field):
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
def test_grc_root_node_results_subsets(grc: CustomizedResultsAdmin, field):
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


def test_grc_area1_node_ids(grc: CustomizedResultsAdmin):
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


def test_grc_area2_node_ids(grc: CustomizedResultsAdmin):
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
def test_grc_node_areas_results_composites(grc: CustomizedResultsAdmin, field, area):
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
def test_grc_node_area_results_subsets(grc: CustomizedResultsAdmin, field, area):
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


def test_grc_root_line_ids(grc: CustomizedResultsAdmin):
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


def test_grc_area1_line_ids(grc: CustomizedResultsAdmin):
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


def test_grc_area2_line_ids(grc: CustomizedResultsAdmin):
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
def test_grc_root_line_results_composites(grc: CustomizedResultsAdmin, field):
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
def test_grc_root_line_results_subsets(grc: CustomizedResultsAdmin, field):
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
def test_grc_area_line_results_composites(grc: CustomizedResultsAdmin, field, area):
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


@pytest.mark.skip(reason="todo")
def test_pumps_root(grc: CustomizedResultsAdmin):
    assert_array_equal(
        grc.pumps.id,
        [0, 1, 2],
    )
    assert_array_equal(
        grc.pumps.subset("2D_ALL").id,
        [],
    )
    assert_array_equal(
        grc.pumps.subset("1D_ALL").id,
        [1, 2],
    )


@pytest.mark.skip(reason="todo")
def test_pumps_areas(grc: CustomizedResultsAdmin):
    assert_array_equal(
        grc.area1.pumps.id,
        [1],
    )
    assert_array_equal(
        grc.area2.pumps.id,
        [2],
    )


@pytest.mark.skip(reason="todo")
def test_breaches_root(grc: CustomizedResultsAdmin):
    pass  # 1111
