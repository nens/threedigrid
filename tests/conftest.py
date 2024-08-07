import os
import shutil
from itertools import count
from unittest import mock

import h5py
import pytest

from threedigrid.admin.constants import TYPE_CODE_MAP
from threedigrid.admin.gridresultadmin import GridH5Admin, GridH5ResultAdmin
from threedigrid.admin.idmapper import IdMapper
from threedigrid.admin.prepare import GridAdminH5Export

test_file_dir = os.path.join(os.path.dirname(__file__), "test_files")

grid_bck = os.path.join(test_file_dir, "gridadmin.bck")

# the testfile is a copy of the v2_bergermeer gridadmin file
result_file = os.path.join(test_file_dir, "results_3di.nc")


NODE_LENGTH = 10


@pytest.fixture(params=["gridadmin.h5"])
def gr(request):
    gr = GridH5ResultAdmin(os.path.join(test_file_dir, request.param), result_file)
    yield gr
    gr.close()


@pytest.fixture(params=["gridadmin.h5"])
def ga(request):
    with GridH5Admin(os.path.join(test_file_dir, request.param)) as ga:
        yield ga


@pytest.fixture
def gr_bergen_with_boundaries():
    """
    Bergermeer including boundaries which results in node_id not to be continous(step 1)
    for `Mesh2D_node_id`
    """
    gr = GridH5ResultAdmin(
        os.path.join(test_file_dir, "bergen_with_boundaries/", "gridadmin.h5"),
        os.path.join(test_file_dir, "bergen_with_boundaries/", "results_3di.nc"),
    )
    yield gr
    gr.close()


@pytest.fixture(params=["gridadmin.h5"])
def ga_export(request, tmp_path):
    exporter = GridAdminH5Export(
        os.path.join(test_file_dir, request.param),
        export_method="to_geojson",
    )
    exporter._dest = str(tmp_path)
    yield exporter


def simple_id_map(node_length=NODE_LENGTH):
    """Return a simple mapping

    NODE_LENGTH nodes are created for each TYPE_CODE, each mapping to an ever
    increasing sequence number"""
    sequence_id_generator = count(start=1, step=1)
    id_map = {}
    for code in TYPE_CODE_MAP.values():
        pk_generator = range(1, 1 + node_length)
        id_map[code] = dict(zip(pk_generator, sequence_id_generator))
    return id_map


@pytest.fixture
def empty_hdf5_file(tmpdir):
    """Create an empty hdf5 file"""
    hdf5_file_name = str(tmpdir.join("gridadmin.h5"))
    with h5py.File(hdf5_file_name, "w") as h5py_file:
        yield h5py_file


@pytest.fixture
def h5py_file(tmpdir):
    """Copy and open an unprepared h5py file, based on gridadmin.bck"""
    tmp_file = str(tmpdir.join("gridadmin.h5"))
    shutil.copyfile(grid_bck, tmp_file)
    with h5py.File(tmp_file, "r+") as h5py_file:
        yield h5py_file


@pytest.fixture
def threedi_datasource():
    """Mocks a threedi_datasource"""
    m = mock.MagicMock()
    return m


@pytest.fixture
@mock.patch("threedigrid.admin.idmapper.get_id_map")
def h5py_file_mapper(mocked_id_map, h5py_file, threedi_datasource):
    """Unprepared h5py file with a prepared id_mapper"""
    id_map = simple_id_map()
    mocked_id_map.return_value = id_map
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    return h5py_file, threedi_datasource
