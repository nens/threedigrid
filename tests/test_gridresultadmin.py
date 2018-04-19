from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import pytest

import numpy as np


from threedigrid.admin.gridresultadmin import GridH5ResultAdmin

test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
result_file = os.path.join(test_file_dir, "results_3di.nc")
agg_result_file = os.path.join(test_file_dir, 'flow_aggregate.nc')
grid_file = os.path.join(test_file_dir, "gridadmin.h5")


@pytest.fixture()
def agg_gr():
    gr = GridH5ResultAdmin(grid_file, agg_result_file)
    yield gr
    gr.close()


@pytest.fixture()
def gr():
    gr = GridH5ResultAdmin(grid_file, result_file)
    yield gr
    gr.close()


def test_nodes_timeseries_start_end_time_kwargs(gr):
    qs_s1 = gr.nodes.timeseries(start_time=0, end_time=500).s1
    assert qs_s1.shape[0] == 17


def test_nodes_timeseries_with_subset(gr):
    qs_s1 = gr.nodes.subset('1d_all').timeseries(start_time=0, end_time=500).s1
    assert qs_s1.shape[0] == 17 and qs_s1.shape[1] > 0


def test_nodes_timeseries_start_time_only_kwarg(gr):
    qs = gr.nodes.timeseries(start_time=450)
    assert qs.s1.shape[0] == 6


def test_nodes_timeseries_end_time_only_kwarg(gr):
    qs = gr.nodes.timeseries(end_time=500)
    assert qs.s1.shape[0] == 17


def test_nodes_timeseries_index_filter(gr):
    qs_s1 = gr.nodes.timeseries(indexes=[1, 2, 3]).s1
    assert qs_s1.shape[0] == 3


def test_nodes_timeseries_slice_filter(gr):
    qs_s1 = gr.nodes.timeseries(indexes=slice(1, 4)).s1
    assert qs_s1.shape[0] == 3


def test_pump_timeseries_slice_filter(gr):
    qs = gr.pumps.timeseries(indexes=slice(1, 4)).Mesh1D_q_pump
    assert qs.shape[0] == 3


def test_pump_timeseries_index_filter(gr):
    qs = gr.pumps.timeseries(indexes=[1, 2, 3]).Mesh1D_q_pump
    assert qs.shape[0] == 3


def test_breach_timeseries_slice_filter(gr):
    qs = gr.breaches.timeseries(indexes=slice(1, 4)).Mesh1D_breach_depth
    assert qs.shape[0] == 3


def test_breach_timeseries_index_filter(gr):
    qs = gr.breaches.timeseries(indexes=[1, 2, 3]).Mesh1D_breach_width
    assert qs.shape[0] == 3


def test_lines_timeseries_index_filter(gr):
    qs_u1 = gr.lines.timeseries(indexes=[1, 2, 3, 4, 5]).u1
    assert qs_u1.shape[0] == 5

def test_lines_timeseries_slice_filter(gr):
    qs_u1 = gr.lines.timeseries(indexes=slice(1, 4)).u1
    assert qs_u1.shape[0] == 3

def test_lines_timeseries_with_subset(gr):
    qs_u1 = gr.lines.subset('1d_all').timeseries(indexes=slice(1, 4)).u1
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
        gr.lines.timeseries(indexes='wrong').u1


def test_set_timeseries_chunk_size_raises_value_error(gr):
    # default should be 10
    with pytest.raises(ValueError):
        gr.set_timeseries_chunk_size(0)

    with pytest.raises(ValueError):
        gr.set_timeseries_chunk_size(-5)

    with pytest.raises(ValueError):
        gr.set_timeseries_chunk_size('20.5')


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
