# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Models
++++++

The ``Nodes`` models represent the actual calculation points of the
threedicore and derived information like the cells they lie in.

For examples how to query the ``Nodes`` model see :ref:`api-label`


"""

from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np

from threedigrid.orm.models import Model
from threedigrid.orm.fields import ArrayField
from threedigrid.orm.base.fields import BooleanArrayField
from threedigrid.orm.fields import PointArrayField
from threedigrid.orm.fields import BboxArrayField
from threedigrid.geo_utils import transform_xys
from threedigrid.numpy_utils import get_smallest_uint_dtype
from threedigrid.admin.nodes import exporters
from threedigrid.admin.nodes import subsets
from six.moves import zip


NODE_SUBSETS = {
    'node_type__eq': subsets.NODE_TYPE__EQ_SUBSETS,
    'node_type__in': subsets.NODE_TYPE__IN_SUBSETS,
}


class Nodes(Model):
    content_pk = ArrayField()
    seq_id = ArrayField()
    coordinates = PointArrayField()
    cell_coords = BboxArrayField()
    zoom_category = ArrayField()
    node_type = ArrayField()
    is_manhole = BooleanArrayField()
    sumax = ArrayField()

    SUBSETS = NODE_SUBSETS

    @property
    def connectionnodes(self):
        return self._filter_as(ConnectionNodes, content_pk__ne=0)

    @property
    def manholes(self):
        return self._filter_as(Manholes, is_manhole=True)

    @property
    def added_calculationnodes(self):
        return self._filter_as(AddedCalculationNodes, content_pk=0)

    def __init__(self, *args, **kwargs):

        super(Nodes, self).__init__(*args, **kwargs)

        self._exporters = [
            exporters.NodesOgrExporter(self),
        ]

    @property
    def locations_2d(self):
        data = self.subset('2D_open_water').data
        # x0 = 0, y0 = 0
        # Translate
        # data['coordinates'][0] += x0
        # data['coordinates'][1] += y0

        # Return [[node_id, coordinate_x + x0, coordinate_y + y0]]
        return list(zip(
            data['id'].tolist(),
            data['coordinates'][0].tolist(),
            data['coordinates'][1].tolist()))


class AddedCalculationNodes(Nodes):
    pass


class ConnectionNodes(Nodes):
    initial_waterlevel = ArrayField()
    storage_area = ArrayField()


class Manholes(ConnectionNodes):
    bottom_level = ArrayField()
    drain_level = ArrayField()
    display_name = ArrayField()
    surface_level = ArrayField()
    calculation_type = ArrayField()
    shape = ArrayField()
    width = ArrayField()
    manhole_indicator = ArrayField()


class Cells(Nodes):
    """
    Model that represents the threedicore calculation cells. ``Cells`` are
    a sub-class of ``Nodes`` because they share the same attributes.
    ``Cells``, however, also have a z_coordinate, the bottom level of
    the grid cell and cell_coords, the lower left and upper right coordinates
    of the cells extent.

    """

    z_coordinate = ArrayField()
    pixel_width = ArrayField()
    pixel_coords = BboxArrayField()

    def __init__(self, *args, **kwargs):

        super(Cells, self).__init__(*args, **kwargs)

        self._exporters = [
            exporters.CellsOgrExporter(self),
        ]

    @property
    def bounds(self):
        """
        :return: coordinates of the cell bounds (counter clockwise):
                 minx, miny, maxx, miny, maxx, maxy, minx, maxy
        """
        minx, miny, maxx, maxy = self.cell_coords
        return np.vstack(
            (minx, miny,
             maxx, miny,
             maxx, maxy,
             minx, maxy))

    def get_id_from_xy(self, x, y, xy_epsg_code=None, subset_name=None):
        """
        :param x: the x coordinate in xy_epsg_code
        :param y: the y coordinate in xy_epsg_code
        :param subset_name: filter on a subset of cells

        :return: numpy array with cell id's for x, y
        """

        if xy_epsg_code and xy_epsg_code != self.epsg_code:
            xy = transform_xys(
                np.array([x]), np.array([y]),
                xy_epsg_code, self.epsg_code).flatten()
        else:
            xy = [x, y]

        inst = self
        if subset_name:
            inst = self.subset(subset_name)
        id = inst.filter(cell_coords__contains_point=xy).id
        return id.tolist()

    def get_ids_from_pix_bbox(self, bbox, subset_name='2D_OPEN_WATER'):
        """
        :param x: the x coordinate in xy_epsg_code
        :param y: the y coordinate in xy_epsg_code
        :param subset_name: filter on a subset of cells

        :return: numpy array with cell id's for x, y
        """

        inst = self
        if subset_name:
            inst = self.subset(subset_name)
        id = inst.filter(pixel_coords__intersects_bbox=bbox).id
        return id.tolist()

    def get_nodgrid(self, pix_bbox, subset_name='2D_OPEN_WATER'):
        ids = np.array(
            self.get_ids_from_pix_bbox(pix_bbox, subset_name=subset_name),
            dtype=np.int32
        )
        nodgrid = create_nodgrid(
            self.pixel_coords[:],
            ids[:],
            int(pix_bbox[2] - pix_bbox[0]),
            int(pix_bbox[3] - pix_bbox[1]),
            int(pix_bbox[0]),
            int(pix_bbox[1])
        )
        return nodgrid[::-1, ::]

    def __repr__(self):
        return "<orm cells instance of {}>".format(self.model_name)

    def __contenttype__(self):
        return 'cells'


class Grid(Model):
    """
    Implemented fields:

        - nodm
        - nodn
        - nodk

    They all have the same size as nodes and cells, which is why this
    model lives in the nodes/model module. In fact they are attributes
    of the cell coordinates
    """

    nodm = ArrayField()  #
    nodn = ArrayField()
    nodk = ArrayField()
    ip = ArrayField()
    jp = ArrayField()

    def __init__(self, *args, **kwargs):

        super(Grid, self).__init__(*args, **kwargs)
        self.n2dtot = kwargs['n2dtot']
        self.dx = kwargs['dx']

    def get_pixel_map(self, dem_pixelsize, dem_shape):
        """
        get the node grid to pixel map

        :param dem_pixelsize: pixelsize of the geo tiff
        :param dem_shape: shape of the numpy representation of the geo tiff

        :return: flipped array of the dem_shape that matches the geotiff
        """

        # Convert nod_grid to smallest uint type possible
        dtype = get_smallest_uint_dtype(maxval=self.n2dtot)
        grid_arr = np.zeros(dem_shape, dtype=dtype)

        # applies for for 2D nodes only
        _k = self.nodk[0:self.n2dtot + 1] - 1
        _m = self.nodm[0:self.n2dtot + 1] - 1
        _n = self.nodn[0:self.n2dtot + 1] - 1

        # the size in pixels of each grid cell
        _size = self.dx[_k] / dem_pixelsize
        # corresponding node index
        _ind = np.arange(0, self.n2dtot + 1, dtype='int')

        n_slice_start = np.array(_n * _size, dtype='int')
        n_slice_end = np.array((_n * _size) + _size, dtype='int')
        n_slice = list(zip(n_slice_start, n_slice_end))
        m_slice_start = np.array(_m * _size, dtype='int')
        m_slice_end = np.array((_m * _size) + _size, dtype='int')
        m_slice = list(zip(m_slice_start, m_slice_end))

        for ns, ms, idx in zip(n_slice, m_slice, _ind):
            axis_x = slice(*ns)
            axis_y = slice(*ms)
            grid_arr[axis_x, axis_y] = idx

        # flip upside-down to match geotiff
        return grid_arr[::-1, ::]


def create_nodgrid(pixel_coords, ids, width, height, offset_i, offset_j):
    grid_arr = np.zeros((height, width), dtype=np.int32)
    for id in ids:
        i0 = np.maximum(pixel_coords[0, id], offset_i) - offset_i
        i1 = np.minimum(pixel_coords[2, id], offset_i + width) - offset_i
        j0 = np.maximum(pixel_coords[1, id], offset_j) - offset_j
        j1 = np.minimum(pixel_coords[3, id], offset_j + height) - offset_j
        grid_arr[j0:j1, i0:i1] = id
    return grid_arr
