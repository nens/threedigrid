from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import h5py
import unittest

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
