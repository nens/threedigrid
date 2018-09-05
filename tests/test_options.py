# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import pytest

from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedigrid.admin.nodes.models import Nodes
from threedigrid.orm.base.fields import TimeSeriesCompositeArrayField

from threedigrid.orm.base.options import Options

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


@pytest.fixture()
def opt_nodes(gr):
    opt = Options(gr.nodes)
    yield opt


@pytest.fixture()
def opt_lines(gr):
    opt = Options(gr.lines)
    yield opt


@pytest.fixture()
def opt_breaches(gr):
    opt = Options(gr.breaches)
    yield opt


@pytest.fixture()
def opt_pumps(gr):
    opt = Options(gr.pumps)
    yield opt


def test_options_nodes(opt_nodes):
    assert isinstance(opt_nodes.inst, Nodes)


def test_options_get_field(opt_lines):
    field = opt_lines.get_field('au')
    assert isinstance(field, TimeSeriesCompositeArrayField)


def test_breach_options_get_fields(opt_breaches):
    fields = opt_breaches.get_fields()
    assert set(fields.keys()) == {
        'levbr', 'breach_width', 'levl', 'breach_depth',
        'coordinates', 'kcu', 'levmat', 'seq_ids', 'content_pk', 'id'}


def test_pump_options_get_fields_only_names(opt_pumps):
    fields = opt_pumps.get_fields(only_names=True)

    assert set(fields) == {
        'zoom_category', 'bottom_level', 'display_name', 'lower_stop_level',
        'node_coordinates', 'coordinates', 'start_level', 'q_pump',
        'capacity', 'id', 'node2_id', 'node1_id'}


def test_nodes_options_get_composite_meta(opt_nodes):
    assert opt_nodes._get_composite_meta('s1', 'units') == b'm'


def test_lines_options_get_meta_values(opt_lines):
    v = opt_lines._get_meta_values('q')
    assert set(v.get('q')) == {None, b'Discharge on flow line', b'm3 s-1'}


def test_smoke_looup_idx(opt_nodes):
    idx = opt_nodes._get_lookup_index()
    assert len(idx.shape) == 1 and idx.size > 0
