import json
import logging
from collections import OrderedDict

import numpy as np

from threedigrid.admin import constants
from threedigrid.geo_utils import raise_import_exception, transform_bbox, transform_xys
from threedigrid.orm.base.encoder import NumpyEncoder
from threedigrid.orm.base.models import Model

try:
    import geojson
except ImportError:
    geojson = None


logger = logging.getLogger(__name__)


class GeoJsonSerializer:
    def __init__(self, fields, model=None, indent=None, coupled_model=None):
        if geojson is None:
            raise_import_exception("geojson")
        if model:
            assert isinstance(model, Model)
        if coupled_model:
            assert isinstance(coupled_model, Model)

        self.fields = fields
        self._coupled_model = coupled_model
        self._model = model
        self._indent = indent

    def save(self, filename, **kwargs):
        with open(filename, "w") as file:
            file.write('{"type": "FeatureCollection", "features": [')
            first = True
            for geo in self.geos_iter():
                if not first:
                    file.write(", ")
                else:
                    first = False
                json.dump(
                    geo, file, indent=self._indent, allow_nan=False, cls=NumpyEncoder
                )
            file.write("]}")

    def geos_iter(self):
        if self._model.count == 0:
            return []

        # Get the data, skipping the dummy element
        data = self._model.filter(id__ne=0).to_dict()
        content_type = self._model.__contenttype__()
        model_type = type(self._model).__name__
        if content_type == "lines":
            for i in range(data["id"].shape[-1]):
                linepoints = np.round(
                    data["line_geometries"][i].reshape(2, -1).T.astype("float64"),
                    constants.LONLAT_DIGITS,
                )
                line = geojson.LineString(linepoints.tolist())
                properties = fill_properties(self.fields, data, i, model_type)
                self._set_tabulated_cross_section_information(data, i, properties)
                yield geojson.Feature(geometry=line, properties=properties)
        elif content_type == "nodes":
            for i in range(data["id"].shape[-1]):
                coords = np.round(data["coordinates"][:, i], constants.LONLAT_DIGITS)
                point = geojson.Point([coords[0], coords[1]])
                properties = fill_properties(self.fields, data, i, model_type)
                yield geojson.Feature(geometry=point, properties=properties)
        elif content_type == "pumps":
            for i in range(data["id"].shape[-1]):
                # Pump is defined on start node, add line geom if end node is defined
                coords = np.round(
                    data["node_coordinates"][:, i], constants.LONLAT_DIGITS
                )
                geometry = geojson.Point([coords[0], coords[1]])
                properties = fill_properties(self.fields, data, i, model_type)
                if data["node2_id"][i] != -9999:
                    line_geometry = geojson.LineString(coords.tolist())
                    properties["line_geometry"] = line_geometry
                yield geojson.Feature(geometry=geometry, properties=properties)
        elif content_type == "breaches":
            for i in range(data["id"].shape[-1]):
                linepoints = np.round(
                    data["line_geometries"][i].reshape(2, -1).T.astype("float64"),
                    constants.LONLAT_DIGITS,
                )
                line = geojson.LineString(linepoints.tolist())
                properties = fill_properties(self.fields, data, i, model_type)
                properties["levl"] = self._coupled_model.dpumax[data["levl"][i]]
                yield geojson.Feature(geometry=line, properties=properties)
        elif content_type == "cells":
            if (
                self._model.reproject_to_epsg is not None
                and self._model.reproject_to_epsg != self._model.epsg_code
            ):
                cell_coords = transform_bbox(
                    self._model.reproject_to(self._model.epsg_code).cell_coords,
                    self._model.epsg_code,
                    self._model.reproject_to_epsg,
                    all_coords=True,
                )
            else:
                cell_coords = np.array(
                    [
                        data.get("cell_coords")[0],
                        data.get("cell_coords")[3],
                        data.get("cell_coords")[2],
                        data.get("cell_coords")[3],
                        data.get("cell_coords")[2],
                        data.get("cell_coords")[1],
                        data.get("cell_coords")[0],
                        data.get("cell_coords")[1],
                    ]
                )
            cell_coords = np.round(cell_coords, constants.LONLAT_DIGITS)
            for i in range(data["id"].shape[-1]):
                left_top = (cell_coords[0][i], cell_coords[1][i])
                right_top = (cell_coords[2][i], cell_coords[3][i])
                right_bottom = (cell_coords[4][i], cell_coords[5][i])
                left_bottom = (cell_coords[6][i], cell_coords[7][i])
                polygon = geojson.Polygon(
                    [(left_top, right_top, right_bottom, left_bottom, left_top)]
                )
                properties = fill_properties(self.fields, data, i, model_type)
                yield geojson.Feature(geometry=polygon, properties=properties)
        elif content_type == "fragments":
            for i in range(data["id"].shape[-1]):
                coords = np.round(
                    data["coords"][i].reshape(2, -1).astype("float64"),
                    constants.LONLAT_DIGITS,
                )
                if (
                    self._model.reproject_to_epsg is not None
                    and self._model.reproject_to_epsg != self._model.epsg_code
                ):
                    # Pick reproject_to_epsg or original model epsg_code
                    coords = transform_xys(
                        np.array(coords[0]),
                        np.array(coords[1]),
                        self._model.epsg_code,
                        self._model.reproject_to_epsg,
                    )
                polygon = geojson.Polygon(coords.T.tolist())
                properties = fill_properties(self.fields, data, i, model_type)
                yield geojson.Feature(geometry=polygon, properties=properties)
        elif content_type == "levees":
            for i in range(data["id"].shape[-1]):
                coords = np.round(
                    data["coords"][i].reshape(2, -1).astype("float64"),
                    constants.LONLAT_DIGITS,
                )
                line = geojson.LineString(coords.T.tolist())
                properties = fill_properties(self.fields, data, i, model_type)
                yield geojson.Feature(geometry=line, properties=properties)
        else:
            raise ValueError("Unknown content type for %s" % self._model)

    @property
    def geos(self):
        return [x for x in self.geos_iter()]

    @property
    def data(self):
        geos = self.geos
        return json.dumps(
            {"type": "FeatureCollection", "features": geos},
            indent=self._indent,
            cls=NumpyEncoder,
        )

    def _set_tabulated_cross_section_information(self, lines_data, i, properties):
        """Add cross section information to line properties

        Args:
            line_data (Dict): lines data
            i (int): index into the lines data
            properties (Dict): to be exported line data
        """
        from threedigrid.admin.crosssections.models import CrossSections

        if isinstance(self._coupled_model, CrossSections):
            try:
                cross1 = lines_data["cross1"][i]
                (
                    width,
                    height,
                ) = self._coupled_model.get_tabulated_cross_section_height_and_width(
                    cross1
                )
                properties["cross_section_type_1"] = self._coupled_model.shape[cross1]
                properties["cross_section_table_1"] = [width, height]
                properties["cross_section_weight"] = lines_data["cross_weight"][i]
            except IndexError:
                properties["cross_section_type_1"] = None
                properties["cross_section_table_1"] = [[], []]
                properties["cross_section_weight"] = None

            try:
                cross2 = lines_data["cross2"][i]
                (
                    width,
                    height,
                ) = self._coupled_model.get_tabulated_cross_section_height_and_width(
                    cross2
                )
                properties["cross_section_type_2"] = self._coupled_model.shape[cross2]
                properties["cross_section_table_2"] = [width, height]
            except IndexError:
                properties["cross_section_type_2"] = None
                properties["cross_section_table_2"] = [[], []]


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
    for field in fields:
        if isinstance(field, dict):
            for key, sub_list in field.items():
                result[key] = fill_properties(sub_list, data, index)
        else:
            field_data = data.get(field, None)
            if field_data is not None and field_data.size > 0:
                if field == "line_geometries" and len(field_data.shape) > 1:
                    # Indexing for reprojected line_geometries
                    value = field_data[index]
                else:
                    value = field_data[..., index]
                # Replace NaN, Inf, -Inf, -9999.0 floats with None (null)
                if np.issubdtype(value.dtype, np.floating):
                    is_invalid = (~np.isfinite(value)) | (value == -9999.0)
                else:
                    is_invalid = False
                if np.any(is_invalid):
                    value = np.where(is_invalid, None, value)
                if value.size == 1:
                    value = value.item()
            else:
                if index == 0:
                    # only log it once
                    logger.warning("missing field %s" % field)
                value = None
            result[field] = value

    if model_type:
        result["model_type"] = model_type

    return result
