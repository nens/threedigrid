from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import pytest
import numpy as np

from threedigrid.admin.nodes.models import Nodes


def test_nodes_timeseries_start_end_time_kwargs(gr):
    ts = gr.nodes.timestamps
    qs_s1 = gr.nodes.timeseries(start_time=ts[0], end_time=ts[6]).s1
    assert qs_s1.shape[0] == ts[0:6+1].size


def test_nodes_timeseries_with_subset(gr):
    qs_s1 = gr.nodes.subset('1d_all').timeseries(start_time=0, end_time=500).s1
    assert qs_s1.shape[0] == 9 and qs_s1.shape[1] > 0


def test_nodes_timeseries_start_time_only_kwarg(gr):
    ts = gr.nodes.timestamps
    qs = gr.nodes.timeseries(start_time=ts[6])
    assert qs.s1.shape[0] == ts[6:].size


def test_nodes_timeseries_end_time_only_kwarg(gr):
    ts = gr.nodes.timestamps
    qs = gr.nodes.timeseries(end_time=ts[6])
    assert qs.s1.shape[0] == ts[:6+1].size


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


def test_get_model_instance_by_field_name(gr):
    inst = gr.get_model_instance_by_field_name('s1')
    assert isinstance(inst, Nodes)


def test_get_model_instance_by_field_name_raises_index_error_unknown_field(gr):
    with pytest.raises(IndexError):
        gr.get_model_instance_by_field_name('unknown_field')


def test_get_model_instance_by_field_name_raises_index_error(gr):
    with pytest.raises(IndexError):
        gr.get_model_instance_by_field_name('zoom_category')


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
