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

CHANNELS_EXPORT_FIELDS = OrderedDict([
    ('display_name', None),  # missing in prepare step
    ('material', 'str'),
    ('extra_data', OrderedDict([
        ('code', None),
        ('calculation_type', None),
        ('dist_calc_points', None),
        ('connection_node_start_id', None),
        ('connection_node_end_id', None)
    ]))

])

PIPES_EXPORT_FIELDS = OrderedDict([
    ('display_name', 'str'),
    ('material', 'int'),  # missing in prepare step
    ('calculation_type', 'int'),
    ('cross_section_shape', 'int'),
    ('cross_section_width', 'int'),
    ('cross_section_height', 'int'),
    ('extra_data', OrderedDict([
        ('id', 'int'),
        ('code', 'str'),  # missing in prepare step
        ('sewerage_type', 'str'),
        ('calculation_type', 'str'),
        ('invert_level_start_point', 'str'),
        ('invert_level_end_point', 'str'),
        ('cross_section_definition_id', 'str'),  # missing in prepare step
        ('friction_value', 'int'),
        ('original_lenght', 'int'),
        ('connection_node_start_id', 'int'),  # ! map to connection_node_start_pk
        ('connection_node_end_id', 'int'),  # !  map to connection_node_end_pk
        ('cross_section_code', 'int'),
    ]))
])

WEIRS_EXPORT_FIELDS = OrderedDict([
    ('display_name', None),
    ('cross_section_shape', 'int'),
    ('cross_section_width', 'int'),
    ('cross_section_height', 'int'),
    ('extra_data', OrderedDict([
        ('id', None),
        ('code', None),
        ('crest_level', None),
        ('crest_type', None),
        ('discharge_coefficient_positive', None),
        ('discharge_coefficient_negative', None),
        ('friction_value', None),
        ('friction_type', None),
        ('connection_node_start_id', None),
        ('connection_node_end_id', None),
    ]))
])

CULVERT_EXPORT_FIELDS = OrderedDict([
    ('display_name', None),
    ('cross_section_shape', 'int'),
    ('cross_section_width', 'int'),
    ('cross_section_height', 'int'),
    ('extra_data', OrderedDict([
        ('calculation_type', None),
        ('friction_value', None),
        ('friction_type', None),
        ('discharge_coefficient_positive', None),
        ('discharge_coefficient_negative', None),
        ('invert_level_start_point', None),
        ('invert_level_end_point', None),
        ('connection_node_start_id', None),
        ('connection_node_end_id', None),
    ]))
])

CONNECTION_NODES_EXPORT_FIELDS = OrderedDict([
    ('extra_data', OrderedDict([
        ('initial_waterlevel', None),  # missing in prepare step
    ]))
])

MANHOLE_EXPORT_FIELDS = OrderedDict([
    ('display_name', None),
    ('cross_section_shape', 'int'),
    ('calculation_type', None),
    ('bottom_level', None),
    ('surface_level', None),
    ('storage_area', None),
    ('initial_waterlevel', None),
    ('extra_data', OrderedDict([
        ('code', None),  # missing in prepare step
        ('cross_section_width', 'int'),
        ('cross_section_height', 'int'),
        ('drain_level', None),
    ]))
])

PUMPS_EXPORT_FIELDS = OrderedDict([
    ('id', None),
    ('display_name', None),
    ('start_level', None),
    ('lower_stop_level', None),
    ('upper_stop_level', None),  # missing in prepare step
    ('capacity', None),
    ('connection_node_start_id', None),
    ('connection_node_end_id', None),
    ('extra_data', OrderedDict([
        ('classification', None),  # missing in prepare step
        ('type', None),  # missing in prepare step
    ]))
])


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
