# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import logging
from itertools import izip
from itertools import tee

import mercantile
import numpy as np
from pyproj import transform, Proj
import osr

logger = logging.getLogger(__name__)


MERCANTILE_EPSG_CODE = '4326'

BBOX_LEFT = 0
BBOX_TOP = 1
BBOX_RIGHT = 2
BBOX_BOTTOM = 3


class PKMapper(object):
    """
    Solves the following situation:

    content_pk[pk[i]] == to_map[i]

    Having two array's of the same length, with corresponding
    values:

        pk     = [1,     2,   3,   4,   5,   6]
        to_map = [1.1, 2.1, 3.1, 4.1, 5.1, 6.1]

    And an array with with (unsorted) numbers that might
    match values in pk:

        content_pk = [0, 0, 15, 3, 4, 0, 0, 1, 1, 15]


    PKMapper(pk, content_pk).apply_on(to_map, 0)

    result = [0, 0, 0, 3.1, 4.1, 0, 0, 1.1, 1.1, 0]
    """

    def __init__(self, pk, content_pk, ignore_mask=None):
        """
        :param pk: np.ndarray with pk values
        :param content_pk: np.ndarray with pk values to map to
        :param ignore_mask: boolean np.ndarray, when True the value
                            of content_pk is ignored.
        """
        # NOTE: pk should only contain unique values

        # create copies of pk an content_pk and
        # add -1 to front of pk
        # This value serves as a trash value and will be returned
        # when values in content_pk are 0 or not in pk.
        content_pk_copy = np.array(content_pk)
        pk_copy = np.concatenate((np.array([-1]), pk))

        # Apply the boolean_mask if given
        if isinstance(ignore_mask, np.ndarray):
            content_pk_copy[ignore_mask] = -1

        # Set content_pk_copy[i] = -1 if the value at i is not in pk
        content_pk_copy[np.invert(np.isin(content_pk_copy, pk))] = -1

        # sort and create an array with indices of pk
        # on content_pk
        sort_idx = np.argsort(pk_copy)
        self._indices = sort_idx[
            np.searchsorted(
                pk_copy, content_pk_copy, sorter=sort_idx)]

        # Note: self._indices[i] == 0 when the content_pk[i] could not
        # be found in pk

        del content_pk_copy
        del pk_copy

    def apply_on(self, np_array, null_value=0):
        """
        Apply the filter on np_array.

        :param np_array: the np.ndarray with values to map to content_pk
        :param null_value: the value inserted when the content_pk value
                           is zero or could not be found in pk.

        :return: an np_array with length content_pk with
                 pk[i] values replaced with np_array[i]
        """
        # Add the 'null_value' in front of np_array,
        # self._indices[i] == 0 when the content_pk[i] is not in pk
        # thus returns the null_value
        if len(np_array.shape) > 1:
            to_select_from = np.insert(np_array, 0, null_value, axis=1)
        else:
            to_select_from = np.concatenate(
                (np.array([null_value]), np_array))

        # Enable multidimensional array's.
        _filter = [slice(None)] * (
            len(np_array.shape) - 1) + [self._indices]
        return to_select_from[_filter]


def create_np_lookup_index_for(search_array, index_array):
    """
    Return a np.ndarray which can be used to lookup the indices
    from index_array

    This can be used to map values of two array's like:

    search_array = np.array([7, 8, 2])
    index_array = np.array([2, 7, 8])
    lookup = create_np_lookup_index_for(search_array, index_array)
    indices_of_search_array_in_index_array = lookup[search_array]

    index_array[indices_of_search_array_in_index_array] == search_array
    (If all elements could be found)

    :param search_array: the np.ndarray with values that should be available
                         for the lookup
    :param index_array:  the np.ndarray from which the indexes should be
                         searchable by value

    :return: an np.ndarray with the values of index_array as indices, or -1
             if the value is not in index_array

    examples:

    >>> create_np_lookup_index_for(np.array([7, 8, 2]), np.array([2, 7, 8]))
    array([1, 2, 0])
    """

    sort_idx = np.argsort(index_array)
    lookup = sort_idx[np.searchsorted(
        index_array, search_array, sorter=sort_idx)]

    return lookup


