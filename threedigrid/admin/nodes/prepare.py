# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np
from threedigrid.admin import constants
from threedigrid.admin.nodes.subsets import NODE_TYPE__IN_SUBSETS
from threedigrid.admin.prepare_utils import (
        db_objects_to_numpy_array_dict, add_or_update_datasets)


def as_numpy_array(array):
    if hasattr(array, 'value'):
        return array.value
    return array[()]


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
        if 'id' not in list(datasource.keys()):
            datasource.set(
                'id', np.arange(0, datasource['x_coordinate'].size))

        if 'content_pk' not in list(datasource.keys()) and has_1d:
            datasource.set(
                'content_pk', cls.get_node_pks(mapping1d, id_mapper))

        if 'seq_id' not in list(datasource.keys()) and has_1d:
            datasource.set('seq_id', mapping1d['nend1d'][:])

        if 'coordinates' not in list(datasource.keys()):
            datasource.set(
                'coordinates', np.array(
                    [as_numpy_array(datasource['x_coordinate']),
                     as_numpy_array(datasource['y_coordinate'])]))


class PrepareConnectionNodes:

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        node_group = h5py_file['nodes']
        content_pk = node_group['content_pk'][:]

        connection_nodes_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.connection_nodes,
            ['pk', 'initial_waterlevel', 'storage_area'])

        add_or_update_datasets(
            node_group, connection_nodes_numpy_array_dict,
            ['initial_waterlevel', 'storage_area'],
            connection_nodes_numpy_array_dict['pk'], content_pk)


class PrepareCells:

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        node_group = h5py_file['nodes']
        lgrmin = h5py_file['meta']['lgrmin'][()]
        nodk = h5py_file['grid_coordinate_attributes']['nodk'][()]
        nodm = h5py_file['grid_coordinate_attributes']['nodm'][()]
        nodn = h5py_file['grid_coordinate_attributes']['nodn'][()]
        ip = h5py_file['grid_coordinate_attributes']['ip'][()]
        jp = h5py_file['grid_coordinate_attributes']['jp'][()]

        node_types = h5py_file['nodes']['node_type'][:]

        pixel_width = np.zeros(nodk.shape, dtype='int')
        pixel_coords = np.full((4, nodk.shape[0]), -9999, dtype='int')
        for node_type_subset in NODE_TYPE__IN_SUBSETS['2D_ALL']:
            mask = node_types == node_type_subset
            pixel_width[mask] = lgrmin * 2 ** (nodk[mask] - 1)
            pixel_coords[0, mask] = ip[0, nodm[mask] - 1, nodk[mask] - 1] - 1
            pixel_coords[1, mask] = jp[0, nodn[mask] - 1, nodk[mask] - 1] - 1
            pixel_coords[2, mask] = ip[3, nodm[mask] - 1, nodk[mask] - 1]
            pixel_coords[3, mask] = jp[3, nodn[mask] - 1, nodk[mask] - 1]

        node_group.create_dataset('pixel_width', data=pixel_width, dtype='int')
        node_group.create_dataset(
            'pixel_coords', data=pixel_coords, dtype='int'
        )


class PrepareManholes:

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        node_group = h5py_file['nodes']
        content_pk = node_group['content_pk'][:]

        manhole_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.v2_manholes, [
                'pk', 'surface_level', 'display_name', 'bottom_level',
                'calculation_type', 'shape', 'drain_level', 'width',
                'manhole_indicator', 'zoom_category', 'connection_node_pk'])

        # extra field to distinguish manholes from connection nodes.
        is_manhole = np.full(len(threedi_datasource.v2_manholes), True)
        manhole_numpy_array_dict['is_manhole'] = is_manhole

        add_or_update_datasets(
            node_group, manhole_numpy_array_dict,
            ['surface_level', 'display_name', 'bottom_level',
             'calculation_type', 'shape', 'drain_level', 'width',
             'manhole_indicator', 'zoom_category', 'is_manhole'],
            manhole_numpy_array_dict['connection_node_pk'], content_pk)
