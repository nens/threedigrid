# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import h5py
import numpy as np
from shapely import wkt
from shapely.geometry import MultiPoint, Point
from threedigrid.admin import constants
from threedigrid.admin.prepare_utils import (
        db_objects_to_numpy_array_dict, add_or_update_datasets)
from six.moves import range
from six.moves import zip


DT_VARIABLE = h5py.special_dtype(vlen=np.dtype('float64'))


def as_numpy_array(array):
    if hasattr(array, 'value'):
        return array.value
    return array


class PrepareLines(object):

    @staticmethod
    def get_1d_object_info(datasource, id_mapper):
        """
        Set content type and content pk's based on id mapping and
        kcu's from calculationcore.

        :return: content_type and content_pk with length lines
        """

        # TODO channel might be different
        LINE_TYPES = [
            constants.TYPE_V2_PIPE, constants.TYPE_V2_CHANNEL,
            constants.TYPE_V2_CULVERT,
            constants.TYPE_V2_ORIFICE, constants.TYPE_V2_WEIR]

        _tmp_kcu = datasource['kcu'].value
        filter_1d = (_tmp_kcu >= 0) & (_tmp_kcu <= 5)

        lik_all = as_numpy_array(datasource['lik'])
        lik_1d = as_numpy_array(datasource['lik'])[filter_1d]

        content_pk = np.zeros(lik_all.shape, dtype='i4')
        content_type = np.zeros(lik_all.shape, dtype='U32')

        _content_pk = np.zeros(lik_1d.shape, dtype='i4')
        _content_type = np.zeros(lik_1d.shape, dtype='U32')

        for line_type in LINE_TYPES:
            line_code = constants.TYPE_CODE_MAP[line_type]
            mapper_idx = id_mapper.obj_slices.get(line_code)
            if mapper_idx is None:
                continue
            seq_ids = id_mapper.id_mapping[mapper_idx]['seq_id']
            for i in range(len(seq_ids)):
                slice1 = np.where(lik_1d == seq_ids[i])
                _content_pk[slice1] = id_mapper.id_mapping[mapper_idx]['pk'][i]
                _content_type[slice1] = line_type

        content_pk[filter_1d] = _content_pk
        content_type[filter_1d] = _content_type

        return content_pk, content_type

    @classmethod
    def make_line_geometries(cls, datasource, threedi_datasource):
        """

        create line geometries based on spatialite geometries but with
        segmentized for calculation core line segments
        :return:
        flattened array of line_geometries with length lines
        array[
            [x1, x2, x3, y1, y2, y3],
            [x1, x2, y1, y2]
        ]
        """

        DB_OBJECTS = [
            threedi_datasource.v2_channels, threedi_datasource.v2_culverts
        ]

        LINE_TYPES = [
            constants.TYPE_V2_CHANNEL, constants.TYPE_V2_CULVERT
        ]

        line_db_dict = dict(list(zip(LINE_TYPES, DB_OBJECTS)))

        size_array = as_numpy_array(datasource['lik']).shape[0]
        line_geometries = np.full(size_array, 0, dtype=DT_VARIABLE)
        start_x = datasource['line_coords'][0][:]
        start_y = datasource['line_coords'][1][:]
        end_x = datasource['line_coords'][2][:]
        end_y = datasource['line_coords'][3][:]
        kcu = datasource['kcu'][:]
        xys = np.array(list(zip(start_x.T, end_x.T, start_y.T, end_y.T)))
        for i in range(len(line_geometries)):
            line_geometries[i] = np.array(xys[i])

        for line_type, db_objects in line_db_dict.items():
            for db_object in db_objects:
                line_idx = np.where(
                    (datasource['content_pk'].value == db_object.pk) &
                    (datasource['content_type'].value == line_type))[0]
                geom = wkt.loads(db_object.the_geom.wkt)
                line_geometries[line_idx] = PrepareLines._cut_geometries(
                    geom,
                    start_x[line_idx], start_y[line_idx],
                    end_x[line_idx], end_y[line_idx],
                    kcu[line_idx])

        return line_geometries

    @staticmethod
    def _cut_geometries(geom, start_x, start_y, end_x, end_y, kcu_array):
        """
        Segmentize line geometry based on start and end points from calc
        line segments

        :param geom: orginal geometry from the sqlite database
        :param start_x: threedicore x-coordinates for start points
        :param start_y: threedicore y-coordinates for start points
        :param end_x: threedicore x-coordinates for end points
        :param end_y: threedicore y-coordinates for end points
        :kcu_array: corresponding kcu values for threedicore coordinates

        :returns  an array of seperate line geometries for number of
        calc lines on geometry, like so::

            array[
                [x1, x2, x3, y1, y2, y3],
                [x1, x2, y1, y2]
            ]
        """

        cut_geometries = np.zeros((len(start_x),), dtype=DT_VARIABLE)
        start_points = MultiPoint(list(zip(start_x, start_y)))
        end_points = MultiPoint(list(zip(end_x, end_y)))

        for piece in range(len(cut_geometries)):
            kcu = kcu_array[piece]
            if kcu == 0:
                start_pnt = geom.interpolate(geom.project(start_points[piece]))
                end_pnt = geom.interpolate(geom.project(end_points[piece]))
            else:
                start_pnt = start_points[piece]
                end_pnt = end_points[piece]
            start_distance = round(geom.project(start_pnt), 3)
            end_distance = round(geom.project(end_pnt), 3)
            coords = list(geom.coords)
            start_set = False
            # no additional calc points
            if start_distance <= 0.0 and end_distance >= geom.length:
                linestring = np.array(
                    [(start_pnt.x, start_pnt.y)] +
                    coords[1:-1] +
                    [(end_pnt.x, end_pnt.y)])
                # "F" means to flatten in column-major (Fortran- style) order
                cut_geometries[piece] = linestring.flatten('F')

            for i, p in enumerate(coords):
                # dist to vertex
                pd = round(geom.project(Point(p)), 3)

                # should not happen but sometimes drawing direction does not
                # correspond with start and endpoints, so flip them
                if start_distance > end_distance:
                    # This is not safe!!!!!!
                    # TODO: check if this actually can happen
                    start_distance, end_distance = end_distance, start_distance
                    start_points, end_points = end_points, start_points

                # check for start point
                if (pd == start_distance) and not start_set:
                    start_pnt = []
                    start_i = i
                    start_set = True
                # should not happen but in case pd (point) and first vertex
                # do not have the same position move pd back
                elif (pd > start_distance) and not start_set:
                    start_pnt = [
                        (start_pnt.x, start_pnt.y)]
                    start_i = i
                    start_set = True
                if pd >= end_distance:
                    linestring = np.array(
                        start_pnt + coords[start_i: i] +
                        [(end_pnt.x, end_pnt.y)])
                    # "F" means to flatten in column-major (Fortran- style)
                    # order
                    cut_geometries[piece] = linestring.flatten('F')
                    break

        return cut_geometries

    @classmethod
    def prepare_datasource(cls, datasource, id_mapper, threedi_datasource,
                           node_coordinates, has_1d):
        if 'id' not in list(datasource.keys()):
            datasource.set(
                'id', np.arange(0, datasource['kcu'].size))

        if has_1d and ('content_pk' not in list(datasource.keys()) or
           'content_type' not in list(datasource.keys())):
            content_pk, content_type =\
                cls.get_1d_object_info(datasource, id_mapper)

            if 'content_pk' not in list(datasource.keys()):
                datasource.set('content_pk', content_pk)
            if 'content_type' not in list(datasource.keys()):
                datasource.set('content_type',
                               [x.encode('ascii') for x in content_type])

        if 'line_coords' not in list(datasource.keys()):
            line = as_numpy_array(datasource['line'])
            x, y = as_numpy_array(node_coordinates[0]),\
                as_numpy_array(node_coordinates[1])
            datasource.set('line_coords', np.array(
                [x[line[0]], y[line[0]], x[line[1]], y[line[1]]]))

        if has_1d and 'line_geometries' not in list(datasource.keys()):
            line_geometries = cls.make_line_geometries(datasource,
                                                       threedi_datasource)
            datasource.set('line_geometries', np.array(line_geometries))