def angle_in_degrees(x0, y0, x1, y1):
    """
    Calculate the angle of lines made up by the points (p1, p2):

        p1[i] = ([x0[i], y0[i]])
        p2[i] = ([x1[i], y1[i]])

    param x0: np.array with x coordinates of point p1[i]
    param y0: np.array with y coordinates of point p1[i]
    param x1: np.array with x coordinates of point p2[i]
    param y1: np.array with y coordinates of point p2[i]

    Returns: the angles of the lines with the (horizontal) x-axis
             in degrees

    Example:
    >>> angle_in_degrees(np.array([0.0]), np.array([0.0]),
    ...                  np.array([1.0]), np.array([1.0]))
    array([ 45.])
    """

    assert isinstance(x0, np.ndarray)
    assert isinstance(y0, np.ndarray)
    assert isinstance(x1, np.ndarray)
    assert isinstance(y1, np.ndarray)

    # Calculate the differences
    dx, dy = x1 - x0, y1 - y0

    # Divide by zero (dx) solution:
    #   skip (dy/dx)[i] where dx[i] == 0 and replace
    #   the (dy/dx)[i] value with np.inf when dy >= 0 and
    #   -np.inf when dy < 0

    # Create an array with the size of dy with np.inf where
    # dy >=0 and -np.inf where dy < 0
    out_inf = np.full_like(dy, np.inf)
    out_inf[dy < 0] = -np.inf

    # compute dy/dx, but use the out_inf[i] value if dx[i]==0
    dy_divided_by_dx_with_inf = np.divide(
        dy, dx, out=out_inf, where=dx != 0)

    # Return the values of the inverse-tan in degrees
    # np.inf gives 90 and -np.inf gives -90
    return np.degrees(np.arctan(dy_divided_by_dx_with_inf))


def transform_xys(x_array, y_array, source_epsg, target_epsg):
    """
    Transform x_array, y_array from source_epsg_code to
    target_epsg code
    """

    assert isinstance(x_array, np.ndarray)
    assert isinstance(y_array, np.ndarray)

    projections = []
    for epsg_code in (source_epsg, target_epsg):
        epsg_str = 'epsg:{}'.format(epsg_code)
        projection = Proj(init=epsg_str)
        projections.append(projection)

    return np.array(transform(
        projections[0], projections[1], x_array, y_array))


def get_spatial_reference(epsg_code):
    """
    :param epsg_code: Spatial Reference System Identifier (SRID)
        as implemented by the European Petroleum Survey Group (EPSG).

    :return: an osr spatial reference instance

    :raise RuntimeError: if the import from epsg_code failed

    """
    sr = osr.SpatialReference()
    try:
        sr.ImportFromEPSG(int(epsg_code))
        return sr
    except RuntimeError:
        logger.exception(
            "[-] Importing projection from epsg code %s failed." % epsg_code
        )
        raise


def pairwise(iterable):
    # from https://docs.python.org/2/library/
    # itertools.html#recipes
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def transform_bbox(bbox, source_epsg_code, target_epsg_code):
    """
    Transform bbox from source_epsg_code to target_epsg_code,
    if necessary
    """
    if source_epsg_code != target_epsg_code:
        # Transform to [[left, right],[top, bottom]]
        bbox_trans = np.array(
                transform_xys(
                    np.array([bbox[BBOX_LEFT], bbox[BBOX_RIGHT]]),
                    np.array([bbox[BBOX_TOP], bbox[BBOX_BOTTOM]]),
                    source_epsg_code, target_epsg_code))

        # Transform back to [left,top,right, bottom]
        bbox = np.array(
            [min(bbox_trans[0]),
             min(bbox_trans[1]),
             max(bbox_trans[0]),
             max(bbox_trans[1])])
    return bbox


def get_bbox_for_tile(tile_xyz=(0, 0, 0), target_epsg_code='4326'):
    """
    Get the bbox for a tile defined by x,y,z in epsg=target_epsg_code

    :param tile_xyz: tuple with tile x,y,z
    :param target_epsg_code: the epsg_code to reproject the bbox to.

    :return: The bbox of the tile
             (reprojected to target_epsg_code if necessary)
             Numpy array: [left, top, right, bottom]
             y-axis is inverted: bottom >= top

    Examples:
    >>> get_bbox_for_tile((10, 10, 15))
    array([-179.89013672,   85.04069252, -179.87915039,   85.04164217])

    >>> get_bbox_for_tile((10, 10, 15), '28992')
    array([  212572.58551456,  5468921.2451706 ,   212705.73721283,
            5469031.60724307])
    """
    bbox = np.array(
        mercantile.bounds(
            mercantile.Tile(
                x=int(tile_xyz[0]), y=int(tile_xyz[1]), z=int(tile_xyz[2])))
        )

    if MERCANTILE_EPSG_CODE != target_epsg_code:
        bbox = transform_bbox(bbox, MERCANTILE_EPSG_CODE, target_epsg_code)

    return bbox


