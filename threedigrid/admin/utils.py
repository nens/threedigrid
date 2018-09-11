# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import logging
from itertools import tee

import numpy as np
from six.moves import range
from six.moves import zip

logger = logging.getLogger(__name__)

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


class KCUDescriptor(dict):
    """
    A dictionary-like object that provides human readable descriptions
    for threedicore kcu codes::

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

    """

    def __init__(self, *arg, **kw):
        super(KCUDescriptor, self).__init__(*arg, **kw)
        self.bound_keys_groundwater = [x for x in range(600, 1000)]
        self.bound_keys_2d = [x for x in range(200, 600)]

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
        v = list(self._descr.values())
        v.extend(['2d boundary', '2d groundwater boundary'])
        return v

    def keys(self):
        k = list(self._descr.keys())
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


def pairwise(iterable):
    # from https://docs.python.org/2/library/
    # itertools.html#recipes
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


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


def _get_storage_area(storage_area):
    """

    :param storage_area: storage area entry in nodes collection.
        Either a numpy string or a bytes type
    :returns default '--' if the input is an empty string or 0., or the
        given input will be converted to a float representation
    """

    default_null = '--'
    # case python string type
    try:
        a = float(storage_area)
        if a > 0.:
            return a
    except ValueError:
        pass
    except TypeError:
        if storage_area is None:
            return default_null
        return _get_storage_area(np.asscalar(storage_area))

    return default_null
