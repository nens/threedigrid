# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np
from threedigrid.admin import constants
from threedigrid.admin.prepare_utils import (
        db_objects_to_numpy_array_dict, add_or_update_datasets)


def as_numpy_array(array):
    if hasattr(array, 'value'):
        return array.value
    return array


class PrepareNodes:

    @staticmethod
    def get_node_pks(mapping1d, id_mapper):
        # pk template
        type_code = constants.TYPE_CODE_MAP['v2_connection_nodes']

        content_pk = np.zeros(
            mapping1d['nend1d'].shape, dtype='i4'
        )

        # with argsort
        sort_idx = np.argsort(mapping1d['nend1d'])
        idx = sort_idx[np.searchsorted(
            mapping1d['nend1d'],
            id_mapper.id_mapping[
                id_mapper.obj_slices[type_code]]['seq_id'],
            sorter=sort_idx)]

        content_pk[idx] = id_mapper.id_mapping[
            id_mapper.obj_slices[type_code]]['pk']
        return content_pk

    @classmethod
    def prepare_datasource(cls, datasource, mapping1d, id_mapper, has_1d):
        if 'id' not in datasource.keys():
            datasource.set(
                'id', np.arange(0, datasource['x_coordinate'].size))

        if 'content_pk' not in datasource.keys() and has_1d:
            datasource.set(
                'content_pk', cls.get_node_pks(mapping1d, id_mapper))

        if 'seq_id' not in datasource.keys() and has_1d:
            datasource.set('seq_id', mapping1d['nend1d'].value)

        if 'coordinates' not in datasource.keys():
            datasource.set(
                'coordinates', np.array(
                    [as_numpy_array(datasource['x_coordinate']),
                     as_numpy_array(datasource['y_coordinate'])]))


class PrepareConnectionNodes:

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        node_group = h5py_file['nodes']
        content_pk = node_group['content_pk'].value

        connection_nodes_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.connection_nodes,
            ['pk', 'initial_waterlevel', 'storage_area'])

        add_or_update_datasets(
            node_group, connection_nodes_numpy_array_dict,
            ['initial_waterlevel', 'storage_area'],
            connection_nodes_numpy_array_dict['pk'], content_pk)


class PrepareManholes:

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        node_group = h5py_file['nodes']
        content_pk = node_group['content_pk'].value

        manhole_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.v2_manholes, [
                'pk', 'surface_level', 'display_name', 'bottom_level',
                'calculation_type', 'shape', 'drain_level', 'width',
                'manhole_indicator', 'zoom_category'])
        add_or_update_datasets(
            node_group, manhole_numpy_array_dict,
            ['surface_level', 'display_name', 'bottom_level',
             'calculation_type', 'shape', 'drain_level', 'width',
             'manhole_indicator', 'zoom_category'],
            manhole_numpy_array_dict['pk'], content_pk)
