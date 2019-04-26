import os
import sys

if sys.version_info >= (3, 3):  # noqa
    from unittest import mock
else:
    import mock

from threedigrid.admin.idmapper import IdMapper
from threedigrid.admin.prepare import GridAdminH5Prepare
from threedigrid.admin.prepare import is_prepared
from .conftest import simple_id_map


test_file_dir = os.path.join(
    os.path.dirname(__file__), "test_files")

grid_bck = os.path.join(test_file_dir, "gridadmin.bck")


def test_prepare_onedee_lines(h5py_file, threedi_datasource):
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    GridAdminH5Prepare.prepare_onedee_lines(h5py_file, threedi_datasource)
    # check some special fixed types
    assert h5py_file['lines']['code'].dtype == 'S32'
    assert h5py_file['lines']['display_name'].dtype == 'S64'
    assert is_prepared(h5py_file, 'lines', 'lines_prepared')


def test_prepare_lines(h5py_file, threedi_datasource):
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    GridAdminH5Prepare.prepare_lines(h5py_file, threedi_datasource)
    assert is_prepared(h5py_file, 'lines', 'lines_prepared')


def test_prepare_onedee_nodes(h5py_file_mapper):
    h5py_file, threedi_datasource = h5py_file_mapper
    GridAdminH5Prepare.prepare_onedee_nodes(h5py_file, threedi_datasource)
    assert is_prepared(h5py_file, 'nodes', 'connectionnodes_prepared')
    assert is_prepared(h5py_file, 'nodes', 'manholes_prepared')
    connection_nodes_field_names = {'initial_waterlevel', 'storage_area'}
    assert connection_nodes_field_names.issubset(h5py_file['nodes'].keys())


def test_prepare_nodes(h5py_file_mapper):
    h5py_file, threedi_datasource = h5py_file_mapper
    GridAdminH5Prepare.prepare_nodes(h5py_file, threedi_datasource)
    assert is_prepared(h5py_file, 'nodes', 'prepared')
    assert {'id', 'content_pk', 'seq_id', 'coordinates'}.issubset(
        h5py_file['nodes'].keys())


def test_prepare_pumps(h5py_file_mapper):
    h5py_file, threedi_datasource = h5py_file_mapper
    # need to prepare onedee_nodes before we can prepare pumps
    GridAdminH5Prepare.prepare_onedee_nodes(h5py_file, threedi_datasource)
    GridAdminH5Prepare.prepare_pumps(h5py_file, threedi_datasource)
    assert is_prepared(h5py_file, 'pumps', 'prepared')
    pumpstations_field_names = {'display_name', 'start_level',
                                'lower_stop_level', 'capacity',
                                'connection_node_start_pk',
                                'connection_node_end_pk',
                                'zoom_category'
                                }
    assert pumpstations_field_names.issubset(h5py_file['pumps'].keys())


def test_prepare_levees(h5py_file_mapper):
    h5py_file, threedi_datasource = h5py_file_mapper
    GridAdminH5Prepare.prepare_levees(h5py_file, threedi_datasource)
    assert is_prepared(h5py_file, 'levees', 'prepared')
    levees_field_names = {'coords', 'crest_level', 'max_breach_depth', 'id'}
    assert levees_field_names.issubset(h5py_file['levees'].keys())


@mock.patch('threedigrid.admin.idmapper.get_id_map')
def test_prepare_breaches(mocked_id_map, h5py_file, threedi_datasource):
    id_map = simple_id_map()
    id_map[13] = {0: 1, 1: 1, 2: 1}
    mocked_id_map.return_value = id_map
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    GridAdminH5Prepare.prepare_breaches(h5py_file, threedi_datasource)
    assert is_prepared(h5py_file, 'breaches', 'prepared')
    breaches_field_names = {'id', 'seq_ids', 'content_pk', 'kcu',
                            'coordinates'}
    assert breaches_field_names.issubset(h5py_file['breaches'].keys())


@mock.patch('threedigrid.admin.idmapper.get_id_map')
def test_prepare(mocked_id_map, h5py_file, threedi_datasource):
    # breaches fix
    id_map = simple_id_map()
    id_map[13] = {0: 1}
    mocked_id_map.return_value = id_map
    GridAdminH5Prepare.prepare(h5py_file, threedi_datasource)
    assert is_prepared(h5py_file, 'lines', 'lines_prepared')
    assert is_prepared(h5py_file, 'nodes', 'prepared')
    assert is_prepared(h5py_file, 'pumps', 'prepared')
    assert is_prepared(h5py_file, 'levees', 'prepared')
    assert is_prepared(h5py_file, 'breaches', 'prepared')
