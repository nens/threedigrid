
NODES_LAYER_DEF = {
    'id': 'id',
    'content_pk': 'connection_node_id',
    'node_type': 'node_type',
    'calculation_type': 'calculation_type',
    'is_manhole': 'is_manhole',
    'storage_area': 'connection_node_storage_area',
    'sumax': 'max_surface_area',
    'dmax': 'bottom_level',
    'drain_level': 'drain_level',
}


CELL_LAYER_DEF = {
    'id': 'id',
    'node_type': 'node_type',
    'has_dem_averaged': 'has_dem_averaged',
    'sumax': 'max_surface_area',
    'dmax': 'bottom_level',
    'dimp': 'impervious_layer_elevation',
}


FLOWLINE_LAYER_DEF = {
    'id': 'id',
    'flou': 'discharge_coefficient_positive',
    'flod': 'discharge_coefficient_negative',
    'cross1': "cross1", # id of cross section at start side of the flowline; does not have to be exposed to user
    'cross2': "cross2", # id of cross section at end side of the flowline; does not have to be exposed to user
    'cross_weight': "cross_weight", # cross section is distance weighted average between cross1 and cross 2, cross_weight is the weight; does not have to be exposed to user
    'kcu': 'line_type',
    'content_type': 'source_table',
    'content_pk': 'source_table_id',
    'invert_level_start_point': 'invert_level_start_point',
    'invert_level_end_point': 'invert_level_end_point',
    'dpumax': 'exchange_level',
    # 'line' --> 'calculation_node_id_start', 'calculation_node_id_end',
}