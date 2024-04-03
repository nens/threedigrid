from unittest import mock

from threedigrid.admin.constants import TYPE_CODE_MAP
from threedigrid.admin.idmapper import IdMapper

from .conftest import NODE_LENGTH, simple_id_map


@mock.patch("threedigrid.admin.idmapper.get_id_map")
def test_prepare_mapper(mocked_id_map, h5py_file, threedi_datasource):
    mocked_id_map.return_value = simple_id_map()
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    # now a mapping should exist on the h5py file
    mapping = h5py_file["mappings"]["id_map"]
    assert mapping
    assert mapping.dtype.names == ("obj_code", "pk", "seq_id")
    assert mapping[:].size == len(TYPE_CODE_MAP.values()) * NODE_LENGTH


@mock.patch("threedigrid.admin.idmapper.get_id_map")
def test_init_idMapper(mocked_id_map, h5py_file, threedi_datasource):
    mocked_id_map.return_value = simple_id_map()
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    mapper = IdMapper(h5py_file["mappings"]["id_map"])
    assert mapper.get_by_code(TYPE_CODE_MAP["v2_channel"]).size == NODE_LENGTH
    assert mapper.get_by_name("v2_channel").size == NODE_LENGTH
