# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np
import geojson
import json
from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin import constants
from threedigrid.orm.base.encoder import NumpyEncoder
from six.moves import range


class BreachesGeoJsonSerializer():
    def __init__(self, breaches=None, data=None, indent=None):
        if breaches:
            assert isinstance(breaches, Breaches)
        self._data = data
        self._breaches = breaches
        self._indent = indent

    @property
    def geos(self):
        if self._breaches:
            selection = self._breaches.to_dict()
        else:
            selection = self._data

        geos = []
        if 'coordinates' not in selection:
            raise ValueError(
                "Can't return data as geojson "
                "for selection without geometries")
        for i in range(selection['id'].shape[-1]):
            pt = geojson.Point(
                    np.round(
                        selection['coordinates'][:, i],
                        constants.LONLAT_DIGITS).tolist())
            breach_meta = [
                    ['object_type', constants.TYPE_V2_BREACH],
                    ['line_idx', int(selection['levl'][i])],
                    ['breach_idx', int(selection['id'][i])],
                    ]
            breach_props = dict(
                object_type=constants.TYPE_V2_BREACH,
                props={},
                line_idx=int(selection['levl'][i]),
                breach_idx=int(selection['id'][i]),
                meta=breach_meta,
                )
            feat = geojson.Feature(
                geometry=pt,
                properties=breach_props,
                )
            geos.append(feat)

        return geos

    @property
    def data(self):
        return json.dumps({
            'type': 'FeatureCollection',
            'features': self.geos,
        }, indent=self._indent, cls=NumpyEncoder)
