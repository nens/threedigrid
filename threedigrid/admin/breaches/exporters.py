# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import os
import logging
from collections import OrderedDict

from osgeo import ogr

from threedigrid.admin.utils import reshape_flat_array
from threedigrid.admin.utils import get_spatial_reference
from threedigrid.admin.utils import KCUDescriptor
from threedigrid.admin.constants import GEO_PACKAGE_DRIVER_NAME
from threedigrid.admin.constants import OGR_FIELD_TYPE_MAP
from threedigrid.admin.constants import SHP_DRIVER_NAME
from threedigrid.orm.base.exporters import BaseOgrExporter

logger = logging.getLogger(__name__)



class BreachesOgrExporter(BaseOgrExporter):
    def __init__(self, breaches):
        self._breaches = breaches
        self.supported_drivers = {
            SHP_DRIVER_NAME,
            GEO_PACKAGE_DRIVER_NAME,
        }

    def save(self, file_name, breach_data, target_epsg_code, **kwargs):
        assert self.driver is not None
        selection = breach_data
        kcu_dict = KCUDescriptor()
        geomtype = 0
        sr = get_spatial_reference(target_epsg_code)
        self.del_datasource(file_name)
        data_source = self.driver.CreateDataSource(file_name)
        layer = data_source.CreateLayer(
            str(os.path.basename(file_name)),
            sr,
            geomtype
        )
        fields = OrderedDict([
            ('link_id', 'int'),
            ('kcu', 'int'),
            ('kcu_descr', 'str'),
            ('cont_pk', 'int'),
        ])
        for field_name, field_type in fields.iteritems():
            layer.CreateField(
                ogr.FieldDefn(
                    str(field_name), OGR_FIELD_TYPE_MAP[field_type]
                )
            )
        _definition = layer.GetLayerDefn()
        points = reshape_flat_array(selection['coordinates']).T

        for i in xrange(selection['id'].size):
            feature = ogr.Feature(_definition)
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(points[i][0], points[i][1])
            feature.SetGeometry(point)
            feature.SetField(str("link_id"), int(selection['levl'][i]))
            kcu = selection['kcu'][i]
            feature.SetField(str("kcu"), int(kcu))
            kcu_descr = ''
            try:
                kcu_descr = kcu_dict[kcu]
            except KeyError:
                pass
            feature.SetField(str("kcu_descr"), str(kcu_descr))
            feature.SetField(str("cont_pk"), int(selection['content_pk'][i]))
            layer.CreateFeature(feature)