def select_points_by_tile(tile_xyz=(0, 0, 0), target_epsg_code='4326',
                          points=None):
    """
    Select points by a tile

    :param tile_xyz: tuple with tile x,y,z
    :param target_epsg_code: the epsg_code to reproject the bbox to
            before selecting.
    :param points: (np.array) array [[x1, x2, x3...], [y1, y2, y3...]]
    :return: A boolean mask for the points within the tile_xyz bbox.

    Example:
    >>> select_points_by_tile((10, 10, 15),
    ...     '4326',
    ...     np.array([[-179.89013670, -179.89013670],
    ...               [  85.04069252,   85.04269252]]))
    array([ True, False], dtype=bool)
    """

    assert isinstance(points, np.ndarray)

    return select_points_by_bbox(
        points, get_bbox_for_tile(tile_xyz, target_epsg_code))


def select_lines_by_tile(tile_xyz=(0, 0, 0), target_epsg_code='4326',
                         lines=None, include_intersections=False):
    """
    Select lines by a tile

    :param tile_xyz: tuple with tile x,y,z
    :param target_epsg_code: the epsg_code to reproject the bbox to
            before selecting.
    :param lines: (np.array) array:
                    x1_array=lines[0], y1_array=lines[1],
                    x2_array=lines[2], y2_array=lines[3]
           line[i] = (x1[i], y1[i]) - (x2[i], y2[i])

    :return: The bbox of the tile
             (reprojected to target_epsg_code if necessary)
    """

    assert isinstance(lines, np.ndarray)

    return select_lines_by_bbox(
        lines, get_bbox_for_tile(tile_xyz, target_epsg_code),
        include_intersections)


def select_points_by_bbox(points, bbox):
    """
    Return a boolean mask array for the points that are in bbox

    :param points: np.array [[x1, x2, x3...], [y1, y2, y3...]]
    :param bbox: np.array [left, top, right, bottom], bottom >= top
    :return: a boolean mask array with 'True' for the
             points that are in the bbox

    Example:
    >>> select_points_by_bbox(
    ...     points=np.array([[1, 10, 1, 10], [10, 10, 50, 50]]),
    ...     bbox=np.array([10, 10, 50, 50]))
    array([False,  True, False,  True], dtype=bool)

    >>> select_points_by_bbox(
    ...     points=np.array([[-11, 10, 10, -10], [10, 10, -11, -10]]),
    ...     bbox=np.array([-10, -10, 10, 10]))
    array([False,  True, False,  True], dtype=bool)

    >>> select_points_by_bbox(
    ...     points=np.array([[-11, 10, 10, -10], [10, 10, 0, -10]]),
    ...     bbox=np.array([-10, 0, 10, 10]))
    array([False,  True,  True, False], dtype=bool)

    >>> select_points_by_bbox(
    ...     points=np.array([[-1, 0, 0, 10], [0, 0, -11, -10]]),
    ...     bbox=np.array([0, -10, 10, 0]))
    array([False,  True, False,  True], dtype=bool)

    >>> select_points_by_bbox(
    ...     points=np.array([[100, -100], [110, -110]]),
    ...     bbox=np.array([0, -10, 10, 0]))
    array([False, False], dtype=bool)
    """
    lleft = np.array([bbox[BBOX_LEFT], bbox[BBOX_TOP]])  # lower-left
    uright = np.array([bbox[BBOX_RIGHT], bbox[BBOX_BOTTOM]])  # upper-right
    xy_points = points.T
    pre_sel_low = xy_points >= lleft
    pre_sel_up = xy_points <= uright
    return np.all((pre_sel_low & pre_sel_up), axis=1)


def lines_to_bbox_array(lines):
    """
    Convert lines:
        x1_array=lines[0], y1_array=lines[1],
        x2_array=lines[2], y2_array=lines[3]

    to bbox_array:
        bbox[i] = [left, top, right, bottom]

    :param lines:
        x1_array=lines[0], y1_array=lines[1],
        x2_array=lines[2], y2_array=lines[3]

    :return: np.array with bboxes
    """
    # Use min/max, don't assume the x1[i] to always be left,
    # y1[i] to be top etc..
    return np.stack(
        (np.fmin(lines[0], lines[2]), np.fmin(lines[1], lines[3]),
         np.fmax(lines[0], lines[2]), np.fmax(lines[1], lines[3])), axis=1)


