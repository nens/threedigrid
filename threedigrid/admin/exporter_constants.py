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

DEFAULT_EXPORT_FIELDS = {
    'Lines': [],
    'Pipes': PIPES_EXPORT_FIELDS,
    'Channels': [],
    'Weirs': [],
    'Culverts': [],
    'Orifices': [],
    'Nodes': [],
    'ConnectionNodes': [],
    'Manholes': [],
    'Cells': [],
    'Grid': [],
    'Breaches': [],
    'Levees': [],
    'Pumps': [],


}
