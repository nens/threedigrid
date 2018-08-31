# constants for exporter objects.  At this point there
# is a only one exporter type which depends on ogr. As ogr
# is an optional install the constants have been moved to a
# module of their own

from __future__ import absolute_import
try:
    from osgeo import ogr
except ImportError:
    ogr = None

if ogr is not None:
    OGR_FIELD_TYPE_MAP = {
        'int': ogr.OFTInteger,
        'str': ogr.OFTString,
        'real': ogr.OFTReal,
        'float': ogr.OFTReal,
    }

SHP_DRIVER_NAME = 'ESRI Shapefile'
GEO_PACKAGE_DRIVER_NAME = 'GPKG'