class PrepareChannels(object):

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        line_group = h5py_file['lines']

        content_pk = line_group['content_pk'].value
        content_type = line_group['content_type'].value

        channels_field_names = [
            'pk', 'code', 'calculation_type', 'dist_calc_points',
            'connection_node_start_pk', 'connection_node_end_pk',
            'zoom_category'
        ]

        channels_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.v2_channels, channels_field_names)

        add_or_update_datasets(
            line_group, channels_numpy_array_dict,
            channels_field_names,
            channels_numpy_array_dict['pk'], content_pk,
            ignore_mask=content_type != 'v2_channel')


class PreparePipes(object):

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        line_group = h5py_file['lines']
        content_pk = line_group['content_pk'].value
        content_type = line_group['content_type'].value

        pipes_field_names = [
            'pk', 'display_name',
            'invert_level_start_point',
            'invert_level_end_point',
            'friction_type', 'friction_value',
            'sewerage_type', 'calculation_type',
            'connection_node_start_pk',
            'connection_node_end_pk', 'zoom_category',
            'cross_section_definition__db_width',
            'cross_section_definition__db_height',
            'cross_section_definition__db_shape']

        pipes_field_name_override = {
            'cross_section_definition__db_width': 'cross_section_width',
            'cross_section_definition__db_height': 'cross_section_height',
            'cross_section_definition__db_shape': 'cross_section_shape'}

        pipes_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.v2_pipes, pipes_field_names)

        add_or_update_datasets(
            line_group, pipes_numpy_array_dict,
            pipes_field_names,
            pipes_numpy_array_dict['pk'], content_pk,
            ignore_mask=content_type != 'v2_pipe',
            field_name_override=pipes_field_name_override)


