# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
from collections import OrderedDict
from six.moves import range

LONLAT_DIGITS = 7  # 7 decimals is about 11mm accuracy

TYPE_V2_PIPE = 'v2_pipe'
TYPE_V2_CHANNEL = 'v2_channel'
TYPE_V2_CULVERT = 'v2_culvert'
TYPE_V2_ORIFICE = 'v2_orifice'
TYPE_V2_WEIR = 'v2_weir'
TYPE_V2_MANHOLE = 'v2_manhole'
TYPE_V2_PUMPSTATION = 'v2_pumpstation'
TYPE_V2_LEVEE = 'v2_levee'
TYPE_V2_1D_LATERAL = 'v2_1d_lateral'
TYPE_V2_WINDSHIELD = 'v2_windshielding'

TYPE_V2_1D_BOUNDARY_CONDITIONS = 'v2_1d_boundary_conditions'
TYPE_V2_2D_BOUNDARY_CONDITIONS = 'v2_2d_boundary_conditions'
TYPE_V2_CONNECTION_NODES = 'v2_connection_nodes'

TYPE_V2_BREACH = 'v2_breach'
TYPE_V2_CROSS_SECTION_DEF = 'v2_cross_section_definition'
TYPE_V2_CROSS_SECTION_LOCATION = 'v2_cross_section_location'
TYPE_V2_ADDED_CALCULATION_POINT = 'v2_added_calculation_point'


TYPE_CODE_MAP = {
    TYPE_V2_PIPE: 1,
    TYPE_V2_CHANNEL: 2,
    TYPE_V2_CULVERT: 3,
    TYPE_V2_ORIFICE: 4,
    TYPE_V2_WEIR: 5,
    TYPE_V2_MANHOLE: 6,
    TYPE_V2_PUMPSTATION: 7,
    TYPE_V2_LEVEE: 8,
    TYPE_V2_1D_LATERAL: 9,
    TYPE_V2_1D_BOUNDARY_CONDITIONS: 10,
    TYPE_V2_2D_BOUNDARY_CONDITIONS: 11,
    TYPE_V2_CONNECTION_NODES: 12,
    TYPE_V2_BREACH: 13,
    TYPE_V2_CROSS_SECTION_DEF: 14,
    TYPE_V2_CROSS_SECTION_LOCATION: 15,
    TYPE_V2_ADDED_CALCULATION_POINT: 16,
    TYPE_V2_WINDSHIELD: 17
}

# ------------------ HDF5 NAMES ------------------ #
DSET_ID_MAPPING = 'id_map'
GROUP_MAPPINGS = 'mappings'

DSET_GEOMS = 'geoms'
GROUP_LEVEE = 'levees'

###############################################################################
# HDF5 ATTRIBUTE NAMES
EXTENT_1D_KEY = 'extent_1d'
EXTENT_2D_KEY = 'extent_2d'
THREEDICORE_VERSION_KEY = 'threedicore_version'
HAS_1D_KEY = 'has_1d'
HAS_2D_KEY = 'has_2d'
HAS_PUMPSTATIONS_KEY = 'has_pumpstations'
HAS_BREACHES_KEY = 'has_breaches'


###############################################################################
# MANHOLE_TYPES is used by:
#
#   - v2_manhole

MANHOLE_TYPES = {
    0: 'manhole',
    1: 'outlet',
    2: 'pumpstation',
}


CALCULATION_TYPES = {
    # -1 tot 99 ::= Node | 'verbinding-zonder-subnodes(="vertices")'
    -1: 'boundary node',
    0: 'embedded',
    1: 'stand-alone',
    2: 'connected',
    3: 'broad crested',  # only orifices + weirs, corresponds
    4: 'short crested',  # only orifices + weirs
    5: 'double connected',

    # 100 tot oneindig ::= 'verbinding-met-subnodes(="vertices")'
    # a.k.a. pinpoint
    100: 'embedded',
    101: 'stand-alone',
    102: 'connected',
    105: 'double connected'
}

# Hardcoded zoom levels for pipe/nod/nod_1d/line/pump
# for 1-5 zoom level ("zoom_category") in sqlite file.


