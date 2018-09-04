# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np
import logging

logger = logging.getLogger(__name__)

BBOX_LEFT = 0
BBOX_TOP = 1
BBOX_RIGHT = 2
BBOX_BOTTOM = 3


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
