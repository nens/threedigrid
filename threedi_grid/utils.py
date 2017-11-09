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
