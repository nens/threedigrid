# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import logging
from collections import OrderedDict
import six
from six.moves import range

try:
    from osgeo import ogr
except ImportError:
    ogr = None

from threedigrid.numpy_utils import reshape_flat_array
from threedigrid.geo_utils import get_spatial_reference
from threedigrid.orm.base.exporters import BaseOgrExporter
from threedigrid.admin import exporter_constants as const

logger = logging.getLogger(__name__)


class LeveeOgrExporter(BaseOgrExporter):
    """
    Exports to ogr formats. You need to set the driver explicitly
    before calling save()
    """
    def __init__(self, levees):
        """
        :param lines: lines.models.Lines instance
        """
        self._levees = levees
        self.supported_drivers = {
            const.GEO_PACKAGE_DRIVER_NAME,
            const.SHP_DRIVER_NAME,
        }
        self.driver = None

    def save(self, file_name, levee_data, target_epsg_code, **kwargs):
        """
        save to file format specified by the driver, e.g. shapefile

        :param file_name: name of the outputfile
        :param line_data: dict of line data
        """
        assert self.driver is not None

        geomtype = 0
        sr = get_spatial_reference(target_epsg_code)

        self.del_datasource(file_name)
        data_source = self.driver.CreateDataSource(file_name)
        layer = data_source.CreateLayer(
            str(os.path.basename(file_name)),
            sr,
            geomtype
        )
        # accounts for 2D only
        fields = OrderedDict([
            ('id', 'int'),
            ('cr_level', 'float'),
            ('mx_depth', 'float'),
        ])

        for field_name, field_type in six.iteritems(fields):
            layer.CreateField(ogr.FieldDefn(
                    field_name, const.OGR_FIELD_TYPE_MAP[field_type])
            )
        _definition = layer.GetLayerDefn()

        for i in range(len(self._levees.geoms)):
            line = ogr.Geometry(ogr.wkbLineString)
            feature = ogr.Feature(_definition)
            linepoints = reshape_flat_array(levee_data['coords'][i]).T
            for x in linepoints:
                line.AddPoint(x[0], x[1])
            feature.SetGeometry(line)
            # for field_name, field_type in fields.iteritems():
            #     raw_value = levee_data[field_name][i]
            #     print("raw_value  ", raw_value)
            #     value = TYPE_FUNC_MAP[field_type](raw_value)
            #     print("value  ", value)

            feature.SetField(str('id'), int(levee_data['id'][i]))
            feature.SetField(
                str('cr_level'), float(levee_data['crest_level'][i])
            )
            feature.SetField(
                str('mx_depth'), float(levee_data['max_breach_depth'][i])
            )

            layer.CreateFeature(feature)
            feature.Destroy()
