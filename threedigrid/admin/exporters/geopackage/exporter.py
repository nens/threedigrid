# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

import logging
import os
from collections import OrderedDict

try:
    from osgeo import ogr
except ImportError:
    ogr = None

from threedigrid.admin import exporter_constants as const
from threedigrid.admin.constants import (
    NODE_1D_FIELDS,
    NODE_BASE_FIELDS,
    NODE_FIELD_NAME_MAP,
)
from threedigrid.geo_utils import get_spatial_reference
from threedigrid.orm.base.exporters import BaseOgrExporter

logger = logging.getLogger(__name__)


def get_geometry(field_name, field_type, data, index):
    geom = ogr.Geometry(const.OGR_GEOM_TYPE_MAP[field_type])

    if field_type == 'point':
        geom.AddPoint(
            data[field_name][0][index], data[field_name][1][index]
        )

    return geom


class OgrExporter(BaseOgrExporter):

    def __init__(self, model):
        """
        :param model: model instance (filtered or not)
        """
        self.model = model
        self.supported_drivers = {
            const.GEO_PACKAGE_DRIVER_NAME,
            const.SHP_DRIVER_NAME,
            const.GEOJSON_DRIVER_NAME,
        }

    def save(self, file_name, layer_name, field_definitions,  **kwargs):
        """
        save to file format specified by the driver, e.g. shapefile

        :param file_name: name of the outputfile
        """

        data = self.model.data

        field_definitions = {
            "id": ("id", "int"),
            "content_pk": ("connection_node_id", "int"),
            "node_type": ("node_type", "int"),
            "calculation_type": ("calculation_type", "int"),
            "is_manhole": ("is_manhole", "int"), # TODO: add bool?
            "coordinates": ("the_geom", "point")
        }


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

        layer = data_source.CreateLayer(layer_name, sr, geomtype)

        for (ogr_field_name, field_type)  in field_definitions.values():
            if field_type in const.OGR_FIELD_TYPE_MAP:
                layer.CreateField(
                    ogr.FieldDefn(ogr_field_name, const.OGR_FIELD_TYPE_MAP[field_type])
                )

        _definition = layer.GetLayerDefn()

        data_source.StartTransaction()

        geom_def = [
            (x, field_definitions[x]) for x in field_definitions if field_definitions[x][0] == 'the_geom']
        
        if geom_def:
            geom_def = geom_def[0]
        else:
            geom_def = None
        

        for i in range(data["id"].size):
            if data["id"][i] == 0:
                continue  # skip the dummy element

            feature = ogr.Feature(_definition)
           
            if geom_def:
                field_name, (ogr_field_name, field_type) = geom_def
                geom = get_geometry(field_name, field_type, data, i)
                feature.SetGeometry(geom)


            for field_name, (ogr_field_name, field_type)  in field_definitions.items():
                if ogr_field_name == 'the_geom':
                    continue
                try:
                    raw_value = data[field_name][i]
                except IndexError:
                    raw_value = None

 
                self.set_field(feature, ogr_field_name, field_type, raw_value)

            layer.CreateFeature(feature)
            feature = None
        data_source.CommitTransaction()
        data_source = None
