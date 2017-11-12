"""
Parse (binary) files generated by make_grid and output the data in various
forms.
"""
import logging
import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import json
from collections import namedtuple
from collections import OrderedDict
from abc import ABCMeta
from abc import abstractmethod

import numpy as np
from numpy.ma import masked_where
import ogr
from pyproj import transform, Proj

# from threedi_utils.gis import get_extent, get_bbox
from threedi_grid.utils import get_spatial_reference
from threedi_grid.utils import pairwise

from threedi_grid.exceptions import NotConsistentException
from threedi_grid import constants

logger = logging.getLogger(__name__)


Slice = namedtuple("Slice", 'start, end')


DATASOURCE_FIELD_TYPE = {
    'int': ogr.OFTInteger,
    'str': ogr.OFTString,
    'real': ogr.OFTReal,
}

# class LineKcuFilters:
#     """
#     Some explanation on KCU types. Every flowline has an kcu value
#     to distinguish between the type of lines. In threedicore this
#     distinguishing will result in the use of different formulation
#     for velocities on these lines
#     -1 - 1D boundary
#     0 - 1D embedded line
#     1 - 1D isolated line
#     2 - 1D connected line
#     3 - 1D long-crested structure
#     4 - 1D short-crested structure
#     5 - 1D double connected line
#     51 - 1D2D single connected line with storage
#     52 - 1D2D single connected line without storage
#     53 - 1D2D double connected line with storage
#     54 - 1D2D double connected line without storage
#     55 - 1D2D connected line possible breach
#     56 - 1D2D connected line active breach
#     100 - 2D line
#     101 - 2D obstacle (levee) line
#     """
#
#     def __init__(self, array):
#
#         self.lines = array['line']
#         self.kcu = array['kcu']
#
#     def filter_1d_links(self):
#         return masked_where(
#             (self.tiled_kcu > 0) & (self.tiled_kcu < 10),
#             self.lines, copy=False)
#
#     def filter_all_2d_open_water_links(self):
#         return masked_where(
#             (self.tiled_kcu == 100) | (self.tiled_kcu == 101),
#             self.lines, copy=False)
#
#     def filter_2d_groundwater_links(self):
#         return masked_where(
#             self.tiled_kcu == -150, self.lines, copy=False
#         )
#
#     def filter_2d_vertical_links(self):
#         return masked_where(
#             self.tiled_kcu == 150, self.lines, copy=False
#         )
#
#     def filter_1D_bounds(self):
#         return masked_where(
#             self.tiled_kcu == -1, self.lines, copy=False
#         )
#
#     def filter_2d_bounds(self):
#         return masked_where(
#             (self.tiled_kcu >= 200) | (self.tiled_kcu < 600),
#             self.lines, copy=False
#         )
#
#     def filter_all_structures(self):
#         structure_mask = np.logical_or(self.kcu == 3,  self.kcu == 4)
#         return np.vstack((self.lines[0][mask], self.lines[1][mask]))
#
#     def filter_long_crested_structures(self):
#         return masked_where(
#             self.tiled_kcu == 3, self.lines, copy=False
#         )
#
#     def filter_short_crested_structures(self):
#         return masked_where(
#             self.tiled_kcu == 4, self.lines, copy=False
#         )
#
#     def filter_2d_open_water_obstacles(self):
#         return masked_where(
#             self.tiled_kcu == 101, self.lines, copy=False
#         )
#
#     def filter_1d2d_open_water_links(self):
#         return masked_where(
#             (self.tiled_kcu >= 51) & (self.tiled_kcu <= 56),
#             self.lines, copy=False
#         )
#
#     def filter_1d2d_groundwater_links(self):
#         # not implemented yet
#         return masked_where(
#             (self.tiled_kcu == 57) | (self.tiled_kcu == 58),
#             self.lines, copy=False
#         )
#
#     def filter_2d_groundwater_bounds(self):
#         # not implemented yet
#         return masked_where(
#             self.tiled_kcu > 600, self.lines, copy=False
#         )


