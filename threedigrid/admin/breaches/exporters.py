# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Exporters
---------
At this moment there is one exporter for breach data, called
``BreachesOgrExporter``. For an overview of supported drivers call::

    >>> from threedigrid.admin.breaches.exporters import BreachesOgrExporter
    >>> from threedigrid.admin.gridadmin import GridH5Admin

    >>> f = 'gridadmin.h5'
    >>> ga = GridH5Admin(f)

    >>> # get all active breaches
    >>> active_breaches = ga.breaches.filter(kcu__eq=56)

    >>> exporter = BreachesOgrExporter(active_breaches)
    >>> exporter.supported_drivers
    >>> {u'ESRI Shapefile', u'GPKG'}

"""
from __future__ import unicode_literals
from __future__ import print_function

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
from threedigrid.admin.utils import KCUDescriptor
from threedigrid.admin import exporter_constants as const
from threedigrid.orm.base.exporters import BaseOgrExporter

logger = logging.getLogger(__name__)


class BreachesOgrExporter(BaseOgrExporter):
    """
    ogr exporter for breaches. See ``<instance>.supported_drivers`` to
    get a list of supported drivers
    """
    def __init__(self, breaches):
        self._breaches = breaches
        self.supported_drivers = {
            const.SHP_DRIVER_NAME,
            const.GEO_PACKAGE_DRIVER_NAME,
        }

    def save(self, file_name, breach_data, target_epsg_code, **kwargs):
        """
        save breaches to file

        :param file_name: file name including full path
        :param breach_data: queryset
        :param target_epsg_code: desired epsg code for coords
        :param kwargs: does not take extra kwargs
        """
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
        for field_name, field_type in six.iteritems(fields):
            layer.CreateField(
                ogr.FieldDefn(
                    str(field_name),
                    const.OGR_FIELD_TYPE_MAP[field_type]
                )
            )
        _definition = layer.GetLayerDefn()
        points = reshape_flat_array(selection['coordinates']).T

        for i in range(selection['id'].size):
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
