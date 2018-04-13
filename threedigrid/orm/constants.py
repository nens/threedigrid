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
# result netCDF variables

# values of *_COMPOSITE_FIELDS are the variables names as known in
# the result netCDF file. They are split into 1D and 2D subsets.
# As threedigrid has its own subsection ecosystem they are merged
# into a single field (e.g. the keys of *_COMPOSITE_FIELDS).

# N.B. # fields starting with '_' are private and will not be added to
# fields property

# calc nodes
NODES_COMPOSITE_FIELDS = {
    's1': ['Mesh2D_s1', 'Mesh1D_s1'],
    'vol': ['Mesh2D_vol', 'Mesh1D_vol'],
    'su': ['Mesh2D_su', 'Mesh1D_su'],
    'rain': ['Mesh2D_rain', 'Mesh1D_rain'],
    'q_lat': ['Mesh2D_q_lat', 'Mesh1D_q_lat'],
    '_mesh_id': ['Mesh2DNode_id', 'Mesh1DNode_id'],  # private
}

NODES_VARIABLES = NODES_COMPOSITE_FIELDS.keys()

# flow links
LINES_COMPOSITE_FIELDS = {
    'au': ['Mesh2D_au', 'Mesh1D_au'],
    'u1': ['Mesh2D_u1', 'Mesh1D_u1'],
    'q': ['Mesh2D_q', 'Mesh1D_q'],
    '_mesh_id': ['Mesh2DLine_id', 'Mesh1DLine_id'], # private
}
LINES_VARIABLES = LINES_COMPOSITE_FIELDS.keys()

# pumpstations
PUMPS_VARIABLES = ['Mesh1D_q_pump',]

# breaches
BREACH_VARIABLES = ['Mesh1D_breach_depth', 'Mesh1D_breach_width']
LEVEES_VARIABLES = []
