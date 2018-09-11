# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import geojson
import json

from threedigrid.admin.utils import _get_storage_area
from threedigrid.admin.nodes.models import AddedCalculationNodes
from threedigrid.admin.nodes.models import ConnectionNodes
from threedigrid.admin.nodes.models import Manholes
from threedigrid.admin import constants
from threedigrid.orm.base.encoder import NumpyEncoder
from six.moves import range


class ManholesGeoJsonSerializer():
    def __init__(self, manholes, indent=None):
        assert isinstance(manholes, Manholes)
        self._manholes = manholes
        self._indent = indent

    @property
    def geos(self):
        selection = self._manholes.to_dict()

        geos = []
        if 'coordinates' not in selection:
            raise ValueError(
                "Can't return data as geojson "
                "for selection without geometries")

        for i in range(selection['id'].shape[-1]):
            pt = geojson.Point(
                [round(x, constants.LONLAT_DIGITS)
                 for x in selection['coordinates'][:, i]])

            area = _get_storage_area(selection['storage_area'][i])

            cn_meta = [
                    ['object_type', constants.TYPE_V2_MANHOLE],
                    ['display_name', selection['display_name'][i]],
                    ['manhole_type', constants.MANHOLE_TYPES.get(
                        selection['manhole_indicator'][i])],
                    ['calculation_type', constants.CALCULATION_TYPES.get(
                        selection['calculation_type'][i])],
                    ['shape', selection['shape'][i]],
                    ['area', area],
                    ['bottom_level', "{0} [m MSL]".format(
                        selection['bottom_level'][i])],
                    ['width', "{0} [m]".format(selection['width'][i])],
                    ['drain_level', "{0} [m]".format(
                        selection['drain_level'][i])],
                    ['surface_level', "{0} [m]".format(
                        selection['surface_level'][i])],
                    ['nod idx', int(selection['id'][i])],
                    ]
            cn_props = dict(
                object_type=constants.TYPE_V2_CONNECTION_NODES,
                zoom_category=selection['zoom_category'][i],
                meta=cn_meta,
                node_idx=int(selection['id'][i])
                )
            feat = geojson.Feature(
                geometry=pt,
                properties=cn_props,
                )
            geos.append(feat)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps({
            'type': 'FeatureCollection',
            'features': geos,
        }, indent=self._indent, cls=NumpyEncoder)


class ConnectionNodesGeoJsonSerializer():
    def __init__(self, connection_nodes=None, data=None, indent=None):
        if connection_nodes:
            assert isinstance(connection_nodes, ConnectionNodes)
        self._data = data
        self._connection_nodes = connection_nodes
        self._indent = indent

    @property
    def geos(self):
        if self._connection_nodes:
            selection = self._connection_nodes.to_dict()
        else:
            selection = self._data

        geos = []
        if 'coordinates' not in selection:
            raise ValueError(
                "Can't return data as geojson "
                "for selection without geometries")

        for i in range(selection['id'].shape[-1]):
            pt = geojson.Point(
                [round(x, constants.LONLAT_DIGITS)
                 for x in selection['coordinates'][:, i]])
            area = _get_storage_area(selection['storage_area'][i])

            cn_meta = [
                    ['object_type', constants.TYPE_V2_CONNECTION_NODES],
                    ['storage area', area],
                    ['initial_waterlevel', "{0} [m MSL]".format(
                        selection['initial_waterlevel'][i])],
                    ['nod idx', int(selection['id'][i])],
                    ]
            cn_props = dict(
                object_type=constants.TYPE_V2_CONNECTION_NODES,
                meta=cn_meta,
                node_idx=int(selection['id'][i])
                )
            feat = geojson.Feature(
                geometry=pt,
                properties=cn_props,
                )
            geos.append(feat)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps({
            'type': 'FeatureCollection',
            'features': geos,
        }, indent=self._indent, cls=NumpyEncoder)


class AddedCalculationNodesGeoJsonSerializer():
    def __init__(self, added_calculationnodes=None, data=None, indent=None):
        if added_calculationnodes:
            assert isinstance(added_calculationnodes, AddedCalculationNodes)
        self._data = data
        self._added_calculationnodes = added_calculationnodes
        self._indent = indent

    @property
    def geos(self):
        if self._added_calculationnodes:
            selection = self._added_calculationnodes.to_dict()
        else:
            selection = self._data

        geos = []
        if 'coordinates' not in selection:
            raise ValueError(
                "Can't return data as geojson "
                "for selection without geometries")

        for i in range(selection['id'].shape[-1]):
            pt = geojson.Point(
                [round(x, constants.LONLAT_DIGITS)
                 for x in selection['coordinates'][:, i]])
            cn_meta = [
                    ['object_type', 'added calculation node'],
                    ['nod idx', int(selection['id'][i])],
                    ]
            cn_props = dict(
                object_type='v2_node',
                meta=cn_meta,
                has_1d2d=True,
                node_idx=int(selection['id'][i]),
                size=0,
                )
            feat = geojson.Feature(
                geometry=pt,

                properties=cn_props,
                )
            geos.append(feat)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps({
            'type': 'FeatureCollection',
            'features': geos,
        }, indent=self._indent, cls=NumpyEncoder)