class KCUDescriptor(dict):

    def __init__(self, *arg, **kw):
        super(KCUDescriptor, self).__init__(*arg, **kw)
        self.bound_keys_groundwater = [x for x in xrange(600, 1000)]
        self.bound_keys_2d = [x for x in xrange(200, 600)]

        self._descr = {
            -1: '1D boundary',
            0: '1D embedded line',
            1: '1D isolated line',
            2: '1D connected line',
            3: '1D long-crested structure',
            4: '1D short-crested structure',
            5: '1D double connected line',
            51: '1D2D single connected line with storage',
            52: '1D2D single connected line without storage',
            53: '1D2D double connected line with storage',
            54: '1D2D double connected line without storage',
            55: '1D2D connected line possible breach',
            56: '1D2D connected line active breach',
            57: '1D2D groundwater link',
            58: '1D2D groundwater link # diff to 57? ',
            100: '2D line',
            101: '2D obstacle (levee) line',
            150: '2D vertical link',
            -150: '2D groundwater link',
            200: '2D boundary',
        }

    def get(self, item):
        return self.__getitem__(item)

    def values(self):
        v = self._descr.values()
        v.extend(['2D boundary', '2D groundwater boundary'])
        return v

    def keys(self):
        k = self._descr.keys()
        k += self.bound_keys_2d
        k += self.bound_keys_groundwater
        return k

    def __getitem__(self, item):
        if item in self.bound_keys_2d:
            return '2D boundary'
        elif item in self.bound_keys_groundwater:
            return '2D groundwater boundary'
        v = self._descr.get(item)
        if not v:
            raise KeyError(item)
        return v



def transform_xys(current_epsg, target_epsg, x_array, y_array):
    """
    """
    projections  = []
    for epsg_code in (current_epsg, target_epsg):
        epsg_str = 'epsg:{}'.format(epsg_code)
        projection = Proj(init=epsg_str)
        projections.append(projection)
    x_coords, y_coord = transform(
        projections[0], projections[1], x_array, y_array
    )
    return x_coords, y_coord


class BaseGridObject:
    __metaclass__ = ABCMeta

    _NAMES = None  # OrderedDict

    SLICE_NAMES = None          # _NAMES.values()
    THREEDICORE_NAMES = None    # _NAMES.keys()

    def __init__(self, array, meta):
        self._array = array
        self._meta = meta
        self.starts_at = None  # 0 or 1 based array
        self.filters = {}

    @property
    def _fields(self):
        return self._array.dtype.names

    @abstractmethod
    def _custom_fields(self):
        pass

    @property
    def fields(self):
        return self._fields + self._custom_fields

    @abstractmethod
    def get(self):
        pass

    @property
    def available_filters(self):
        return self.filters.keys()

    def _set_cnt_attr(self):
        """
        sets the count for each slice on the instance, e.g self.count_2D_open_water
        """
        for n in self.SLICE_NAMES:
            setattr(
                self,
                'count_{}'.format(n),
                self.filters[n].stop - self.filters[n].start
            )

    def _set_bool_attr(self):
        """
        sets the truth value for each slice on the instance, e.g self.has_2D_open_water
        """
        for n in self.SLICE_NAMES:
            setattr(
                self,
                'has_{}'.format(n),
                self.filters[n].stop > self.filters[n].start
            )

    @staticmethod
    def cond_add(start, length, length_next):
        end = start + (length - 1 if length > 0 else 0)
        new_start = end + (1 if length_next > 0 else 0)
        return end, new_start

    def _define_filters(self, start_value, check_value):
        """
        """
        names = self.THREEDICORE_NAMES + [0]
        pairs = pairwise([self._meta[n][0] if n else 0 for n in names])
        end = None
        start = start_value
        for i, p in enumerate(pairs):
            end, start_nxt = self.cond_add(start, p[0], p[1])
            self.filters[self.SLICE_NAMES[i]] = slice(start, end)
            start = start_nxt

        if end != check_value:
            raise NotConsistentException(
                'Expected end value of {}, got {}'.format(
                    check_value, end)
            )

    def _pack_up(self, content, stack):
        if stack:
            return np.vstack(tuple(content))
        return content