def select_lines_by_bbox(lines, bbox, include_intersections=False):
    """
    Return a boolean mask array for the lines that are in bbox

    :param lines: np.array
                x1_array=lines[0], y1_array=lines[1],
                x2_array=lines[2], y2_array=lines[3]

                line[i] = (x1[i], y1[i]) - (x2[i], y2[i])

    :param bbox: np.array [left, top, right, bottom]
    :return: a boolean mask array with 'True' for the
             points that are in the bbox

    """
    assert isinstance(lines, np.ndarray)

    # We can treat lines same like bboxes
    # if we transform the lines array's to bboxes
    bbox_array = lines_to_bbox_array(lines)

    if include_intersections:
        return get_bbox_intersect_bool_mask(bbox_array, bbox)

    return get_bbox_in_bool_mask(bbox_array, bbox)


def get_bbox_in_bool_mask(bbox_array, bbox):
    """
    Return a boolean mask with 'True' when bbox_array[i] is in bbox2

    :param bbox_array: np.array with bboxes [left, top, right, bottom]
    :param bbox: np.array to match with bbox_array items
                 [left, top, right, bottom]
    :return: A boolean mask with 'True' when bbox_array[i] is in
             with bbox

    Example:
    >>> get_bbox_in_bool_mask(
    ...     bbox_array=np.array(
    ...         [[5, 5, 10, 10], [15, 15, 30, 30], [50, 50, 60, 60]]),
    ...     bbox=np.array([0, 0, 20, 20]))
    array([ True, False, False], dtype=bool)
    """

    assert isinstance(bbox_array, np.ndarray)

    return ((bbox[BBOX_LEFT] <= bbox_array[:, BBOX_LEFT]) &
            (bbox[BBOX_TOP] <= bbox_array[:, BBOX_TOP]) &
            (bbox[BBOX_RIGHT] >= bbox_array[:, BBOX_RIGHT]) &
            (bbox[BBOX_BOTTOM] >= bbox_array[:, BBOX_BOTTOM])).flatten()


def get_bbox_by_point(pnt, values):
    """

    :param pnt: list or tuple of xy values
    :param values: arrays of xy's of the lower left and
        upper right corner, e.g. [[x,...], [y,...], [x1,...], [y1,...]]]
    :returns the bbox (lower left and upper right corner)
        in values which contains pnt
    Example:
    >>> get_bbox_by_point(
    ...     pnt=(1,5),
    ...     values=np.array([[0,2], [0,2], [6,6], [10,11]]))
    array([ True, False], dtype=bool)
    """
    if isinstance(pnt, (list, tuple)):
        pnt = np.array(pnt)

    assert isinstance(pnt, np.ndarray)
    # pnt --> np.array(x, y)
    lleft = np.array((values[0], values[1]))
    uright = np.array((values[2], values[3]))

    pre_sel_low = pnt >= lleft.T
    pre_sel_up = pnt <= uright.T
    return np.all((pre_sel_low & pre_sel_up), axis=1)


def get_bbox_intersect_bool_mask(bbox_array, bbox):
    """
    Return a boolean mask with 'True' when bbox_array[i] intersects with bbox2

    :param bbox_array: np.array with bboxes [left, top, right, bottom]
    :param bbox: np.array to match with bbox_array items
                 [left, top, right, bottom]
    :return: A boolean mask with 'True' when bbox_array[i] intersects
             with bbox

    Example:
    >>> get_bbox_intersect_bool_mask(
    ...     bbox_array=np.array(
    ...         [[5, 5, 10, 10], [15, 15, 30, 30], [50, 50, 60, 60]]),
    ...     bbox=np.array([0, 0, 20, 20]))
    array([ True,  True, False], dtype=bool)
    """

    assert isinstance(bbox_array, np.ndarray)

    # Check which ones do not intersect with:
    #    bbox[BBOX_LEFT] > bbox_array[:, BBOX_RIGHT] etc..
    #
    #              bbox_array[i, BBOX_RIGHT]
    #              V
    #          ----- -----
    #          |   | |   |
    #          ----- -----
    #                ^
    #                bbox[BBOX_LEFT]
    #
    # Invert the boolean array and flatten.
    return np.invert(
            (bbox[BBOX_LEFT] > bbox_array[:, BBOX_RIGHT]) |
            (bbox[BBOX_RIGHT] < bbox_array[:, BBOX_LEFT]) |
            (bbox[BBOX_TOP] > bbox_array[:, BBOX_BOTTOM]) |
            (bbox[BBOX_BOTTOM] < bbox_array[:, BBOX_TOP])).flatten()


