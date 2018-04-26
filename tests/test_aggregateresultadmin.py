from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import pytest

import numpy as np


from threedigrid.admin.gridresultadmin import GridH5AggregateResultAdmin

test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
result_file = os.path.join(test_file_dir, "results_3di.nc")
agg_result_file = os.path.join(test_file_dir, 'aggregate_results_3di.nc')
grid_file = os.path.join(test_file_dir, "gridadmin.h5")


@pytest.fixture()
def agg_gr():
    gr = GridH5AggregateResultAdmin(grid_file, agg_result_file)
    yield gr
    gr.close()


def test_get_timestamps_nodes(agg_gr):
    ts = agg_gr.nodes.get_timestamps('rain_avg')
    assert isinstance(ts, np.ndarray)
    assert ts.size > 0


def test_get_timestamps_raises_attribute_error(agg_gr):
    with pytest.raises(AttributeError):
        agg_gr.nodes.get_timestamps('does_not_exist')


def test_get_timestamps_lines(agg_gr):
    ts = agg_gr.nodes.get_timestamps('q_cum')
    assert isinstance(ts, np.ndarray)
    assert ts.size > 0


def test_get_time_unit(agg_gr):
    tu = agg_gr.nodes.get_time_unit('q_cum')
    assert tu.startswith('seconds since ')


# TODO
# def test_get_timestamps_pumps(agg_gr):
#     ts = agg_gr.nodes.get_timestamps('q_cum')
#     assert isinstance(ts, np.ndarray)
#     assert ts.size > 0


def test_nodes_timeseries_start_end_time_kwargs(agg_gr):
    ts = agg_gr.nodes.get_timestamps('s1_max')
    qs_s1_max = agg_gr.nodes.timeseries(
        start_time=ts[0], end_time=ts[1]).s1_max
    assert qs_s1_max.shape[0] == 2


def test_nodes_timeseries_with_subset(agg_gr):
    ts = agg_gr.nodes.get_timestamps('s1_max')
    qs_s1_max = agg_gr.nodes.subset(
        '1d_all').timeseries(start_time=ts[0], end_time=ts[1]).s1_max
    assert qs_s1_max.shape[0] == 2 and qs_s1_max.shape[1] > 0


def test_nodes_timeseries_start_time_only_kwarg(agg_gr):
    ts = agg_gr.nodes.get_timestamps('s1_max')
    qs_s1_max = agg_gr.nodes.timeseries(start_time=ts[1]).s1_max
    assert qs_s1_max.shape[0] == 2


def test_nodes_timeseries_end_time_only_kwarg(agg_gr):
    ts = agg_gr.nodes.get_timestamps('s1_max')
    qs_s1_max = agg_gr.nodes.timeseries(end_time=ts[1])
    assert qs_s1_max.s1_max.shape[0] == 2


def test_nodes_timeseries_slice_filter(agg_gr):
    qs_s1_min = agg_gr.nodes.timeseries(indexes=slice(0, 1)).s1_min
    assert qs_s1_min.shape[0] == 1

# TODO once the threedicore has implemented aggregations for pumpstations
# TODO and breaches also implement some tests
# def test_pump_timeseries_slice_filter(agg_gr):
#     qs = agg_gr.pumps.timeseries(indexes=slice(1, 4)).q_pump
#     assert qs.shape[0] == 3
#
#
# def test_pump_timeseries_index_filter(agg_gr):
#     qs = agg_gr.pumps.timeseries(indexes=[1, 2, 3]).q_pump
#     assert qs.shape[0] == 3
#
#
# def test_breach_timeseries_slice_filter(agg_gr):
#     qs = agg_gr.breaches.timeseries(indexes=slice(1, 4)).depth
#     assert qs.shape[0] == 3
#
#
# def test_breach_timeseries_index_filter(agg_gr):
#     qs = agg_gr.breaches.timeseries(indexes=[1, 2, 3]).width
#     assert qs.shape[0] == 3
#
#
# def test_lines_timeseries_index_filter(agg_gr):
#     qs_u1 = agg_gr.lines.timeseries(indexes=[1, 2, 3, 4, 5]).u1
#     assert qs_u1.shape[0] == 5
#
# def test_lines_timeseries_slice_filter(agg_gr):
#     qs_u1 = agg_gr.lines.timeseries(indexes=slice(1, 4)).u1
#     assert qs_u1.shape[0] == 3
#
# def test_lines_timeseries_with_subset(agg_gr):
#     qs_u1 = agg_gr.lines.subset('1d_all').timeseries(indexes=slice(1, 4)).u1
#     assert qs_u1.shape[0] == 3 and qs_u1.shape[1] > 0
