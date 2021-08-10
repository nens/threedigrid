import json
import logging
from collections import OrderedDict

import numpy as np

from threedigrid.admin import constants
from threedigrid.geo_utils import transform_bbox, raise_import_exception
from threedigrid.orm.base.encoder import NumpyEncoder
from threedigrid.orm.base.models import Model

try:
    import geojson
except ImportError:
    geojson = None


logger = logging.getLogger(__name__)


class GeoJsonSerializer:
    def __init__(self, fields, model=None, indent=None):
        if geojson is None:
            raise_import_exception('geojson')
        self.fields = fields
        if model:
            assert isinstance(model, Model)
        self._model = model
        self._indent = indent

    def save(self, filename, **kwargs):
        with open(filename, "w") as file:
            json.dump(
                {"type": "FeatureCollection", "features": self.geos},
                file,
                indent=self._indent,
                allow_nan=False,
                cls=NumpyEncoder,
            )

    @property
    def geos(self):
        geos = []
        if self._model.count == 0:
            return geos
        data = self._model.to_dict()
        content_type = self._model.__contenttype__()
        model_type = type(self._model).__name__
        if content_type == "lines":
            for i in range(data["id"].shape[-1]):
                linepoints = np.round(
                    data['line_geometries'][i].reshape(
                        2, -1).T.astype('float64'),
                    constants.LONLAT_DIGITS
                )
                line = geojson.LineString(linepoints.tolist())

                properties = fill_properties(
                    self.fields, data, i, model_type
                )
                feat = geojson.Feature(geometry=line, properties=properties)
                geos.append(feat)
        elif content_type in ("nodes", "breaches", "pumps"):
            for i in range(data["id"].shape[-1]):
                coords = np.round(
                    data["coordinates"][:, i], constants.LONLAT_DIGITS
                )
                point = geojson.Point([coords[0], coords[1]])
                properties = fill_properties(
                    self.fields, data, i, model_type
                )
                feat = geojson.Feature(geometry=point, properties=properties)
                geos.append(feat)
        elif content_type == "cells":
            if (self._model.reproject_to_epsg is not None and
                    self._model.reproject_to_epsg != self._model.epsg_code):
                cell_coords = transform_bbox(
                    self._model.reproject_to(
                        self._model.epsg_code
                    ).cell_coords,
                    self._model.epsg_code, self._model.reproject_to_epsg,
                    all_coords=True
                )
            else:
                cell_coords = np.array([
                    data.get('cell_coords')[0], data.get('cell_coords')[3],
                    data.get('cell_coords')[2], data.get('cell_coords')[3],
                    data.get('cell_coords')[2], data.get('cell_coords')[1],
                    data.get('cell_coords')[0], data.get('cell_coords')[1],
                ])
            cell_coords = np.round(cell_coords, constants.LONLAT_DIGITS)
            for i in range(data["id"].shape[-1]):
                left_top = (cell_coords[0][i], cell_coords[1][i])
                right_top = (cell_coords[2][i], cell_coords[3][i])
                right_bottom = (cell_coords[4][i], cell_coords[5][i])
                left_bottom = (cell_coords[6][i], cell_coords[7][i])
                polygon = geojson.Polygon([
                    (left_top, right_top, right_bottom, left_bottom, left_top)
                ])
                properties = fill_properties(
                    self.fields, data, i, model_type
                )
                feat = geojson.Feature(geometry=polygon, properties=properties)
                geos.append(feat)
        elif content_type == "levees":
            for i in range(data["id"].shape[-1]):
                coords = np.round(
                    data["coords"][i].reshape(2, -1).astype('float64'),
                    constants.LONLAT_DIGITS
                )
                line = geojson.LineString(zip(coords[1, :], coords[0, :]))
                properties = fill_properties(
                    self.fields, data, i, model_type
                )
                feat = geojson.Feature(geometry=line, properties=properties)
                geos.append(feat)
        else:
            raise ValueError("Unknown content type for %s" % self._model)

        return geos

    @property
    def data(self):
        geos = self.geos
        return json.dumps(
            {"type": "FeatureCollection", "features": geos},
            indent=self._indent,
            cls=NumpyEncoder,
        )


def fill_properties(fields, data, index, model_type=None):
    """Returns a dict containing the keys from `fields` filled from `data`
    at `index`

    :param fields: (list) list of keys (str) to extract from data. The keys
        can can also be a dict, in which case fill_properties will be called
        on its items.
    :param data: (dict) the original data
    :param index: (int) index value to extract from data
    :param model_type: (str, optional) optionally adds the given model_type
    """
    result = OrderedDict()
    for i, field in enumerate(fields):
        if isinstance(field, dict):
            for key, sub_list in field.items():
                result[key] = fill_properties(sub_list, data, index)
        else:
            field_data = data.get(field, None)
            if field_data is not None and field_data.size > 0:
                value = field_data[..., index]
                if value.size == 1:
                    value = value.item()
                try:
                    if ~np.any(np.isfinite(value)):
                        return None
                except TypeError:  # for e.g. strings
                    pass
            else:
                if index == 0:
                    # only log it once
                    logger.warning("missing field %s" % field)
                value = None
            result[field] = value

    if model_type:
        result['model_type'] = model_type

    return result