def get_bbox_intersections(bbox_array, bbox):
    """
    Return the intersections and indices of bbox_array that intersect
    with bbox2

    :param bbox_array: np.array with bboxes [left, top, right, bottom]
    :param bbox: np.array to match with bbox_array items
                 [left, top, right, bottom]
    :return: the intersections and indices of bbox_array which intersect with
             bbox2

    Example:
    >>> get_bbox_intersections(
    ...     bbox_array=np.array(
    ...         [[5, 5, 10, 10], [15, 15, 30, 30], [50, 50, 60, 60]]),
    ...     bbox=np.array([0, 0, 20, 20]))
    (array([[ 5,  5, 10, 10],
           [15, 15, 20, 20]]), array([0, 1]))
    """

    assert isinstance(bbox_array, np.ndarray)

    intersect_mask = get_bbox_intersect_bool_mask(bbox_array, bbox)
    nodes_intersect = bbox_array[intersect_mask]

    # Calculate the intersections by getting the:
    #     max values for: left, top
    #     miniminum for: right, bottom
    #
    #     For example (left):
    #
    #          bbox_array[intersection_mask][i, BBOX_LEFT]
    #          V
    #          -----
    #          |   |
    #          -----
    #             -----
    #             |   |
    #             -----
    #             ^
    #             bbox[BBOX_LEFT]
    #
    #      intersection left value is max of both values.
    intersections = np.concatenate(
        (np.fmax(nodes_intersect[:, 0:2], bbox[0:2]),
         np.fmin(nodes_intersect[:, 2:4], bbox[2:4])), axis=1)
    return (intersections, np.argwhere(intersect_mask).flatten())


def reshape_flat_array(flat_array):
    return flat_array.reshape(2, -1)


class KCUDescriptor(dict):
    """
    dict like object that provides human readable descriptions
    for threedicore kcu codes
    """

    def __init__(self, *arg, **kw):
        super(KCUDescriptor, self).__init__(*arg, **kw)
        self.bound_keys_groundwater = [x for x in xrange(600, 1000)]
        self.bound_keys_2d = [x for x in xrange(200, 600)]

        self._descr = {
            0: '1d embedded line',
            1: '1d isolated line',
            2: '1d connected line',
            3: '1d long-crested structure',
            4: '1d short-crested structure',
            5: '1d double connected line',
            51: '1d2d single connected line with storage',
            52: '1d2d single connected line without storage',
            53: '1d2d double connected line with storage',
            54: '1d2d double connected line without storage',
            55: '1d2d connected line possible breach',
            56: '1d2d connected line active breach',
            57: '1d2d groundwater link',
            58: '1d2d groundwater link # diff to 57? ',
            100: '2d line',
            101: '2d obstacle (levee) line',
            150: '2d vertical link',
            -150: '2d groundwater link',
            200: '2d boundary',
            300: '2d boundary',
            400: '2d boundary',
            500: '2d boundary',
        }

    def get(self, item):
        return self.__getitem__(item)

    def values(self):
        v = self._descr.values()
        v.extend(['2d boundary', '2d groundwater boundary'])
        return v

    def keys(self):
        k = self._descr.keys()
        k += self.bound_keys_2d
        k += self.bound_keys_groundwater
        return k

    def __getitem__(self, item):
        if item in self.bound_keys_2d:
            return '2d boundary'
        elif item in self.bound_keys_groundwater:
            return '2d groundwater boundary'
        v = self._descr.get(item)
        if not v:
            raise KeyError(item)
        return v


def get_or_create_group(grid_file, group_name):
    """

    :param grid_file:
    :param group_name:
    :return:
    """
    gr = grid_file.get(group_name, None)
    if not gr:
        gr = grid_file.create_group(group_name)
    return gr


def get_smallest_uint_dtype(maxval):
    """Returns smallest unsigned integer datatype for holding maxval."""
    if maxval < 0:
        raise ValueError("Value cannot be negative")
    dtypes = [np.uint8, np.uint16, np.uint32, np.uint64]
    for dt in dtypes:
        if maxval <= np.iinfo(dt).max:
            return dt
    raise ValueError(
        "Value of %s exceeds all possible maximum dtype values." % maxval)

