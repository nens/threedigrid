from itertools import count
import os
import shutil
import sys

import h5py
if sys.version_info >= (3, 3):  # noqa
    from unittest import mock
else:
    import mock
import pytest
import six

from threedigrid.admin.constants import TYPE_CODE_MAP
from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedigrid.admin.idmapper import IdMapper


test_file_dir = os.path.join(
    os.path.dirname(__file__), "test_files")

grid_bck = os.path.join(test_file_dir, "gridadmin.bck")

# the testfile is a copy of the v2_bergermeer gridadmin file
result_file = os.path.join(test_file_dir, "results_3di.nc")
grid_file = os.path.join(test_file_dir, "gridadmin.h5")


NODE_LENGTH = 10


@pytest.fixture()
def gr():
    gr = GridH5ResultAdmin(grid_file, result_file)
    yield gr
    gr.close()


def simple_id_map(node_length=NODE_LENGTH):
    """Return a simple mapping

    NODE_LENGTH nodes are created for each TYPE_CODE, each mapping to an ever
    increasing sequence number"""
    sequence_id_generator = count(start=1, step=1)
    id_map = {}
    for code in TYPE_CODE_MAP.values():
        pk_generator = range(1, 1+node_length)
        id_map[code] = dict(zip(pk_generator, sequence_id_generator))
    return id_map


@pytest.fixture
def empty_hdf5_file(tmpdir):
    """Create an empty hdf5 file"""
    hdf5_file_name = six.text_type(tmpdir.join('gridadmin.h5'))
    with h5py.File(hdf5_file_name, 'w') as h5py_file:
        yield h5py_file


@pytest.fixture
def h5py_file(tmpdir):
    """Copy and open an unprepared h5py file, based on gridadmin.bck"""
    tmp_file = six.text_type(tmpdir.join('gridadmin.h5'))
    shutil.copyfile(grid_bck, tmp_file)
    with h5py.File(tmp_file, 'r+') as h5py_file:
        yield h5py_file


@pytest.fixture
def threedi_datasource():
    """Mocks a threedi_datasource"""
    m = mock.MagicMock()
    return m


@pytest.fixture
@mock.patch('threedigrid.admin.idmapper.get_id_map')
def h5py_file_mapper(mocked_id_map, h5py_file, threedi_datasource):
    """Unprepared h5py file with a prepared id_mapper"""
    id_map = simple_id_map()
    mocked_id_map.return_value = id_map
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    return h5py_file, threedi_datasource
