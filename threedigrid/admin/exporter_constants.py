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
    'content_type',
    'display_name',  # missing in prepare step
    'code',
    'material',
    'kcu'
    'calculation_type',
    'dist_calc_points',
    'connection_node_start_id',
    'connection_node_end_id',
]

PIPES_EXPORT_FIELDS = [
    'id',
    'content_type',
    'display_name',
    'code',  # missing in prepare step
    'material',  # missing in prepare step
    'kcu',
    'friction_value',
    'calculation_type',
    'sewerage_type',
    'original_length',  # missing in prepare step
    'cross_section_shape',
    'cross_section_width',
    'cross_section_height',
    'cross_section_code',  # missing in prepare step
    'cross_section_definition_id',  # missing in prepare step
    'invert_level_start_point',
    'invert_level_end_point',
    'connection_node_start_id',  # ! map to connection_node_start_pk
    'connection_node_end_id',  # !  map to connection_node_end_pk
]

WEIRS_EXPORT_FIELDS = [
    'id',
    'content_type',
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
    'connection_node_start_id',
    'connection_node_end_id',
]

CULVERT_EXPORT_FIELDS = [
    'id',
    'content_type',
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
    'connection_node_start_id',
    'connection_node_end_id',
]

CONNECTION_NODES_EXPORT_FIELDS = [
    'initial_waterlevel',   # missing in prepare step
]

MANHOLE_EXPORT_FIELDS = [
    'id',
    'content_type',
    'display_name',
    'code',  # missing in prepare step
    'cross_section_shape',
    'calculation_type',
    'sumax',
    'bottom_level',
    'surface_level',
    'drain_level',
    'width',
    'length',  # missing in prepare step
    'shape',
    'storage_area',
    'initial_waterlevel',
]

PUMPS_EXPORT_FIELDS = [
    'id',
    'content_type',
    'display_name',
    'start_level',
    'bottom_level',
    'lower_stop_level',
    'upper_stop_level',  # missing in prepare step
    'capacity',
    'classification',  # missing in prepare step
    'type',  # missing in prepare step
    'connection_node_start_id',  # missing in prepare step
    'connection_node_end_id',  # missing in prepare step
]


DEFAULT_EXPORT_FIELDS = {
    'Lines': 'ALL',
    'Pipes': PIPES_EXPORT_FIELDS,
    'Channels': CHANNELS_EXPORT_FIELDS,
    'Weirs': WEIRS_EXPORT_FIELDS,
    'Culverts': CULVERT_EXPORT_FIELDS,
    'Orifices': 'ALL',
    'Nodes': 'ALL',
    'ConnectionNodes': CONNECTION_NODES_EXPORT_FIELDS,
    'Manholes': MANHOLE_EXPORT_FIELDS,
    'Cells': 'ALL',
    'Grid': 'ALL',
    'Breaches': 'ALL',
    'Levees': 'ALL',
    'Pumps': PUMPS_EXPORT_FIELDS,
}
