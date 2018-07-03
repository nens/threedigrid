# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np
from six.moves import range


class BaseFilter(object):
    def filter(self, nparray_dict):
        raise NotImplementedError()

    def _do_filter(self, base_filter, nparray_dict):
        if hasattr(base_filter, 'shape'):
            # base_filter is boolean array result of filtering
            # over multidimensional array, for example:
            #      [[True, False, False, True],
            #       [True, False, True, False]]
            #
            # Combine the boolean arrays by 'or', for the above example
            # resulting in:
            #      [True, False, True, True]

            if len(base_filter.shape) == 2:
                # Combine filters with | (or)
                temp_filter = base_filter[0]
                for x in range(1, base_filter.shape[0]):
                    temp_filter = temp_filter | base_filter[x]

                base_filter = temp_filter

        for key in nparray_dict:
            # Apply the filter on the np_array's
            if nparray_dict[key] is not None and hasattr(
               nparray_dict[key], 'shape'):

                # Transform the base_filter by prepending slice(None) to
                # match the dimensionality of the nparray_dict[key].shape
                #
                #      shape(100,) => _filter = [base_filter]
                #      shape(2, 100)  => _filter = [slice(None), base_filter]
                #
                #      Note: x[slice(None),[1,2,3]] == x[:,[1,2,3]]

                _filter = [slice(None)] * (
                    len(nparray_dict[key].shape) - 1) + [base_filter]

                # try both with tuple and list
                # This solves h5py datasets indexing errors
                nparray_dict[key] = nparray_dict[key][:][_filter]

    def filter_dict(self, nparray_dict, model):
        """
        param: nparray_dict = dictionairy of np_array's.
        """
        # Get the filter
        base_filter = self.filter(nparray_dict)

        self._do_filter(base_filter, nparray_dict)

    def get_boolean_mask_filter(self, nparray_dict, model):
        base_filter = self.filter(nparray_dict)
        self._do_filter(base_filter, nparray_dict)

        return base_filter

    def get_field_name(self):
        raise NotImplementedError()


class BaseCompareFilter(BaseFilter):
    """
    Compare filter base
    """
    func_str = '=='

    def __init__(self, key, field, value):
        """
        :param key: E.g. 'content_pk'
        :param field: GridDataField instance
        :param value: E.g. 3, [1, 2], etc.
        """
        self._key = key
        self._field = field
        self._value = value

    def get_field_name(self):
        return self._key

    def __repr__(self):
        return "{0}({1} {2} {3})".format(
            self.__class__.__name__,
            self.func_str,
            self._key, self._value)


class EqualsFilter(BaseCompareFilter):
    func_str = '=='

    def filter(self, nparray_dict):
        return nparray_dict[self._key][:] == self._value


class NotEqualsFilter(BaseCompareFilter):
    func_str = '!='

    def filter(self, nparray_dict):
        return nparray_dict[self._key][:] != self._value


class GtFilter(BaseCompareFilter):
    func_str = '>'

    def filter(self, nparray_dict):
        return nparray_dict[self._key][:] > self._value


class GteFilter(BaseCompareFilter):
    func_str = '>='

    def filter(self, nparray_dict):
        return nparray_dict[self._key][:] >= self._value


class LtFilter(BaseCompareFilter):
    func_str = '<'

    def filter(self, nparray_dict):
        return nparray_dict[self._key][:] < self._value


class LteFilter(BaseCompareFilter):
    func_str = '<='

    def filter(self, nparray_dict):
        return nparray_dict[self._key][:] <= self._value


class InFilter(BaseCompareFilter):
    func_str = ' in '

    def __init__(self, key, field, value):
        try:
            iter(value)
        except TypeError:
            raise Exception("Values should be iterable")

        self._field = field
        self._key = key
        self._value = value

    def filter(self, nparray_dict):
        # Concatenate equals with | (or)
        return np.isin(nparray_dict[self._key][:], self._value)


class SliceFilter(BaseFilter):
    """
    Slice filter
    """
    def __init__(self, _slice):
        self._slice = _slice

    def filter(self, nparray_dict):
        return self._slice

    def get_field_name(self):
        return None

    def __repr__(self):
        return "SliceFilter({0})".format(
            self._slice)


FILTER_MAP = {
    'eq': EqualsFilter,
    'ne': NotEqualsFilter,
    'gt': GtFilter,
    'gte': GteFilter,
    'lt': LtFilter,
    'lte': LteFilter,
    'in': InFilter,
}


def get_filter(splitted_keys, field, value, filter_map=FILTER_MAP):
    """
    Helper function for getting a filter.

    :param splitted_keys: list containing field_name and an optional
        filter_name
    :param field: an instance of GridDataField for the field_name
        (splitted_keys[0])
    :param value: value or values to filter

    Returns: an instantiated filter (a subclass of BaseFilter)

    Example:

    >>> from threedigrid.orm.base.fields import ArrayField
    >>> get_filter(['content_pk', 'in'], ArrayField(), [1, 2, 3, 4])
    InFilter( in  content_pk [1, 2, 3, 4])
    """

    # Default to FILTER_MAP
    if filter_map is None:
        filter_map = FILTER_MAP

    len_splitted = len(splitted_keys)
    if len_splitted == 1:
        field_name, filter_name = splitted_keys[0], 'eq'
    elif len_splitted == 2:
        field_name, filter_name = splitted_keys
    else:
        raise ValueError("splitted keys can only contain one or two elements")

    try:
        filter_class = filter_map[filter_name]
    except KeyError:
        raise ValueError("'%s' is an unknown filter name" % filter_name)

    return filter_class(field_name, field, value)
