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
GEOJSON_DRIVER_NAME = 'GeoJSON'


CHANNELS_EXPORT_FIELDS = [
    'id',
    'content_pk',
    'code',
    'kcu',
    'calculation_type',
    'dist_calc_points',
    'connection_node_start_pk',
    'connection_node_end_pk',
    'discharge_coefficient'
]

PIPES_EXPORT_FIELDS = [
    'id',
    'content_pk',
    'display_name',
    'material',
    'kcu',
    'friction_value',
    'calculation_type',
    'sewerage_type',
    'cross_section_shape',
    'cross_section_width',
    'cross_section_height',
    'invert_level_start_point',
    'invert_level_end_point',
    'connection_node_start_pk',
    'connection_node_end_pk',
    'discharge_coefficient',
]

WEIRS_EXPORT_FIELDS = [
    'id',
    'content_pk',
    'display_name',
    'code',
    'kcu',
    'cross_section_shape',
    'cross_section_width',
    'cross_section_height',
    'crest_level',
    'crest_type',
    'sewerage',
    'discharge_coefficient_positive',
    'discharge_coefficient_negative',
    'friction_value',
    'friction_type',
    'connection_node_start_pk',
    'connection_node_end_pk',
]

CULVERT_EXPORT_FIELDS = [
    'id',
    'content_pk',
    'display_name',
    'code',
    'kcu',
    'cross_section_shape',
    'cross_section_width',
    'cross_section_height',
    'calculation_type',
    'friction_value',
    'friction_type',
    'dist_calc_points',
    'discharge_coefficient_positive',
    'discharge_coefficient_negative',
    'invert_level_start_point',
    'invert_level_end_point',
    'connection_node_start_pk',
    'connection_node_end_pk',
]

ORIFICES_EXPORT_FIELDS = [
    'id',
    'content_pk',
    'display_name',
    'kcu',
    'crest_level',
    'crest_type',
    'sewerage',
    'discharge_coefficient_negative',
    'discharge_coefficient_positive',
    'friction_type',
    'friction_value',
    'connection_node_start_pk',
    'connection_node_end_pk',
]

CONNECTION_NODES_EXPORT_FIELDS = [
    'content_pk',
    'initial_waterlevel',   # missing in prepare step
]

MANHOLE_EXPORT_FIELDS = [
    'id',
    'content_pk',
    'display_name',
    'calculation_type',
    'sumax',
    'bottom_level',
    'surface_level',
    'drain_level',
    'width',
    'shape',
    'storage_area',
    'initial_waterlevel',
]

PUMPS_EXPORT_FIELDS = [
    'id',
    'content_pk',
    'display_name',
    'start_level',
    'bottom_level',
    'lower_stop_level',
    'capacity',
    'type'
]

LEVEES_EXPORT_FIELDS = [
    'id',
    'crest_level',
    'max_breach_depth',
]

BREACHES_EXPORT_FIELDS = [
    "id",
    'content_pk',
    "levmat",
    "levbr",
    "kcu",
    "levl",
]

CELLS_EXPORT_FIELDS = [
    "id",
    'content_pk',
    "node_type",
    "sumax",
    "z_coordinate",
]

DEFAULT_EXPORT_FIELDS = {
    'Lines': 'ALL',
    'Pipes': PIPES_EXPORT_FIELDS,
    'Channels': CHANNELS_EXPORT_FIELDS,
    'Weirs': WEIRS_EXPORT_FIELDS,
    'Culverts': CULVERT_EXPORT_FIELDS,
    'Orifices': ORIFICES_EXPORT_FIELDS,
    'Nodes': 'ALL',
    'ConnectionNodes': CONNECTION_NODES_EXPORT_FIELDS,
    'Manholes': MANHOLE_EXPORT_FIELDS,
    'Cells': CELLS_EXPORT_FIELDS,
    'Grid': 'ALL',
    'Breaches': BREACHES_EXPORT_FIELDS,
    'Levees': LEVEES_EXPORT_FIELDS,
    'Pumps': PUMPS_EXPORT_FIELDS,
}
