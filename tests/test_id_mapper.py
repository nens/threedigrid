from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from itertools import count
import os
import sys
import unittest

import h5py
if sys.version_info >= (3, 3):  # noqa
    from unittest import mock
else:
    import mock
import numpy as np

from threedigrid.admin.idmapper import IdMapper
from threedigrid.admin.h5py_datasource import H5pyGroup
from threedigrid.admin.constants import TYPE_CODE_MAP

test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
grid_file = os.path.join(test_file_dir, "gridadmin.h5")


class TestIdMapperByCode(unittest.TestCase):

    def setUp(self):
        h5py_file = h5py.File(grid_file, 'r')
        self.id_mapper = IdMapper(H5pyGroup(h5py_file, 'mappings')['id_map'])

    def test_get_channels_by_code(self):
        tc = TYPE_CODE_MAP['v2_channel']
        qs = self.id_mapper.get_by_code(tc)
        assert np.all(qs['obj_code'] == tc)

    def test_get_culvert_by_code(self):
        tc = TYPE_CODE_MAP['v2_culvert']
        qs = self.id_mapper.get_by_code(tc)
        assert np.all(qs['obj_code'] == tc)


class TestIdMapperByName(unittest.TestCase):
    def setUp(self):
        h5py_file = h5py.File(grid_file, 'r')
        self.id_mapper = IdMapper(H5pyGroup(h5py_file, 'mappings')['id_map'])

    def test_get_channels_by_code(self):
        tc = TYPE_CODE_MAP['v2_channel']
        qs = self.id_mapper.get_by_name('v2_channel')
        assert np.all(qs['obj_code'] == tc)

    def test_get_culvert_by_code(self):
        tc = TYPE_CODE_MAP['v2_culvert']
        qs = self.id_mapper.get_by_name('v2_culvert')
        assert np.all(qs['obj_code'] == tc)


NODE_LENGTH = 10


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


@mock.patch('threedigrid.admin.idmapper.get_id_map')
def test_prepare_mapper(mocked_id_map, h5py_file, threedi_datasource):
    mocked_id_map.return_value = simple_id_map()
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    # now a mapping should exist on the h5py file
    mapping = h5py_file['mappings']['id_map']
    assert mapping
    assert mapping.dtype.names == ('obj_code', 'pk', 'seq_id')
    assert mapping[:].size == len(TYPE_CODE_MAP.values()) * NODE_LENGTH


@mock.patch('threedigrid.admin.idmapper.get_id_map')
def test_init_idMapper(mocked_id_map, h5py_file, threedi_datasource):
    mocked_id_map.return_value = simple_id_map()
    IdMapper.prepare_mapper(h5py_file, threedi_datasource)
    mapper = IdMapper(h5py_file['mappings']['id_map'])
    assert mapper.get_by_code(TYPE_CODE_MAP['v2_channel']).size == NODE_LENGTH
    assert mapper.get_by_name('v2_channel').size == NODE_LENGTH
