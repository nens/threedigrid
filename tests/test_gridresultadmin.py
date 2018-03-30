from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import pytest

import unittest
import tempfile
import shutil

import numpy as np
import ogr

from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.nodes.exporters import CellsOgrExporter
from threedigrid.admin.nodes.exporters import NodesOgrExporter
from threedigrid.admin.lines.exporters import LinesOgrExporter
from threedigrid.admin.breaches.exporters import BreachesOgrExporter
from threedigrid.admin.constants import SUBSET_1D_ALL
from threedigrid.admin.constants import SUBSET_2D_OPEN_WATER
from threedigrid.admin.constants import NO_DATA_VALUE

from threedigrid.admin.gridresultadmin import GridH5ResultAdmin

test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
result_file = os.path.join(test_file_dir, "subgrid_map.nc")
grid_file = os.path.join(test_file_dir, "gridadmin.h5")


def test_nodes_timeseries_index_filter():

    gr = GridH5ResultAdmin(grid_file, result_file)
    qs_s1 = gr.nodes.timeseries(indexes=[1, 2, 3]).s1
    assert qs_s1.shape[0] == 3


def test_nodes_timeseries_slice_filter():

    gr = GridH5ResultAdmin(grid_file, result_file)
    qs_s1 = gr.nodes.timeseries(indexes=slice(1, 4)).s1
    assert qs_s1.shape[0] == 3


def test_lines_timeseries_index_filter():

    gr = GridH5ResultAdmin(grid_file, result_file)
    qs_u1 = gr.lines.timeseries(indexes=[1, 2, 3, 4, 5]).u1
    assert qs_u1.shape[0] == 5


def test_lines_timeseries_slice_filter():

    gr = GridH5ResultAdmin(grid_file, result_file)
    qs_u1 = gr.lines.timeseries(indexes=slice(1, 4)).u1
    assert qs_u1.shape[0] == 3


def test_set_timeseries_chunk_size():
    gr = GridH5ResultAdmin(grid_file, result_file)
    # default should be 10
    assert gr.timeseries_chunk_size == 10
    gr.set_timeseries_chunk_size(15)
    assert gr.timeseries_chunk_size == 15


def test_set_timeseries_chunk_size_raises_value_error():
    gr = GridH5ResultAdmin(grid_file, result_file)
    # default should be 10
    with pytest.raises(ValueError):
        gr.set_timeseries_chunk_size(0)

    with pytest.raises(ValueError):
        gr.set_timeseries_chunk_size(-5)

    with pytest.raises(ValueError):
        gr.set_timeseries_chunk_size('20.5')
