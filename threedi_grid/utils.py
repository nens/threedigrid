import logging

from itertools import izip
from itertools import tee

import numpy as np
import osr

logger = logging.getLogger(__name__)


# def parse_record_array(record_arr, as_dict=True):
#     b = record_arr[0]
#     if not as_dict:
#         return b
#     return dict(zip(b.dtype.names, b))
#
#
# def c_to_f_array(c_array):
#     """convert c array to fortran array (transpose ordering)"""
#     f_array = np.reshape(c_array.ravel(), c_array.shape[::-1], order='F')
#     return f_array
#
#
# def f_to_c_dims(dimension):
#     """in: fortran dimension (tuple), out: c dimension"""
#     return dimension[::-1]  # just reverses tuple for now...


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


def select_by_bbox(pts, xy_lower_left, xy_upper_right):

    # points = [(random.random(), random.random()) for i in range(100)]
    #
    # bx1, bx2 = sorted([random.random(), random.random()])
    # by1, by2 = sorted([random.random(), random.random()])

    # pts = np.array(points)

    ll = np.array(xy_lower_left)  # lower-left
    ur = np.array(xy_upper_right)  # upper-right

    # ll = np.array([bx1, by1])  # lower-left
    # ur = np.array([bx2, by2])  # upper-right
    xy_pts = pts[:, [0, 1]]
    return pts[np.all((ll <= xy_pts) & (xy_pts <= ur), axis=1)]