class Nodes(BaseGridObject):

    _NAMES = OrderedDict(
        [('n2dtot', '2D_open_water'), ('ngrtot', '2D_groundwater'),
         ('n1dtot', '1D_all'), ('n2dobc', '2D_groundwater_bounds'),
         ('ngr2bc', '2D_open_water_bounds'),
         ('n1dobc', '1D_bounds')]
    )

    SLICE_NAMES = _NAMES.values()
    THREEDICORE_NAMES = _NAMES.keys()

    def __init__(self, array, meta):

        super(Nodes, self).__init__(array, meta)
        self.filters = {}
        self.starts_at = 0
        self._define_filters(
            start_value=self.starts_at,
            check_value=self._meta['nodall'][0] - 1
        )
        self._set_bool_attr()
        self._set_cnt_attr()
        self.content_pk = None

    def get(self, fields=None, filter_name=None):
        _fields = set(self.fields)
        if fields:
            _fields = _fields.intersection(
                set(fields.strip().split(','))
            )
        _filter = self.filters.get(filter_name, None)
        if _filter is None:
            _filter = slice(
                self.starts_at, self._meta['nodall'][0] - 1
            )

        selection = OrderedDict()
        for n in _fields:
            try:
                selection[n] = self._array[n][_filter]
            except ValueError:
                selection[n] = getattr(self, n)[self.starts_at:][_filter]
        return selection

    # def get_slice(self, slice_name, stack=True):
    #     try:
    #         k = self.slices[slice_name]
    #     except KeyError:
    #         logger.error(
    #             "[!] Could not get data for {}. Valid choices are {}".format(
    #                 slice_name, self.SLICE_NAMES)
    #         )
    #         return
    #
    #     if not getattr(self, 'has_{}'.format(slice_name)):
    #         logger.info('[*] Model does not have {}'.format(slice_name))
    #         return
    #     selection = [self._array[n][k] for n in self.fields]
    #     return self._pack_up(selection, stack)
    #
    # def get_values(self, field_name, slice_name=''):
    #     if field_name not in self.fields:
    #         logger.error("[-] Field name {} does not exist".format(field_name))
    #         return
    #     if slice_name and slice_name not in self.SLICE_NAMES:
    #         logger.error("[-] Slice  name {} does not exist".format(slice_name))
    #         return
    #
    #     if not slice_name:
    #         return self._array[field_name][self.starts_at:]
    #     return self._array[field_name][self.slices[slice_name]]
    #
    # def get_reprojected(self, src_epsg_code, target_epsg_code, slice_name='',
    #                     stack=True):
    #     node_x = self.get_values('x', slice_name=slice_name)
    #     node_y = self.get_values('y', slice_name=slice_name)
    #     return self._pack_up(
    #         transform_xys(src_epsg_code, target_epsg_code, node_x, node_y),
    #         stack
    #     )

    def add_node_pks(self, mapping1d, id_mapper):

        # pk template
        self.content_pk = np.zeros(
            mapping1d['nend1d'].shape, dtype='i4'
        )

        # with argsort
        sort_idx = np.argsort(mapping1d['nend1d'])
        idx = sort_idx[np.searchsorted(
            mapping1d['nend1d'],
            id_mapper.id_mapping[
                id_mapper.obj_slices['v2_connection_nodes']]['seq_id'],
            sorter=sort_idx)]

        self.content_pk[idx] = id_mapper.id_mapping[
            id_mapper.obj_slices['v2_connection_nodes']]['pk']

    @property
    def _custom_fields(self):
        field_is_set = []
        custom_field_names = ('content_pk',)
        for fn in custom_field_names:
            attr = getattr(self, fn)
            if hasattr(attr, 'dtype'):
                field_is_set.append(fn)
        return tuple(field_is_set)


