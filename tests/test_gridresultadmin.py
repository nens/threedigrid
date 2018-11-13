from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import pytest

import numpy as np


from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedigrid.admin.nodes.models import Nodes


test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
result_file = os.path.join(test_file_dir, "results_3di.nc")
grid_file = os.path.join(test_file_dir, "gridadmin.h5")


@pytest.fixture()
def gr():
    gr = GridH5ResultAdmin(grid_file, result_file)
    yield gr
    gr.close()

def test_fieldnames_nodes(gr):
    assert set(gr.nodes._field_names) == {
        'cell_coords', 'content_pk', 'coordinates', 'id',
        u'intercepted_volume', 'is_manhole', u'leak', 'node_type', u'q_lat',
        u'rain', u's1', 'seq_id', u'su', u'ucx', u'ucy', u'vol',
        'zoom_category',
    }

def test_fieldnames_lines(gr):
    assert set(gr.lines._field_names) == {
        u'au', 'content_pk', 'content_type', 'id', 'kcu', 'lik', 'line',
        'line_coords', 'line_geometries', u'q', u'u1', 'zoom_category',
    }

def test_fieldnames_pumps(gr):
    assert set(gr.pumps._field_names) == {
        'bottom_level', 'capacity', 'coordinates', 'display_name', 'id',
        'lower_stop_level', 'node1_id', 'node2_id', 'node_coordinates',
        u'q_pump', 'start_level', 'zoom_category',
    }

def test_composite_fields_nodes(gr):
    assert set(gr.nodes.Meta.composite_fields.keys()) == {
        u'_mesh_id', u'q_lat', u'rain', u's1', u'su', u'vol'
    }

def test_composite_fields_lines(gr):
    assert set(gr.lines.Meta.composite_fields.keys()) == {
        u'_mesh_id', u'au', u'q', u'qp', u'u1', u'up1',
    }

def test_composite_fields_pumps(gr):
    assert set(gr.pumps.Meta.composite_fields.keys()) == {
        u'_mesh_id', u'q_pump',
    }

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


# TODO: fix this (Add breach to new testdata)
@pytest.mark.skip("test succeeded with previous testdata, but skip for now, "
               "because of new testdata (with breaches")
def test_breach_timeseries_slice_filter(gr):
    qs = gr.breaches.timeseries(indexes=slice(1, 4)).breach_depth
    assert qs.shape[0] == 3


# TODO: fix this (Add breach to new testdata)
@pytest.mark.skip("test succeeded with previous testdata, but skip for now, "
               "because of new testdata (with breaches")
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


# TODO: fix this (jira ticket: THREEDI-578)
@pytest.mark.skip("skipped for now until this KeyError (Cant open attribute "
                  "cant locate attribute: 'threedi_version') "
                  "has been fixed")
def test_get_model_instance_by_field_name(gr):
    inst = gr.get_model_instance_by_field_name('s1')
    assert isinstance(inst, Nodes)


# TODO: fix this (jira ticket: THREEDI-578)
@pytest.mark.skip("skipped for now until this KeyError (Cant open attribute "
                  "cant locate attribute: 'threedi_version') "
                  "has been fixed")
def test_get_model_instance_by_field_name_raises_index_error_unknown_field(gr):
    with pytest.raises(IndexError):
        gr.get_model_instance_by_field_name('unknown_field')


# TODO: fix this (jira ticket: THREEDI-578)
@pytest.mark.skip("skipped for now until this KeyError (Cant open attribute "
                  "cant locate attribute: 'threedi_version') "
                  "has been fixed")
def test_get_model_instance_by_field_name_raises_index_error(gr):
    with pytest.raises(IndexError):
        gr.get_model_instance_by_field_name('zoom_category')


@pytest.mark.skip("skip for now until the new aggregate.nc is finished")
def test_get_node_netcdf_results(gr):
    assert 's1' in gr.netcdf_file.variables.keys()
    assert 'vol' in gr.netcdf_file.variables.keys()
    assert hasattr(gr.nodes, 's1')
    assert hasattr(gr.nodes, 'vol')
    assert gr.nodes.s1.shape[0] > 0
    assert gr.nodes.vol.shape[0] > 0
