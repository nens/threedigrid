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


class NodesOgrExporter(BaseOgrExporter):
    """
    Exports to ogr formats. You need to set the driver explicitly
    before calling save()
    """

    def __init__(self, nodes):
        """
        :param lines: lines.models.Lines instance
        """
        self._nodes = nodes
        self.supported_drivers = {
            const.GEO_PACKAGE_DRIVER_NAME,
            const.SHP_DRIVER_NAME,
            const.GEOJSON_DRIVER_NAME,
        }

    def save(self, file_name, node_data, target_epsg_code, **kwargs):
        """
        save to file format specified by the driver, e.g. shapefile

        :param file_name: name of the outputfile
        :param node_data: dict of node data
        """
        assert self.driver is not None
        geomtype = 0
        sr = get_spatial_reference(target_epsg_code)
        self.del_datasource(file_name)
        data_source = self.driver.CreateDataSource(file_name)
        layer = data_source.CreateLayer(str(os.path.basename(file_name)), sr, geomtype)
        fields = NODE_BASE_FIELDS
        if self._nodes.has_1d:
            fields.update(NODE_1D_FIELDS)

        for field_name, field_type in fields.items():
            layer.CreateField(
                ogr.FieldDefn(str(field_name), const.OGR_FIELD_TYPE_MAP[field_type])
            )
        _definition = layer.GetLayerDefn()

        for i in range(node_data["id"].size):
            if node_data["id"][i] == 0:
                continue  # skip the dummy element
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(
                node_data["coordinates"][0][i], node_data["coordinates"][1][i]
            )
            feature = ogr.Feature(_definition)
            feature.SetGeometry(point)
            for field_name, field_type in fields.items():
                fname = NODE_FIELD_NAME_MAP[field_name]
                try:
                    raw_value = node_data[fname][i]
                except IndexError:
                    raw_value = None
                self.set_field(feature, field_name, field_type, raw_value)
            layer.CreateFeature(feature)


class CellsOgrExporter(BaseOgrExporter):
    """
    Exports to ogr formats. You need to set the driver explicitly
    before calling save()
    """

    def __init__(self, cells):
        """
        :param lines: lines.models.Lines instance
        """
        self._cells = cells
        self.supported_drivers = {
            const.GEO_PACKAGE_DRIVER_NAME,
            const.SHP_DRIVER_NAME,
        }
        self.driver = None

    def save(self, file_name, cells_data, target_epsg_code, **kwargs):
        """
        save to file format specified by the driver, e.g. shapefile

        :param file_name: name of the outputfile
        :param cells_data: dict of cell data
        """
        assert self.driver is not None

        geomtype = 0
        sr = get_spatial_reference(target_epsg_code)

        self.del_datasource(file_name)
        data_source = self.driver.CreateDataSource(file_name)
        layer = data_source.CreateLayer(str(os.path.basename(file_name)), sr, geomtype)
        fields = OrderedDict(
            [
                ("nod_id", "int"),
                ("bottom_lev", "float"),
            ]
        )
        for field_name, field_type in fields.items():
            layer.CreateField(
                ogr.FieldDefn(str(field_name), const.OGR_FIELD_TYPE_MAP[field_type])
            )

        _definition = layer.GetLayerDefn()
        for i in range(cells_data["id"].size):
            if cells_data["id"][i] == 0:
                continue  # skip the dummy element
            feature = ogr.Feature(_definition)
            # Create ring
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(
                cells_data["cell_coords"][0][i], cells_data["cell_coords"][1][i]
            )

            ring.AddPoint(
                cells_data["cell_coords"][2][i], cells_data["cell_coords"][1][i]
            )

            ring.AddPoint(
                cells_data["cell_coords"][2][i], cells_data["cell_coords"][3][i]
            )

            ring.AddPoint(
                cells_data["cell_coords"][0][i], cells_data["cell_coords"][3][i]
            )

            ring.AddPoint(
                cells_data["cell_coords"][0][i], cells_data["cell_coords"][1][i]
            )

            # Create polygon from ring
            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(ring)
            feature.SetGeometry(poly)
            self.set_field(feature, "nod_id", "int", cells_data["id"][i])
            self.set_field(
                feature, "bottom_lev", "float", cells_data["z_coordinate"][i]
            )
            layer.CreateFeature(feature)