class Lines(BaseGridObject):

    _NAMES = OrderedDict(
        [('liutot', '2D_open_water_x'),
         ('livtot', '2D_open_water_y'),
         ('ngrtot', 'vertical'),
         ('lgutot', '2D_groundwater_x'),
         ('lgvtot', '2D_groundwater_y'),
         ('l1dtot', '1D_all'),
         #('infl1d', '1D_2D_open_water'),
         ('ingrw1d', '1D_2D_groundwater'),
         ('n2dobc', '2D_open_water_bounds'),
         ('ngr2bc', '2D_groundwater_bounds'),
         ('n1dobc', '1D_bounds')]
    )

    SLICE_NAMES = _NAMES.values()
    THREEDICORE_NAMES = _NAMES.keys()

    def __init__(self, array, meta):

        super(Lines, self).__init__(array, meta)
        self.filters = {}
        self.starts_at = 1
        self._define_filters(
            start_value=self.starts_at,
            check_value=self._meta['linall'][0]
        )
        self._add_kcu_filters()
        self._set_bool_attr()
        self._set_cnt_attr()
        self.content_pk = None
        self.content_type = None

    @property
    def _custom_fields(self):
        field_is_set = []
        custom_field_names = ('content_pk', 'content_type')
        for fn in custom_field_names:
            attr = getattr(self, fn)
            if hasattr(attr, 'dtype'):
                field_is_set.append(fn)
        return tuple(field_is_set)

    def get(self, fields=None, filter_name=None):
        _fields = set(self.fields)
        if fields:
            _fields = _fields.intersection(
                set(fields.strip().split(','))
            )
        _filter = self.filters.get(filter_name, None)
        if _filter is None:
            _filter = slice(
                self.starts_at, self._meta['linall'][0]
            )

        selection = OrderedDict()
        for n in _fields:
            try:
                if n == 'line':
                    selection[n] = self._array[n][:, _filter]
                else:
                    selection[n] = self._array[n][_filter]
            except ValueError:
                selection[n] = getattr(self, n)[self.starts_at:][_filter]
        return selection

    def add_1d_object_info(self, id_mapper):
        """
        applies only for 1d
        :return:
        """

        # TODO channel might be different
        LINE_TYPES = [
            constants.TYPE_V2_PIPE, constants.TYPE_V2_CHANNEL,
            constants.TYPE_V2_CULVERT,
            constants.TYPE_V2_ORIFICE, constants.TYPE_V2_WEIR]

        # pk template
        lik_all = self.get('lik')
        lik_1d = self.get('lik', '1D_all')

        self.content_pk = np.zeros(lik_all['lik'].shape, dtype='i4')
        self.content_type = np.zeros(lik_all['lik'].shape, dtype='U32')
        _content_pk = np.zeros(lik_1d['lik'].shape, dtype='i4')
        _content_type = np.zeros(lik_1d['lik'].shape, dtype='U32')

        sort_idx = np.argsort(lik_1d['lik'])

        for line in LINE_TYPES:
            mapper_idx = id_mapper.obj_slices.get(line)
            if mapper_idx is None:
                continue
            seq_ids = id_mapper.id_mapping[mapper_idx]['seq_id']
            idx = sort_idx[np.searchsorted(lik_1d['lik'], seq_ids, sorter=sort_idx)]
            _content_pk[idx] = id_mapper.id_mapping[mapper_idx]['pk']
            _content_type[idx] = id_mapper.id_mapping[mapper_idx]['obj_name']
        self.content_pk[self.filters['1D_all']] = _content_pk
        self.content_type[self.filters['1D_all']] = _content_type

    def _add_kcu_filters(self):
        self.filters['structures'] = np.logical_or(
            self._array['kcu'] == 3,  self._array['kcu'] == 4)

        self.filters['long_crested_structures'] = np.where(
            self._array['kcu'] == 3)

        self.filters['short_crested_structures'] = np.where(
            self._array['kcu'] == 4)

        self.filters['2d_open_water_obstacles'] = np.where(
            self._array['kcu'] == 101)

        self.filters['active_breach'] = np.where(
            self._array['kcu'] == 56)


    # def get_by_filter(self, filter_name='active_breach', fields=''):
    #     mask = getattr(self, '_{}_mask'.format(filter_name))
    #
    #     _fields = set(self.fields + self._custom_fields)
    #     if fields:
    #         _fields = set([fields]).intersection(_fields)
    #     selection = OrderedDict()
    #     for n in _fields:
    #         if n == 'line':
    #             line_values = self.get_values(n)
    #             selection['node_a'] = (line_values[0][mask])
    #             selection['node_b'] = (line_values[1][mask])
    #         else:
    #             selection[n] = (self.get_values(n)[mask])
    #     return selection

    @property
    def _custom_fields(self):
        field_is_set = []
        custom_field_names = ('content_pk', 'content_type')
        for fn in custom_field_names:
            attr = getattr(self, fn)
            if hasattr(attr, 'dtype'):
                field_is_set.append(fn)
        return tuple(field_is_set)

