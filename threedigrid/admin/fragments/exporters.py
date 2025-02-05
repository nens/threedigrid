# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

import os
from collections import OrderedDict

try:
    from osgeo import ogr
except ImportError:
    ogr = None

from threedigrid.admin import exporter_constants as const
from threedigrid.geo_utils import get_spatial_reference
from threedigrid.numpy_utils import reshape_flat_array
from threedigrid.orm.base.exporters import BaseOgrExporter


class FragmentsOgrExporter(BaseOgrExporter):
    """
    Exports to ogr formats. You need to set the driver explicitly
    before calling save()
    """

    def __init__(self, fragments):
        """
        :param fragments: fragments.models.Fragments instance
        """
        self._fragments = fragments
        self.supported_drivers = {
            const.GEO_PACKAGE_DRIVER_NAME,
            const.SHP_DRIVER_NAME,
            const.GEOJSON_DRIVER_NAME,
        }
        self.driver = None

    def save(self, file_name, layer_name, target_epsg_code, **kwargs):
        """
        save to file format specified by the driver, e.g. shapefile

        :param file_name: name of the outputfile
        :param fragment_data: dict of fragment data
        """
        if self.driver is None:
            self.set_driver(extension=os.path.splitext(file_name)[1])

        assert self.driver is not None

        sr = get_spatial_reference(target_epsg_code)

        self.del_datasource(file_name)
        data_source = self.driver.CreateDataSource(file_name)
        layer = data_source.CreateLayer(
            str(os.path.basename(file_name)), sr, ogr.wkbPolygon
        )

        fields = OrderedDict(
            [
                ("id", "int"),
                ("node_id", "int"),
            ]
        )

        for field_name, field_type in fields.items():
            layer.CreateField(
                ogr.FieldDefn(field_name, const.OGR_FIELD_TYPE_MAP[field_type])
            )
        _definition = layer.GetLayerDefn()

        for i in range(len(self._fragments.coords)):
            if self._fragments.id[i] == 0:
                continue  # skip the dummy element
            feature = ogr.Feature(_definition)
            ring = ogr.Geometry(ogr.wkbLinearRing)
            polygon_points = reshape_flat_array(self._fragments.coords[i]).T
            for x in polygon_points:
                ring.AddPoint(x[0], x[1])
            polygon = ogr.Geometry(ogr.wkbPolygon)
            polygon.AddGeometry(ring)
            feature.SetGeometry(polygon)
            self.set_field(feature, "id", "int", self._fragments.id[i])
            self.set_field(feature, "node_id", "int", self._fragments.node_id[i])
            layer.CreateFeature(feature)
            feature.Destroy()
