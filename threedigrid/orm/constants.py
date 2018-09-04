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

###############################################################################
# White list of variables and aggregation variables
AGGREGATION_OPTIONS = {
    'min',
    'max',
    'avg',
    'med',
    'cum',
    'cum_positive',
    'cum_negative'
}

###############################################################################
# result netCDF variables


# pumpstations
PUMPS_VARIABLES = ['Mesh1D_q_pump']

# breaches
BREACH_VARIABLES = ['Mesh1D_breach_depth', 'Mesh1D_breach_width']
LEVEES_VARIABLES = []