class PrepareWeirs(object):

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        line_group = h5py_file['lines']
        content_pk = line_group['content_pk'].value
        content_type = line_group['content_type'].value

        weirs_field_names = [
            'pk', 'code', 'display_name',
            'discharge_coefficient_negative',
            'discharge_coefficient_positive',
            'sewerage', 'friction_type', 'friction_value',
            'crest_type', 'crest_level',
            'connection_node_start_pk', 'connection_node_end_pk',
            'zoom_category'
        ]

        weirs_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.v2_weirs, weirs_field_names)

        add_or_update_datasets(
            line_group, weirs_numpy_array_dict,
            weirs_field_names,
            weirs_numpy_array_dict['pk'], content_pk,
            ignore_mask=content_type != 'v2_weir')


class PrepareOrifices(object):

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        line_group = h5py_file['lines']
        content_pk = line_group['content_pk'].value
        content_type = line_group['content_type'].value

        orifices_field_names = [
            'pk', 'display_name', 'sewerage', 'max_capacity',
            'friction_type', 'friction_value',
            'discharge_coefficient_negative',
            'discharge_coefficient_positive',
            'crest_type', 'crest_level',
            'connection_node_start_pk', 'connection_node_end_pk',
            'zoom_category'
        ]

        orifices_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.v2_orifices, orifices_field_names)

        add_or_update_datasets(
            line_group, orifices_numpy_array_dict,
            orifices_field_names,
            orifices_numpy_array_dict['pk'], content_pk,
            ignore_mask=content_type != 'v2_orifice')


class PrepareCulverts(object):

    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        line_group = h5py_file['lines']
        content_pk = line_group['content_pk'].value
        content_type = line_group['content_type'].value

        culverts_field_names = [
            'pk', 'code', 'display_name',
            'discharge_coefficient_negative',
            'discharge_coefficient_positive',
            'friction_type', 'friction_value',
            'invert_level_start_point',
            'invert_level_end_point',
            'calculation_type', 'dist_calc_points',
            'connection_node_start_pk', 'connection_node_end_pk',
            'zoom_category',
            'cross_section_definition__db_width',
            'cross_section_definition__db_height',
            'cross_section_definition__db_shape']

        culverts_field_name_override = {
            'cross_section_definition__db_width': 'cross_section_width',
            'cross_section_definition__db_height': 'cross_section_height',
            'cross_section_definition__db_shape': 'cross_section_shape'}

        culverts_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.v2_culverts, culverts_field_names)

        add_or_update_datasets(
            line_group, culverts_numpy_array_dict,
            culverts_field_names,
            culverts_numpy_array_dict['pk'], content_pk,
            ignore_mask=content_type != 'v2_culvert',
            field_name_override=culverts_field_name_override)
