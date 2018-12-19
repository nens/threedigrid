import os
import shutil
import sys
from itertools import count

import h5py
if sys.version_info >= (3, 3):  # noqa
    from unittest import mock
else:
    import mock
import pytest
import six

from threedigrid.admin.idmapper import IdMapper
from threedigrid.admin.prepare import GridAdminH5Prepare
from threedigrid.admin.prepare import is_prepared
from threedigrid.admin.constants import TYPE_CODE_MAP


test_file_dir = os.path.join(
    os.path.dirname(__file__), "test_files")

grid_bck = os.path.join(test_file_dir, "gridadmin.bck")


NODE_LENGTH = 10


@pytest.fixture
def h5py_file(tmpdir):
    """Copy and open an unprepared h5py file"""
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
def id_mapper(node_length=NODE_LENGTH):
    """Return a simple mapping"""
    sequence_id_generator = count(start=1, step=1)
    id_map = {}
    for code in TYPE_CODE_MAP.values():
        pk_generator = range(1, 1+node_length)
        id_map[code] = dict(zip(pk_generator, sequence_id_generator))
    return id_map


@mock.patch('threedigrid.admin.idmapper.get_id_map')
def test_prepare_mapper(m_id_map, h5py_file, threedi_datasource, id_mapper):
    m_id_map.return_value = id_mapper
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    mapping = h5py_file['mappings']['id_map']
    assert mapping
    assert mapping.dtype.names == ('obj_code', 'pk', 'seq_id')
    assert mapping[:].size == len(TYPE_CODE_MAP.values()) * NODE_LENGTH


@mock.patch('threedigrid.admin.idmapper.get_id_map')
def test_init_IdMapper(m_id_map, h5py_file, threedi_datasource, id_mapper):
    m_id_map.return_value = id_mapper
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    mapper = IdMapper(h5py_file['mappings']['id_map'])
    assert mapper.get_by_code(2).size == NODE_LENGTH
    assert mapper.get_by_name('v2_channel').size == NODE_LENGTH


def test_prepare_onedee_lines(h5py_file, threedi_datasource):
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    GridAdminH5Prepare.prepare_onedee_lines(h5py_file, threedi_datasource)
    assert h5py_file['lines']['code'].dtype == 'S100'
    assert h5py_file['lines']['display_name'].dtype == 'S255'
    assert is_prepared(h5py_file, 'lines', 'lines_prepared')


def test_prepare_lines(h5py_file, threedi_datasource):
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    GridAdminH5Prepare.prepare_lines(h5py_file, threedi_datasource)
    assert is_prepared(h5py_file, 'lines', 'lines_prepared')


@mock.patch('threedigrid.admin.idmapper.get_id_map')
def test_prepare(m_id_map, h5py_file, threedi_datasource, id_mapper):
    # breaches fix
    id_mapper[13] = {0: 1}
    m_id_map.return_value = id_mapper
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    GridAdminH5Prepare.prepare(h5py_file, threedi_datasource)
    assert is_prepared(h5py_file, 'lines', 'lines_prepared')
    assert is_prepared(h5py_file, 'nodes', 'prepared')
    assert is_prepared(h5py_file, 'pumps', 'prepared')
    assert is_prepared(h5py_file, 'levees', 'prepared')
    assert is_prepared(h5py_file, 'breaches', 'prepared')