class GridParser(object):

    def __init__(self, ini_file_path, file_path, id_mapping, epsg_code=28992):
        self.file_path =  file_path
        self.epsg_code = epsg_code

        self.parser = configparser.ConfigParser()
        self.parser.read(ini_file_path)

        self.meta = None

        # structured numpy arrays, containing node information
        self._nodes = None
        self.nodes = None

        # structured numpy arrays containing line information
        self._lines = None
        self.lines = None

        # structured numpy arrays containing 2D cell information
        self.cells2d = None

        # structured numpy arrays containing pump information
        self.pumps = None

        self.mapping1d = None
        self.breaches = None
        self.id_mapping = None
        self.id_mapper = None
        if id_mapping:
            self.id_mapper = IdMapper(id_mapping)

        # numpy array of shape mapping_1d['nend1d'].shape. Will be populated
        # in _add_connection_node_pks()
        self.node_pks = None

    def get_node_pks(self, nodes):
        """
        get pks for the given node collection
        :return:
        """

        seq_ids = self.mapping1d['nend1d'][nodes]
        # template
        _tmpl = np.zeros(seq_ids.shape, dtype='i4')

        # with argsort
        sort_idx = np.argsort(seq_ids)
        idx = sort_idx[np.searchsorted(
            seq_ids,
            self.id_mapper.id_mapping[
                self.id_mapper.obj_slices['v2_connection_nodes']]['seq_id'],
            sorter=sort_idx)]

        _tmpl[idx] = self.id_mapper.id_mapping[
            self.id_mapper.obj_slices['v2_connection_nodes']]['pk']
        return _tmpl

    def _get_dt(self, block_name):
        """
        """
        dt_l = []
        for item in self.parser.sections():
            if not item.startswith(block_name):
                continue

            block, name = item.split('.')
            dims = tuple(json.loads(self.parser.get(item, 'dimensions')))
            dt_l.append(
                (str(name), (str(self.parser.get(item, 'datatype')), dims))
            )
        return np.dtype(dt_l)

    def parse(self):
        """
        parse the grid.admin file
        """
        validation_value = validation_incre = 10

        try:
            with open(self.file_path, 'rb') as f:

                data = self.seek_file(f, 'meta')
                self.meta = data
                self._validate_block(f, validation_value)
                validation_value += validation_incre

                # section names, attribute names and conditions as to read the section or not
                sections = [
                    ('nodes', '_nodes', True), ('cells2d', 'cells2d', True),
                    ('lines', '_lines', True), ('pumps', 'pumps', self.meta['jap1d'][0] > 0),
                    ('mapping1d', 'mapping1d', any([self.meta['l1dtot'][0], self.meta['n1dtot'][0]]) > 0),
                    ('breaches', 'breaches', self.meta['levnms'][0] > 0)
                ]

                for section, attr_name, condition in sections:
                    if condition:
                        data = self.seek_file(f, section)
                        # will produce attributes like so:
                        # self.nodes = <numpy.array>
                        setattr(self, attr_name, data)
                    self._validate_block(f, validation_value)
                    validation_value += validation_incre

        except IOError:
            logger.exception('[-] Could not read grid file')

        self._finalize_data()

    def _finalize_data(self):
        self.pumps['nodp1d'][:] -= 1
        # references to node index from fortran point of view starting with 1.
        # To integrate flawlessly correct here
        self._lines['line'][:] -= 1
        # TODO check if we still need this
        # self.line_filters = LineKcuFilters(self._lines)
        self.lines = Lines(self._lines, self.meta)
        self.nodes = Nodes(self._nodes, self.meta)

        if self.id_mapper:
            # TODO maybe not the right spot to call these functions
            self.nodes.add_node_pks(self.mapping1d, self.id_mapper)
            self.lines.add_1d_object_info(self.id_mapper)

    def seek_file(self, f, section):
        """
        :param f: file object of the grid.admin file
        :param dtype: numpy datatype definition

        Helper function for parsing the file and updating results in a
        dict.
        """
        dtype = self._get_dt(section)
        record_arr = np.fromfile(f, dtype, count=1)
        return record_arr[0]

    def _validate_block(self, f, check_number, check_str=''):
        """
        :param check_number: TODO
        """

        if not check_str:
            check_str = "check{}".format(check_number)

        dt = np.dtype([
            (check_str, constants.DTYPE_INT)])
        record_arr = np.fromfile(f, dt, count=1)

        if record_arr[check_str] != check_number:
            raise NotConsistentException("{}".format(check_number))

    def get_line_coords(self, method_type, name, target_epsg_code='28992'):
        if method_type == 'get_slice':
            if name and name not in self.lines.SLICE_NAMES:
                logger.error("[-] Slice  name {} does not exist".format(name))
                return
            nodes = self.lines.get_values('line', name)

        elif method_type == 'get_by_filter':
            # TODO validation
            res = self.lines.get_by_filter(name, 'line')
            nodes = res.values()

        if target_epsg_code != self.epsg_code:
            node_coords = self.nodes.get_reprojected(
                self.epsg_code, target_epsg_code).T
        else:
            node_coords = self.nodes.get_all().T
        return node_coords[nodes[0]], node_coords[nodes[1]]

    def create_node_shape(self, slice='', target_epsg_code='28992'):

        geomtype = 0
        output_points = 'nodes_wgs.shp'
        sr = get_spatial_reference(target_epsg_code)
        # points
        driver = ogr.GetDriverByName("ESRI Shapefile")
        if os.path.exists(output_points):
            logger.info('Replacing %s', output_points)
            driver.DeleteDataSource(str(output_points))
        data_source = driver.CreateDataSource(output_points)
        layer = data_source.CreateLayer(
            str(os.path.basename(output_points)),
            sr,
            geomtype
        )

        layer.CreateField(ogr.FieldDefn("nod_id",
                                        DATASOURCE_FIELD_TYPE['int']))
        # layer.CreateField(ogr.FieldDefn("calc", DATASOURCE_FIELD_TYPE['int']))
        layer.CreateField(ogr.FieldDefn("type", DATASOURCE_FIELD_TYPE['str']))
        layer.CreateField(ogr.FieldDefn("con_nod",
                                        DATASOURCE_FIELD_TYPE['int']))
        layer.CreateField(ogr.FieldDefn("con_nod_pk",
                                        DATASOURCE_FIELD_TYPE['int']))
        _definition = layer.GetLayerDefn()

        # all nodes
        cnt = start_id = self.meta['nodall'][0]

        # process a subset of nodes
        if slice:
            if not getattr(self.nodes, 'has_{}'.format(slice)):
                logger.error(
                    '[*] Can not create shape, model does not have {}'.format(
                        slice)
                )
                return
            cnt = getattr(self.nodes, 'count_{}'.format(slice))
            start_id = self.nodes.slices[slice].start
        if target_epsg_code != self.epsg_code:
            node_coords = self.nodes.get_reprojected(
                self.epsg_code, target_epsg_code, slice_name=slice
            ).T
        else:
            node_coords = self.nodes.get_all().T

        seq_ids = self.mapping1d['nend1d'][self.nodes.slices['1D_all']]
        node_pks = self.node_pks[self.nodes.slices['1D_all']]

        for i in xrange(cnt):
            nod_id = start_id + i
            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint(node_coords[i][0], node_coords[i][1])
            feature = ogr.Feature(_definition)
            feature.SetGeometry(point)
            feature.SetField("nod_id", int(nod_id))
            feature.SetField("type", constants.NODE_TYPE_1D)
            feature.SetField("con_nod", int(seq_ids[i]))
            feature.SetField("con_nod_pk", int(node_pks[i]))
            layer.CreateFeature(feature)

    def save_line_data(self, output_format='shapefile', slice='', target_epsg_code='28992'):
        # TODO add other formats like HDF5
        func_dict = {
            'shapefile': '_create_line_shape',
            'hdf5': '_create_line_hdf5'
        }

        func = func_dict.get(output_format)
        getattr(self, func)(slice, target_epsg_code)

    def _collect_line_data(self, slice):
        nodes = self.lines.get_values('line', slice)
        return {
            'nodes': nodes,
            'nodes_a': nodes[0],
            'nodes_b': nodes[1],
            'node_pks_a': self.get_node_pks(nodes[0]),
            # node_pks_b': self.get_node_pks(nodes_b)
            'line_type_int': self.lines.get_values('kcu', slice),
            'seq_id': self.lines.get_values('lik', slice),
            'content_type': self.lines.get_values('content_type', slice),
            'content_pk': self.lines.get_values('content_pk', slice)
        }

    def _create_line_hdf5(self, slice='', target_epsg_code='28992'):

        # TODO clear all offset issues!!! like this only slices work,
        # otherwise we have to do [1:] basically everywhere
        data = self._collect_line_data(slice)
        node_coords_a, node_coords_b= self.get_line_coords('get_slice', slice, target_epsg_code)
        data.update({'node_coords_a': node_coords_a, 'node_coords_b': node_coords_b})
        # TODO create dataset or group or whatever

    def _create_line_shape(self, slice='', target_epsg_code='28992'):

        kcu_dict = KCUDescriptor()
        geomtype = 0
        output_lines = 'lines.shp'
        sr = get_spatial_reference(target_epsg_code)
        # points
        driver = ogr.GetDriverByName("ESRI Shapefile")
        if os.path.exists(output_lines):
            logger.info('Replacing %s', output_lines)
            driver.DeleteDataSource(str(output_lines))
        data_source = driver.CreateDataSource(output_lines)
        layer = data_source.CreateLayer(
            str(os.path.basename(output_lines)),
            sr,
            geomtype
        )
        fields = OrderedDict([
            ('link_id', 'int'),
            ('kcu', 'int'),
            ('kcu_descr', 'str'),
            ('node_a', 'int'),
            ('node_b', 'int'),
            ('node_a_pk', 'int'),
            ('node_b_pk', 'int'),
            ('cont_type', 'str'),
            ('cont_pk', 'int'),
            ('seq_id', 'int')
        ])
        for field_name, field_type in fields.iteritems():
            layer.CreateField(
                ogr.FieldDefn(
                    field_name, DATASOURCE_FIELD_TYPE[field_type]
                )
            )
        _definition = layer.GetLayerDefn()

        # all nodes
        cnt = start_id = self.meta['linall'][0] - 1

        # process a subset of nodes
        if slice:
            if not getattr(self.lines, 'has_{}'.format(slice)):
                logger.error(
                    '[*] Can not create shape, model does not have {}'.format(
                        slice)
                )
                return
            cnt = getattr(self.lines, 'count_{}'.format(slice))
            start_id = self.lines.slices[slice].start

        # TODO clear all offset issues!!! like this only slices work,
        # otherwise we have to do [1:] basically everywhere

        # node_coords_a, node_coords_b= self.get_line_coords('get_slice', slice, target_epsg_code)
        # nodes = self.lines.get_values('line', slice)
        # nodes_a = nodes[0]
        # nodes_b = nodes[1]
        # node_pks_a = self.get_node_pks(nodes_a)
        # # node_pks_b = self.get_node_pks(nodes_b)
        # line_type_int = self.lines.get_values('kcu', slice)
        # seq_id = self.lines.get_values('lik', slice)
        # content_type = self.lines.get_values('content_type', slice)
        # content_pk = self.lines.get_values('content_pk', slice)
        filtered_lines = self.lines.get_by_filter('short_crested_structure')
        node_coords_a, node_coords_b= self.get_line_coords('get_by_filter', 'short_crested_structure', target_epsg_code)
        # node_pks_a = self.get_node_pks(filtered_lines['node_a'])
        # node_pks_b = self.get_node_pks(filtered_lines['node_b'])

        node_pks_a = self.node_pks(filtered_lines['node_a'])
        node_pks_b = self.node_pks(filtered_lines['node_b'])


        for i in xrange(56):
            line_id = start_id + i
            line = ogr.Geometry(ogr.wkbLineString)
            # line.AddPoint(node_a[i][0], node_a[i][1])
            # line.AddPoint(node_b[i][0], node_b[i][1])
            line.AddPoint(node_coords_a[i][0], node_coords_a[i][1])
            line.AddPoint(node_coords_b[i][0], node_coords_b[i][1])
            feature = ogr.Feature(_definition)
            feature.SetGeometry(line)
            feature.SetField("link_id", int(line_id))
            feature.SetField("kcu", int(filtered_lines['kcu'][i]))
            feature.SetField("node_a", int(filtered_lines['node_a'][i]))
            feature.SetField("node_b", int(filtered_lines['node_b'][i]))
            feature.SetField("node_a_pk", int(node_pks_a[i]))
            feature.SetField("node_b_pk", int(node_pks_b[i]))
            kcu_descr = ''
            try:
                kcu_descr = kcu_dict[int(filtered_lines['kcu'][i])]
            except KeyError:
                pass
            feature.SetField("kcu_descr", kcu_descr)
            feature.SetField("cont_type", str(filtered_lines['content_type'][i]))
            feature.SetField("cont_pk", int(filtered_lines['content_pk'][i]))
            feature.SetField("seq_id", int(filtered_lines['lik'][[i]]))
            layer.CreateFeature(feature)
        # for i in xrange(cnt):
        #     line_id = start_id + i
        #     line = ogr.Geometry(ogr.wkbLineString)
        #     # line.AddPoint(node_a[i][0], node_a[i][1])
        #     # line.AddPoint(node_b[i][0], node_b[i][1])
        #     line.AddPoint(node_coords_a[i][0], node_coords_a[i][1])
        #     line.AddPoint(node_coords_b[i][0], node_coords_b[i][1])
        #     feature = ogr.Feature(_definition)
        #     feature.SetGeometry(line)
        #     feature.SetField("link_id", int(line_id))
        #     feature.SetField("kcu", int(line_type_int[i]))
        #     feature.SetField("node_a", int(nodes_a[i]))
        #     feature.SetField("node_b", int(nodes_b[i]))
        #     feature.SetField("node_a_pk", int(node_pks_a[i]))
        #     # feature.SetField("node_b_pk", int(node_pks_b[i]))
        #     kcu_descr = ''
        #     try:
        #         kcu_descr = kcu_dict[int(line_type_int[i])]
        #     except KeyError:
        #         pass
        #     feature.SetField("kcu_descr", kcu_descr)
        #     feature.SetField("cont_type", str(content_type[i]))
        #     feature.SetField("cont_pk", int(content_pk[i]))
        #     feature.SetField("seq_id", int(seq_id[[i]]))
        #     layer.CreateFeature(feature)




