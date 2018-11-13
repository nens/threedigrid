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

# TODO check for intercepted_volume
def test_fieldnames_nodes(agg_gr):
    assert set(agg_gr.nodes._field_names) == {
        'cell_coords', 'content_pk', 'coordinates', 'id', 'is_manhole',
        'node_type', u'q_lat_cum', u'rain_avg', u'rain_cum', u's1_max',
        u's1_min', 'seq_id', u'su_min', u'vol_max', 'zoom_category',
    }

def test_fieldnames_lines(agg_gr):
    assert set(agg_gr.lines._field_names) == {
        'content_pk', 'content_type', 'id', 'kcu', 'lik', 'line',
        'line_coords', 'line_geometries', u'q_cum', u'q_cum_negative',
        u'q_cum_positive', u'u1_avg', 'zoom_category',
    }

def test_fieldnames_pumps(agg_gr):
    assert set(agg_gr.pumps._field_names) == {
        'bottom_level', 'capacity', 'coordinates', 'display_name', 'id',
        'lower_stop_level', 'node1_id', 'node2_id', 'node_coordinates',
        u'q_pump_cum', 'start_level', 'zoom_category'
    }

# TODO check for intercepted_volume
def test_composite_fields_nodes(agg_gr):
    assert set(agg_gr.nodes.Meta.composite_fields.keys()) == {
        u'_mesh_id', u'q_lat_avg', u'q_lat_cum', u'q_lat_cum_negative',
        u'q_lat_cum_positive', u'q_lat_max', u'q_lat_min', u'rain_avg',
        u'rain_cum', u'rain_cum_negative', u'rain_cum_positive', u'rain_max',
        u'rain_min', u's1_avg', u's1_max', u's1_min', u'su_avg', u'su_max',
        u'su_min', u'vol_avg', u'vol_max', u'vol_min', u'vol_sum',
    }

def test_composite_fields_lines(agg_gr):
    assert set(agg_gr.lines.Meta.composite_fields.keys()) == {
        u'_mesh_id', u'au_avg', u'au_max', u'au_min', u'q_avg', u'q_cum',
        u'q_cum_negative', u'q_cum_positive', u'q_max', u'q_min', u'qp_avg',
        u'qp_cum', u'qp_cum_negative', u'qp_cum_positive', u'qp_max',
        u'qp_min', u'u1_avg', u'u1_max', u'u1_min', u'up1_avg', u'up1_max',
        u'up1_min',
    }

def test_composite_fields_pumps(agg_gr):
    assert set(agg_gr.pumps.Meta.composite_fields.keys()) == {
        u'q_pump_avg', u'q_pump_cum', u'q_pump_cum_negative',
        u'q_pump_cum_positive', u'q_pump_max', u'q_pump_min',
    }

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
    assert tu.startswith(b'seconds since ')


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
    assert qs_s1_max.shape[0] == 6


def test_nodes_timeseries_end_time_only_kwarg(agg_gr):
    ts = agg_gr.nodes.get_timestamps('s1_max')
    qs_s1_max = agg_gr.nodes.timeseries(end_time=ts[1])
    assert qs_s1_max.s1_max.shape[0] == 2


def test_nodes_timeseries_slice_filter(agg_gr):
    qs_s1_min = agg_gr.nodes.timeseries(indexes=slice(0, 1)).s1_min
    assert qs_s1_min.shape[0] == 1

@pytest.mark.skip("skip for now until the new aggregate.nc is finished")
def test_get_node_aggregate_netcdf_results(agg_gr):
    assert 's1_max' in agg_gr.netcdf_file.variables.keys()
    assert 'vol_max' in agg_gr.netcdf_file.variables.keys()
    assert hasattr(agg_gr.nodes, 's1_max')
    assert hasattr(agg_gr.nodes, 'vol_max')
    assert agg_gr.nodes.s1_max.shape[0] > 0
    assert agg_gr.nodes.vol_max.shape[0] > 0

@pytest.mark.skip("skip for now until the new aggregate.nc is finished")
def test_get_line_aggregate_netcdf_results(agg_gr):
    assert 'q_max' in agg_gr.netcdf_file.variables.keys()
    assert 'u1_max' in agg_gr.netcdf_file.variables.keys()
    assert hasattr(agg_gr.lines, 'q_max')
    assert hasattr(agg_gr.lines, 'u1_max')
    assert agg_gr.lines.q_max.shape[0] > 0
    assert agg_gr.lines.u1_max.shape[0] > 0


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
