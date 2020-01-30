import json
import logging
from collections import OrderedDict

import geojson
import numpy as np
import six

from threedigrid.admin import constants
from threedigrid.orm.base.encoder import NumpyEncoder
from threedigrid.orm.base.models import Model


logger = logging.getLogger(__name__)


class GeoJsonSerializer:
    def __init__(
            self,
            fields,
            model: Model = None,
            indent: int = None,
    ):
        self.fields = fields
        if model:
            assert isinstance(model, Model)
        self._model = model
        self._indent = indent

    def save(self, filename, **kwargs):
        with open(filename, 'w') as file:
            json.dump(
                {'type': 'FeatureCollection', 'features': self.geos},
                file,
                indent=self._indent,
                cls=NumpyEncoder
            )

    @property
    def geos(self):
        geos = []
        if self._model.count == 0:
            return geos
        data = self._model.to_dict()
        if self._model.__contenttype__() in ('lines',):
            for i in range(data['id'].shape[-1]):
                p1, p2 = np.round(
                    data['line_coords'][:, i].reshape((2, -1)), constants.LONLAT_DIGITS
                )
                line = geojson.LineString([(p1[0], p1[1]), (p2[0], p2[1])])
                properties = fill_properties(self.fields, data, i)
                feat = geojson.Feature(
                    geometry=line,
                    properties=properties,
                )
                geos.append(feat)
        elif self._model.__contenttype__() in ('nodes', 'cells', 'breaches', 'pumps'):
            for i in range(data['id'].shape[-1]):
                coords = np.round(data['coordinates'][:, i], constants.LONLAT_DIGITS)
                point = geojson.Point([coords[0], coords[1]])
                properties = fill_properties(self.fields, data, i)
                feat = geojson.Feature(
                    geometry=point,
                    properties=properties,
                )
                geos.append(feat)
        elif self._model.__contenttype__() == 'levees':
            for i in range(data['id'].shape[-1]):
                coords = np.round(
                    data['coords'][i].reshape(2, -1),
                    constants.LONLAT_DIGITS
                ).T
                line = geojson.LineString(coords.tolist())
                properties = fill_properties(self.fields, data, i)
                feat = geojson.Feature(
                    geometry=line,
                    properties=properties,
                )
                geos.append(feat)
        else:
            raise ValueError("Unknown content type for %s" % self._model)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps({
            'type': 'FeatureCollection',
            'features': geos,
        }, indent=self._indent, cls=NumpyEncoder)


def fill_properties(fields: list, data: dict, index: int) -> OrderedDict:
    """Returns a dict containing the keys from `fields` filled from `data` at `index`"""
    result = OrderedDict()
    for i, field in enumerate(fields):
        if isinstance(field, dict):
            for key, sub_list in field.items():
                result[key] = fill_properties(sub_list, data, index)
        else:
            field_data = data.get(field, None)
            if field_data is not None:
                value = field_data[..., index]
                if value.size == 1:
                    value = value.item()
            else:
                if index == 0:
                    # only log it once
                    logger.warning("missing field %s" % field)
                value = None
            result[field] = value
    return result
