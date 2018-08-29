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
from threedigrid.admin.breaches.serializers import BreachesGeoJsonSerializer
from threedigrid.admin.nodes.serializers import ManholesGeoJsonSerializer
from threedigrid.admin.pumps.serializers import PumpsGeoJsonSerializer

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
        self.assertGreater(channels_wgs84.id.size, 0)
        self.assertEqual(len(feat), channels_wgs84.id.size)
        self.assertEqual(feat[0]['properties']['object_type'], 'v2_channel')

    def test_weir_serializer(self):
        weirs = self.parser.lines.weirs.subset('1D_ALL').reproject_to('4326')
        wjson = WeirsGeoJsonSerializer(weirs).data
        j = json.loads(wjson)
        feat = j['features']
        self.assertGreater(weirs.id.size, 0)
        self.assertEqual(len(feat), weirs.id.size)
        self.assertEqual(feat[0]['properties']['object_type'], 'v2_weir')

    def test_breach_serializer(self):
        breaches = self.parser.breaches.filter(kcu=55).reproject_to('4326')
        bjson = BreachesGeoJsonSerializer(breaches).data
        j = json.loads(bjson)
        feat = j['features']
        self.assertGreater(breaches.id.size, 0)
        self.assertEqual(len(feat), breaches.id.size)
        self.assertEqual(feat[0]['properties']['object_type'], 'v2_breach')

    def test_manhole_serializer(self):
        manholes = self.parser.nodes.manholes.subset(
            '1D_ALL').reproject_to('4326')
        mjson = ManholesGeoJsonSerializer(manholes).data
        j = json.loads(mjson)
        feat = j['features']
        self.assertGreater(manholes.id.size, 0)
        self.assertEqual(len(feat), manholes.id.size)
        self.assertEqual(
            feat[0]['properties']['object_type'], 'v2_connection_nodes')

    def test_pump_serializer(self):
        pumps = self.parser.pumps.reproject_to('4326')
        pjson = PumpsGeoJsonSerializer(pumps).data
        j = json.loads(pjson)
        feat = j['features']
        self.assertGreater(pumps.id.size, 0)
        self.assertEqual(len(feat), pumps.id.size)
        self.assertEqual(
            feat[0]['properties']['object_type'], 'v2_pumpstation')
