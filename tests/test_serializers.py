from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import unittest
import json

from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.lines.serializers import ChannelsGeoJsonSerializer
from threedigrid.admin.lines.serializers import WeirsGeoJsonSerializer

test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
grid_admin_h5_file = os.path.join(test_file_dir, "gridadmin.h5")


class GridAdminSerializerTest(unittest.TestCase):

    def setUp(self):
        self.parser = GridH5Admin(grid_admin_h5_file)

    def test_channel_serializer(self):
        channels_wgs84 = self.parser.lines.channels.subset(
            '1D_ALL').reproject_to('4326')
        channels_wgs84_geojson = ChannelsGeoJsonSerializer(channels_wgs84).data
        j = json.loads(channels_wgs84_geojson)
        feat = j['features']
        self.assertEqual(len(feat), channels_wgs84.id.size)
        self.assertEqual(feat[0]['properties']['object_type'], 'v2_channel')

    def test_weir_serializer(self):
        weirs = self.parser.lines.weirs.subset('1D_ALL').reproject_to('4326')
        wjson = WeirsGeoJsonSerializer(weirs).data
        j = json.loads(wjson)
        feat = j['features']
        self.assertEqual(len(feat), weirs.id.size)
        self.assertEqual(feat[0]['properties']['object_type'], 'v2_weir')
