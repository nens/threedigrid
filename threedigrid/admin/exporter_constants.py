# constants for exporter objects.  At this point there
# is a only one exporter type which depends on ogr. As ogr
# is an optional install the constants have been moved to a
# module of their own

from __future__ import absolute_import

from collections import OrderedDict

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
    'display_name',  # missing in prepare step
    'material',
    'code',
    'calculation_type',
    'dist_calc_points',
    'connection_node_start_id',
    'connection_node_end_id',
]

PIPES_EXPORT_FIELDS = [
    'id',
    'display_name',
    'material',  # missing in prepare step
    'calculation_type',
    'cross_section_shape',
    'cross_section_width',
    'cross_section_height',
    'code',  # missing in prepare step
    'sewerage_type',
    'calculation_type',
    'invert_level_start_point',
    'invert_level_end_point',
    'cross_section_definition_id',  # missing in prepare step
    'friction_value',
    'original_lenght',  # missing in prepare step
    'connection_node_start_id',  # ! map to connection_node_start_pk
    'connection_node_end_id',  # !  map to connection_node_end_pk
    'cross_section_code',  # missing in prepare step
]

WEIRS_EXPORT_FIELDS = [
    'id',
    'display_name',
    'cross_section_shape',
    'cross_section_width',
    'cross_section_height',
    'code',
    'crest_level',
    'crest_type',
    'discharge_coefficient_positive',
    'discharge_coefficient_negative',
    'friction_value',
    'friction_type',
    'connection_node_start_id',
    'connection_node_end_id',
]

CULVERT_EXPORT_FIELDS = [
    'id',
    'display_name',
    'cross_section_shape',
    'cross_section_width',
    'cross_section_height',
    'calculation_type',
    'friction_value',
    'friction_type',
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
    'display_name',
    'cross_section_shape',
    'calculation_type',
    'bottom_level',
    'surface_level',
    'storage_area',
    'initial_waterlevel',
    'code',  # missing in prepare step
    'cross_section_width',
    'cross_section_height',
    'drain_level',
]

PUMPS_EXPORT_FIELDS = [
    'id',
    'display_name',
    'start_level',
    'lower_stop_level',
    'upper_stop_level',  # missing in prepare step
    'capacity',
    'connection_node_start_id',
    'connection_node_end_id',
    'classification',  # missing in prepare step
    'type',  # missing in prepare step
]


DEFAULT_EXPORT_FIELDS = {
    'Lines': 'all',
    'Pipes': PIPES_EXPORT_FIELDS,
    'Channels': CHANNELS_EXPORT_FIELDS,
    'Weirs': WEIRS_EXPORT_FIELDS,
    'Culverts': CULVERT_EXPORT_FIELDS,
    'Orifices': {},
    'Nodes': {},
    'ConnectionNodes': CONNECTION_NODES_EXPORT_FIELDS,
    'Manholes': MANHOLE_EXPORT_FIELDS,
    'Cells': {},
    'Grid': {},
    'Breaches': {},
    'Levees': {},
    'Pumps': PUMPS_EXPORT_FIELDS,
}