ZOOM_LEVELS = {
    'pipe': list(range(16, 21)),
    'nod': list(range(16, 21)),
    'nod_1d': list(range(16, 21)),
    'line': list(range(16, 21)),
    'pump': list(range(16, 21)),
}


###############################################################################
# SEWERAGE_TYPES is used by:
#
#   - v2_pipe

SEWERAGE_TYPES = {
    0: 'combined',
    1: 'stormwater',
    2: 'wastewater',
    3: 'transport',
    4: 'overflow',
    5: 'sinker',
    6: 'storage',
    7: 'storage settling tank',
    8: None,
}


###############################################################################
# CREST_TYPES is used by:
#
#   - v2_weir
#   - v2_orifice
#
# NB! This mapping is related to CALCULATION_TYPES mapping (key=3 | key=4)

CREST_TYPES = {
    3: 'broad crested',  # only orifices + weirs
    4: 'short crested',  # only orifices + weirs
}

# accounts for 2D only
LINE_BASE_FIELDS = OrderedDict([
    ('link_id', 'int'),
    ('kcu', 'int'),
    ('kcu_descr', 'str'),
    ('node_a', 'int'),
    ('node_b', 'int'),
])

# extends LINE_BASE_FIELDS in case of 1D
LINE_1D_FIELDS = OrderedDict([
    ('cont_type', 'str'),
    ('cont_pk', 'int'),
    ('seq_id', 'int'),
])

# maps the fields names of grid line objects
# to their external representation
LINE_FIELD_NAME_MAP = OrderedDict([
    ('link_id', 'id'),
    ('kcu', 'kcu'),
    ('kcu_descr', 'kcu_descr'),
    ('node_a', 'node_a'),
    ('node_b', 'node_b'),
    ('seq_id', 'lik'),
    ('cont_type', 'content_type'),
    ('cont_pk', 'content_pk'),
])

# accounts for 2D only
NODE_BASE_FIELDS = OrderedDict([
    ('nod_id', 'int'),
])

NODE_1D_FIELDS = OrderedDict([
    ('con_nod', 'str'),
    ('con_nod_pk', 'int'),
])

NODE_FIELD_NAME_MAP = OrderedDict([
    ('nod_id', 'id'),
    ('con_nod', 'seq_id'),
    ('con_nod_pk', 'content_pk'),
])

TYPE_FUNC_MAP = {
    'int': int,
    'float': float,
    'str': str}


###############################################################################
# shapefile names (served by tilestache)
SUBSET_1D_ALL = '1D_all'
SUBSET_2D_GROUNDWATER = '2D_groundwater'
SUBSET_2D_OPEN_WATER = '2D_open_water'
SUBSET_2D_VERTICAL_INFILTRATION = '2D_vertical_infiltration'

# grids
_BASE_NAME = 'grid_'
GROUNDWATER_SHP = _BASE_NAME + SUBSET_2D_GROUNDWATER + ".shp"
OPEN_WATER_SHP = _BASE_NAME + SUBSET_2D_OPEN_WATER + ".shp"

# nodes
_NODES_BASE = 'nodes_'
NODES_SHP = _NODES_BASE + SUBSET_1D_ALL + ".shp"

# lines
_LINES_BASE = 'lines_'
LINES_SHP = _LINES_BASE + SUBSET_1D_ALL + ".shp"
GROUNDWATER_LINES_SHP = _LINES_BASE + SUBSET_2D_GROUNDWATER + ".shp"
OPEN_WATER_LINES_SHP = _LINES_BASE + SUBSET_2D_OPEN_WATER + ".shp"
VERTICAL_INFILTRATION_LINES_SHP = (
    _LINES_BASE + SUBSET_2D_VERTICAL_INFILTRATION + ".shp")

# levees
LEVEES_SHP = "levees.shp"


###############################################################################
# for extent calculations

# key: name of the node subset
# value: hdf5 attribute
SUBSET_NAME_H5_ATTR_MAP = {
    SUBSET_1D_ALL.upper(): EXTENT_1D_KEY,
    SUBSET_2D_OPEN_WATER.upper(): EXTENT_2D_KEY
}

NO_DATA_VALUE = -9999.

# the default slice for result timeseries
DEFAULT_CHUNK_TIMESERIES = slice(0, 10)