#   breslocaties --> see LineKcuFilters
#   structures --> see LineKcuFilters
#       - terug naar oorsprongelijke object
#       - terug naar oorsprongelijke geometry
#
#   1D line index --> lik --> seq id 1d object  --> object type
#        inverse moet kunnen, use case: snelheid van je weir opvragen
#
#   split sqlite channel geoms by nodes on channel
#
#
#
#
#
#
# link_id --> 'linall' index
# node_left
# node_right
# kcu
# type ??
# channel_id --> lik
# content_type --> sql object
# cont_pk --> sql pk

        # layer.CreateField(
        #     ogr.FieldDefn("link_id", DATASOURCE_FIELD_TYPE['int']))
        # layer.CreateField(
        #     ogr.FieldDefn("node_left", DATASOURCE_FIELD_TYPE['int']))
        # layer.CreateField(
        #     ogr.FieldDefn("node_right", DATASOURCE_FIELD_TYPE['int']))
        # layer.CreateField(
        #     ogr.FieldDefn("kcu", DATASOURCE_FIELD_TYPE['int']))
        # layer.CreateField(
        #     ogr.FieldDefn("type", DATASOURCE_FIELD_TYPE['str']))
        # layer.CreateField(
        #     ogr.FieldDefn("channel_id", DATASOURCE_FIELD_TYPE['int']))
        # layer.CreateField(
        #     ogr.FieldDefn("cont_type", DATASOURCE_FIELD_TYPE['str']))
        # layer.CreateField(
        #     ogr.FieldDefn("cont_pk", DATASOURCE_FIELD_TYPE['int']))


