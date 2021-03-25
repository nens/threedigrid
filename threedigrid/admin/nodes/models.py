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
import itertools

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
        self.class_kwargs["transform"] = kwargs.get("transform")
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

    @property
    def transform(self):
        """Return the affine transformation that maps pixels to coordinates.

        The six returned values (a, b, c, d, e, f) map pixels (i, j) to
        coordinates x, y as follows::

        >>> x = a * i + b * j + c
        >>> y = d * i + e * j + f

        Note that for older gridadmin files, the transform will be derived
        from the pixel_coords and cell_coords.
        """
        if self.class_kwargs["transform"] is None:
            self.class_kwargs["transform"] = self._compute_transform()
        return self.class_kwargs["transform"]

    def _compute_transform(self):
        """Compute geotransform from pixel_coords and cell_coords"""
        nodes = self._datasource
        idx = np.where(nodes["node_type"][:] == 1)[0]

        # find two cells that have different x and y coordinates
        cell_1_px = nodes["pixel_coords"][:, idx[0]]
        cell_1_m = nodes["cell_coords"][:, idx[0]]
        for _idx in idx[1:]:
            cell_2_px = nodes["pixel_coords"][:, _idx]
            if cell_1_px[0] != cell_2_px[0] and cell_1_px[1] != cell_2_px[1]:
                break
        else:
            raise RuntimeError(
                "Unable to determine transform of gridadmin pixel_coords"
            )
        cell_2_m = nodes["cell_coords"][:, _idx]

        # compute the centers
        center_1_px = (cell_1_px[:2] + cell_1_px[2:]) / 2
        center_1_m = (cell_1_m[:2] + cell_1_m[2:]) / 2
        center_2_px = (cell_2_px[:2] + cell_2_px[2:]) / 2
        center_2_m = (cell_2_m[:2] + cell_2_m[2:]) / 2

        # compute pixel size
        size = (center_2_m - center_1_m) / (center_2_px - center_1_px)
        if abs(size[0]) != abs(size[1]):
            raise ValueError("Gridadmin cells have non-square pixels.")

        # compute origin
        origin_1 = center_1_m - center_1_px * size
        origin_2 = center_2_m - center_2_px * size
        if np.any(origin_1 != origin_2):
            raise ValueError("Gridadmin cells have tilt.")

        return size[0], 0.0, origin_1[0], 0.0, size[1], origin_1[1]

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

    def get_px_extent(self):
        """Determine the extent of the cells (in pixels)

        The returned bounding box is left-exclusive; cells cover the
        the half-open intervals [xmin, xmax) and [ymin, ymax).

        :return: tuple of xmin, ymin, xmax, ymax or None
        """
        coords = self.pixel_coords
        mask = ~np.any(coords == -9999, axis=0)
        if not np.any(mask):
            return
        xmin = coords[0, mask].min()
        ymin = coords[1, mask].min()
        xmax = coords[2, mask].max()
        ymax = coords[3, mask].max()
        return xmin, ymin, xmax, ymax

    def iter_by_px_window(self, width, height):
        """Iterate over groups of cells given a window shape (in pixels).

        :param width: the width of the window in pixels
        :param height: the height of the window in pixels

        :yield: extent, Cells
        """
        # determine the width of the largest cell
        cell_size = self.pixel_width.max()
        if width % cell_size != 0 or height % cell_size != 0:
            raise ValueError(
                "width and height should be a multiple of {}".format(cell_size)
            )

        # determine the total extent of the 2d nodes
        xmin, ymin, xmax, ymax = self.get_px_extent()

        # determine the amount of rows and cols
        n_rows = np.ceil((ymax - ymin) / height).astype(int)
        n_cols = np.ceil((xmax - xmin) / width).astype(int)

        # loop over the windows
        # for window_i, window_j in itertools.product(range(n_cols), range(n_rows)):
        #     i1, j1, i2, j2 = (
        #         window_i * width + xmin,
        #         window_j * height + ymin,
        #         (window_i + 1) * width + xmin,
        #         (window_j + 1) * height + ymin,
        #     )
        #         result = self.filter(
        #             pixel_coords__intersects_bbox=(x1 + 1, y1 + 1, x2 - 1, y2 - 1)
        #         )
        #         if result is not None:
        #             yield (x1, y1, x2, y2), result

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
        self.class_kwargs["n2dtot"] = kwargs["n2dtot"]
        self.class_kwargs["dx"] = kwargs["dx"]

    @property
    def n2dtot(self):
        return self.class_kwargs["n2dtot"]

    @property
    def dx(self):
        return self.class_kwargs["dx"]

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
