# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

import logging
import os

import numpy as np

try:
    from osgeo import ogr
except ImportError:
    ogr = None


from threedigrid.admin import exporter_constants as const
from threedigrid.geo_utils import get_spatial_reference
from threedigrid.orm.base.exporters import BaseOgrExporter

logger = logging.getLogger(__name__)


def get_geometry(field_name, field_type, data, index, **kwargs):
    geom = ogr.Geometry(const.OGR_GEOM_TYPE_MAP[field_type])

    if "__" in field_name:
        data[field_name] = kwargs.get(field_name, np.array([]))

    if field_type == "point":
        geom.AddPoint(data[field_name][0][index], data[field_name][1][index])
    elif field_type == "bbox":
        ring = ogr.Geometry(ogr.wkbLinearRing)
        ring.AddPoint(data[field_name][0][index], data[field_name][1][index])
        ring.AddPoint(data[field_name][2][index], data[field_name][1][index])

        ring.AddPoint(data[field_name][2][index], data[field_name][3][index])

        ring.AddPoint(data[field_name][0][index], data[field_name][3][index])

        ring.AddPoint(data[field_name][0][index], data[field_name][1][index])

        # Create polygon from ring
        geom.AddGeometry(ring)
    elif field_type == "line":
        view = data[field_name].astype("float64")
        # print(data[field_name][:, index], data[field_name][:, index].dtype)
        geom.AddPoint(view[0][index], view[1][index])
        geom.AddPoint(view[2][index], view[3][index])
    elif field_type == "multiline":
        for x, y in data[field_name][index].reshape(2, -1).T:
            geom.AddPoint_2D(x, y)
    else:
        raise Exception("Unknown field_type %s", field_type)
    return geom


def get_field_type(model, field_name):
    if "__" in field_name:
        field_name, _ = field_name.split("__")
    return model._get_field(field_name).type


class GpkgExporter(BaseOgrExporter):
    def __init__(self, model):
        """
        :param model: model instance (filtered or not)
        """
        self.model = model
        self.supported_drivers = {
            const.GEO_PACKAGE_DRIVER_NAME,
        }
        self.set_driver(const.GEO_PACKAGE_DRIVER_NAME)

    def add_meta_data(self, file_name, layer_name):
        """
        Note: assumes self.model to be gridadmin root object.
        """
        meta_data = dict(self.model.h5py_file.attrs.items())

        if os.path.exists(file_name):
            data_source = self.driver.Open(file_name, update=1)
        else:
            data_source = self.driver.CreateDataSource(file_name)

        layer = data_source.CreateLayer(
            layer_name, geom_type=ogr.wkbNone, options=["OVERWRITE=YES"]
        )

        usable_fields = []
        for key in meta_data.keys():
            field_type = type(meta_data[key].tolist())
            value = meta_data[key]

            if field_type == bytes:
                field_type = str
            if field_type == list:
                field_type = str
                value = ",".join([str(x) for x in value])

            if field_type in const.OGR_FIELD_TYPE_MAP:
                usable_fields.append((key, field_type, value))
                field = ogr.FieldDefn(key, const.OGR_FIELD_TYPE_MAP[field_type])
                if field_type in ("str", str):
                    field.SetWidth(2048)
                elif field_type in ("bool", bool):
                    field.SetSubType(ogr.OFSTBoolean)
                layer.CreateField(field)

        _definition = layer.GetLayerDefn()
        data_source.StartTransaction()

        feature = ogr.Feature(_definition)

        for key, field_type, value in usable_fields:
            self.set_field(feature, key, field_type, value)

        layer.CreateFeature(feature)
        data_source.CommitTransaction()
        data_source = None

    def save(
        self, file_name, layer_name, field_definitions, progress_func=None, **kwargs
    ):
        """
        save to file format specified by the driver, e.g. shapefile

        :param file_name: name of the outputfile

        :param kwargs: allows to override what's is used as values, see default.py for an example
        """
        field_map = field_definitions
        data = self.model.data

        total = data["id"].size

        if progress_func:
            progress_func(0, total)

        if self.driver is None:
            self.set_driver(extension=os.path.splitext(file_name)[1])

        assert self.driver is not None
        geomtype = 0

        # Pick reproject_to_epsg or original model epsg_code
        target_epsg_code = self.model.reproject_to_epsg or self.model.epsg_code

        sr = get_spatial_reference(target_epsg_code)

        if os.path.exists(file_name):
            data_source = self.driver.Open(file_name, update=1)
        else:
            data_source = self.driver.CreateDataSource(file_name)

        layer = data_source.CreateLayer(layer_name, sr, geomtype, ["OVERWRITE=YES"])

        for field_name, ogr_field_name in field_map.items():
            if ogr_field_name == "the_geom":
                continue

            field_type = get_field_type(self.model, field_name)

            if field_type in const.OGR_FIELD_TYPE_MAP:
                field = ogr.FieldDefn(
                    ogr_field_name, const.OGR_FIELD_TYPE_MAP[field_type]
                )
                if field_type in ("bool", bool):
                    field.SetSubType(ogr.OFSTBoolean)

                layer.CreateField(field)

            else:
                raise Exception(
                    "Could not find type for %s with type %s", field_name, field_type
                )

        _definition = layer.GetLayerDefn()

        data_source.StartTransaction()

        geom_def = [(x, field_map[x]) for x in field_map if field_map[x] == "the_geom"]

        if geom_def:
            geom_def = geom_def[0]
        else:
            geom_def = None

        for i in range(total):
            if data["id"][i] == 0:
                continue  # skip the dummy element

            feature = ogr.Feature(_definition)

            if geom_def:
                field_name, ogr_field_name = geom_def
                field_type = get_field_type(self.model, field_name)
                geom = get_geometry(field_name, field_type, data, i, **kwargs)
                feature.SetGeometry(geom)

            for field_name, ogr_field_name in field_map.items():
                field_type = get_field_type(self.model, field_name)

                if ogr_field_name == "the_geom":
                    continue

                if "__" in field_name:
                    field_name_split, attribute = field_name.split("__")

                    try:
                        raw_value = data[field_name_split][:, i][int(attribute)]
                    except (IndexError, ValueError):
                        raw_value = kwargs.get(field_name, None)
                else:
                    try:
                        raw_value = data[field_name][i]
                    except IndexError:
                        # Try kwargs else None
                        raw_value = kwargs.get(field_name, None)
                self.set_field(feature, ogr_field_name, field_type, raw_value)

            layer.CreateFeature(feature)
            feature = None
            if progress_func:
                progress_func(i + 1, total)

        data_source.CommitTransaction()
        data_source = None
