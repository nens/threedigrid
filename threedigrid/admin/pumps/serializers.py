# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import json
import geojson
from threedigrid.admin.pumps.models import Pumps
from threedigrid.admin import constants


def format_to_str(value, empty_value='--', format_string='%0.2f'):
    """
    Format value with format_string when evaluated as True
    else return the empty value
    """
    if not value:
        return empty_value
    return format_string % value


class PumpsGeoJsonSerializer():
    def __init__(self, pumps=None, data=None, indent=None):
        if pumps:
            assert isinstance(pumps, Pumps)
        self._data = data
        self._pumps = pumps
        self._indent = indent

    @property
    def geos(self):
        if self._pumps:
            selection = self._pumps.to_dict()
        else:
            selection = self._data

        geos = []
        if 'coordinates' not in selection:
            raise ValueError(
                "Can't return data as geojson "
                "for selection without geometries")

        for i in xrange(selection['id'].shape[-1]):
            pt = geojson.Point(
                [round(x, constants.LONLAT_DIGITS)
                 for x in selection['coordinates'][:, i]])
            cn_meta = [
                    ['object_type', constants.TYPE_V2_PUMPSTATION],
                    ['display name', selection['display_name'][i]],
                    ['idx', str(selection['id'][i])],
                    ['start level', '%s [m MSL]' % format_to_str(
                        selection['start_level'][i])],
                    ['lower stop level', '%s [m MSL]' % format_to_str(
                        selection['lower_stop_level'][i])],
                    ['capacity', '%s [L/s]' % format_to_str(
                        selection['capacity'][i] * 1000.0
                        if selection['capacity'][i] else False)],
                    ['bottom level', '%s [m MSL]' % format_to_str(
                        selection['bottom_level'][i])],
                    ['nod1d_a', selection['node1_id'][i]],
                    ['nod1d_b', selection['node2_id'][i]
                        if selection['node2_id'][i] != -9999 else '--'],
                    ]
            cn_props = dict(
                object_type=constants.TYPE_V2_PUMPSTATION,
                meta=cn_meta,
                pump_idx=int(selection['id'][i]),
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
        }, indent=self._indent)