class IdMapper(object):

    LINE_TYPES = [
        constants.TYPE_V2_PIPE, constants.TYPE_V2_CHANNEL,
        constants.TYPE_V2_CULVERT,
        constants.TYPE_V2_ORIFICE, constants.TYPE_V2_WEIR]

    def __init__(self, id_mapping_dict):
        self.id_mapping = None
        self.obj_slices = None
        self._process_id_mapping(id_mapping_dict)
        self._define_id_obj_slices()

    def get(self, object_name):
        idx = self.obj_slices[object_name]
        return self.id_mapping[idx]

    def _process_id_mapping(self, id_mapping_dict):
        """
        """
        self._id_mapping_input = id_mapping_dict
        self.id_mapping = np.fromiter(
            self._get_id_mapping_entry(),
            dtype={'formats':
                       ['U64', 'i4', 'i4'],
                   'names':
                       ['obj_name', 'pk', 'seq_id']},
            count=sum(len(v) for v in id_mapping_dict.itervalues())
        )

    def _define_id_obj_slices(self):
        obj_names = np.unique(self.id_mapping['obj_name'])
        self.obj_slices = {
            n: np.where(self.id_mapping['obj_name'] == n)
            for n in obj_names
        }

    def _get_id_mapping_entry(self):
        """
        """
        for k, v in self._id_mapping_input.iteritems():
            for pk, seq_id in v.iteritems():
                yield k, pk, seq_id

    def filter_by_pks(self, obj_name, seq_id):
        sl = self.obj_slices[obj_name]
        return self.id_mapping[sl]['pk'][np.where(self.id_mapping[sl]['seq_id'] == seq_id)][0]

    def line_idx_to_type_sql(self, line_idx):
        """
        Find out what type and sql_id correspond to given line_idx
        line_idx = network_channel_id in grid_admin.line_attributes
        """
        find_idx = unicode(line_idx)

        for line_type in self.LINE_TYPES:
            if line_type in self.id_mapping:
                if find_idx in self.reverse_mapping[line_type]:
                    return line_type, self.reverse_mapping[line_type][find_idx]
