import numpy as np
import pytest

from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedigrid.admin.nodes.models import Nodes


def test_gr_with_boundaries(gr_bergermeer_with_boundaries: GridH5ResultAdmin):
    gr_one_d_line_subset = gr_bergermeer_with_boundaries.lines.subset("1D_ALL")
    gr_two_d_node_subset = gr_bergermeer_with_boundaries.nodes.subset("2D_ALL")

    assert np.all(
        gr_one_d_line_subset.id
        == gr_bergermeer_with_boundaries.netcdf_file["Mesh1DLine_id"][:]
    )
    assert np.all(
        gr_two_d_node_subset.id
        == gr_bergermeer_with_boundaries.netcdf_file["Mesh2DNode_id"][:]
    )

    # Check ordering/correctness of breach_depth and breach_width
    assert np.all(
        gr_one_d_line_subset.breach_depth
        == gr_bergermeer_with_boundaries.netcdf_file["Mesh1D_breach_depth"][:]
    )
    assert np.all(
        gr_one_d_line_subset.breach_width
        == gr_bergermeer_with_boundaries.netcdf_file["Mesh1D_breach_width"][:]
    )

    # Check ucx and ucy on nodes
    assert np.all(
        gr_two_d_node_subset.ucx
        == gr_bergermeer_with_boundaries.netcdf_file["Mesh2D_ucx"][:]
    )
    assert np.all(
        gr_two_d_node_subset.ucy
        == gr_bergermeer_with_boundaries.netcdf_file["Mesh2D_ucy"][:]
    )


def test_nodes_timeseries_start_end_time_kwargs(gr):
    ts = gr.nodes.timestamps
    qs_s1 = gr.nodes.timeseries(start_time=ts[0], end_time=ts[6]).s1
    assert qs_s1.shape[0] == ts[0 : 6 + 1].size


def test_nodes_timeseries_start_end_time_subset(gr):
    ts = gr.nodes.timestamps
    qs_s1 = (
        gr.nodes.subset("2D_OPEN_WATER").timeseries(start_time=ts[0], end_time=ts[6]).s1
    )
    assert qs_s1.shape[0] == ts[0 : 6 + 1].size


def test_nodes_timeseries_with_subset(gr):
    qs_s1 = gr.nodes.subset("1d_all").timeseries(start_time=0, end_time=500).s1
    assert qs_s1.shape[0] == 9 and qs_s1.shape[1] > 0


def test_nodes_timeseries_start_time_only_kwarg(gr):
    ts = gr.nodes.timestamps
    qs = gr.nodes.timeseries(start_time=ts[6])
    assert qs.s1.shape[0] == ts[6:].size


def test_nodes_timeseries_end_time_only_kwarg(gr):
    ts = gr.nodes.timestamps
    qs = gr.nodes.timeseries(end_time=ts[6])
    assert qs.s1.shape[0] == ts[: 6 + 1].size


def test_nodes_timeseries_index_filter(gr):
    qs_s1 = gr.nodes.timeseries(indexes=[1, 2, 3]).s1
    assert qs_s1.shape[0] == 3


def test_nodes_timeseries_slice_filter(gr):
    qs_s1 = gr.nodes.timeseries(indexes=slice(1, 4)).s1
    assert qs_s1.shape[0] == 3


def test_pump_timeseries_slice_filter(gr):
    qs = gr.pumps.timeseries(indexes=slice(1, 4)).q_pump
    assert qs.shape[0] == 3


def test_pump_timeseries_index_filter(gr):
    qs = gr.pumps.timeseries(indexes=[1, 2, 3]).q_pump
    assert qs.shape[0] == 3


def test_breach_timeseries_slice_filter(gr):
    qs = gr.breaches.timeseries(indexes=slice(1, 4)).breach_depth
    assert qs.shape[0] == 3


def test_breach_timeseries_index_filter(gr):
    qs = gr.breaches.timeseries(indexes=[1, 2, 3]).breach_width
    assert qs.shape[0] == 3


def test_lines_timeseries_index_filter(gr):
    qs_u1 = gr.lines.timeseries(indexes=[1, 2, 3, 4, 5]).u1
    assert qs_u1.shape[0] == 5


def test_lines_timeseries_slice_filter(gr):
    qs_u1 = gr.lines.timeseries(indexes=slice(1, 4)).u1
    assert qs_u1.shape[0] == 3


def test_lines_timeseries_with_subset(gr):
    qs_u1 = gr.lines.subset("1d_all").timeseries(indexes=slice(1, 4)).u1
    assert qs_u1.shape[0] == 3 and qs_u1.shape[1] > 0


