# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

SHP_DRIVER_NAME = 'ESRI Shapefile'
GEO_PACKAGE_DRIVER_NAME = 'GPKG'

SHP_EXTENSION = '.shp'
GEO_PACKAGE_EXTENSION = '.gpkg'

EXTENSION_TO_DRIVER_MAP = {
    SHP_EXTENSION: SHP_DRIVER_NAME,
    GEO_PACKAGE_EXTENSION: GEO_PACKAGE_DRIVER_NAME
}
