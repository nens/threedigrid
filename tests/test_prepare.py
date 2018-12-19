import os
import shutil

import pytest
import h5py
import mock

from threedigrid.admin.idmapper import IdMapper
from threedigrid.admin.prepare import GridAdminH5Prepare
from threedigrid.admin.prepare import is_prepared

from threedigrid.admin import constants
from threedigrid.admin.constants import TYPE_CODE_MAP


test_file_dir = os.path.join(
    os.path.dirname(__file__), "test_files")

grid_bck = os.path.join(test_file_dir, "gridadmin.bck")
spatialite_file = os.path.join(test_file_dir, 'gridadmin.sqlite')


@pytest.fixture
def h5py_file(tmpdir):
    """Create a copy and open an unprepared h5py file"""
    tmp_file = str(tmpdir.join('gridadmin.h5'))
    shutil.copyfile(grid_bck, tmp_file)
    with h5py.File(tmp_file, 'r+') as h5py_file:
        yield h5py_file


@pytest.fixture
def threedi_datasource():
    """Mocks a threedi_datasource"""
    m = mock.MagicMock()
    return m


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