def test_set_timeseries_chunk_size(gr):
    # default should be 10
    assert gr.timeseries_chunk_size == 10
    gr.set_timeseries_chunk_size(15)
    assert gr.timeseries_chunk_size == 15


def test_missing_kwargs_raises_key_error(gr):
    # default should be 10
    with pytest.raises(KeyError):
        gr.lines.timeseries().u1


def test_index_key_raises_type_error(gr):
    # default should be 10
    with pytest.raises(TypeError):
        gr.lines.timeseries(indexes="wrong").u1


def test_set_timeseries_chunk_size_raises_value_error(gr):
    # default should be 10
    with pytest.raises(ValueError):
        gr.set_timeseries_chunk_size(0)

    with pytest.raises(ValueError):
        gr.set_timeseries_chunk_size(-5)

    with pytest.raises(ValueError):
        gr.set_timeseries_chunk_size("20.5")


def test_get_timeseries_mask_filter(gr):
    assert gr.timeseries_chunk_size == 10
    gr.set_timeseries_chunk_size(50)
    mask_f = gr.nodes.get_timeseries_mask_filter()
    assert mask_f == slice(0, 50, None)


def test_timestamps(gr):
    np.testing.assert_array_equal(gr.nodes.timestamps, gr.lines.timestamps)
    n_qs = gr.nodes.timeseries(start_time=0, end_time=500)
    l_qs = gr.lines.timeseries(start_time=0, end_time=500)
    np.testing.assert_array_equal(n_qs.timestamps, l_qs.timestamps)


def test_dt_timestamps(gr):
    n_qs = gr.nodes.timeseries(start_time=0, end_time=500)
    assert len(n_qs.dt_timestamps) == len(n_qs.timestamps)


def test_dt_timeseries_sampling(gr):
    s1 = gr.nodes.timeseries(start_time=0).sample(5).s1
    assert len(s1) == 5
    s1 = gr.nodes.timeseries(start_time=1).sample(5).s1
    assert len(s1) == 5
    s1 = gr.nodes.timeseries(indexes=slice(1, None)).sample(5).s1
    assert len(s1) == 5


def test_get_model_instance_by_field_name(gr):
    inst = gr.get_model_instance_by_field_name("s1")
    assert isinstance(inst, Nodes)


def test_get_model_instance_by_field_name_raises_index_error_unknown_field(gr):
    with pytest.raises(IndexError):
        gr.get_model_instance_by_field_name("unknown_field")


def test_get_model_instance_by_field_name_raises_index_error(gr):
    with pytest.raises(IndexError):
        gr.get_model_instance_by_field_name("zoom_category")


def test_gr_get_subset_idx_leak(gr):
    assert gr.nodes._get_subset_idx("leak").shape == (10748,)


def test_gr_get_subset_ids_no_composite_field(gr):
    assert gr.nodes._get_subset_idx("s1") is None


def test_gr_chain_filter(gr):
    assert gr.nodes.filter(id=4).get_filtered_field_value("leak").shape == (9, 1)


# commented for now until the new aggregate.nc is finished

# def test_get_node_aggregate_netcdf_results(agg_gr):
#     assert 's1_max' in agg_gr.netcdf_file.variables.keys()
#     assert 'vol_max' in agg_gr.netcdf_file.variables.keys()
#     assert hasattr(agg_gr.nodes, 's1_max')
#     assert hasattr(agg_gr.nodes, 'vol_max')
#     assert agg_gr.nodes.s1_max.shape[0] > 0
#     assert agg_gr.nodes.vol_max.shape[0] > 0
#
#
# def test_get_line_aggregate_netcdf_results(agg_gr):
#     assert 'q_max' in agg_gr.netcdf_file.variables.keys()
#     assert 'u1_max' in agg_gr.netcdf_file.variables.keys()
#     assert hasattr(agg_gr.lines, 'q_max')
#     assert hasattr(agg_gr.lines, 'u1_max')
#     assert agg_gr.lines.q_max.shape[0] > 0
#     assert agg_gr.lines.u1_max.shape[0] > 0


# def test_get_node_netcdf_results(gr):
#     assert 's1' in gr.netcdf_file.variables.keys()
#     assert 'vol' in gr.netcdf_file.variables.keys()
#     assert hasattr(gr.nodes, 's1')
#     assert hasattr(gr.nodes, 'vol')
#     assert gr.nodes.s1.shape[0] > 0
#     assert gr.nodes.vol.shape[0] > 0
