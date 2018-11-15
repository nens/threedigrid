from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import sys

import numpy as np

import pytest

from threedigrid.admin.utils import PKMapper
from threedigrid.admin.utils import _get_storage_area
from threedigrid.numpy_utils import get_smallest_uint_dtype
from threedigrid import numpy_utils
from threedigrid.orm.base.utils import _flatten_dict_values


def test_create_np_lookup_index_for():
    a = np.arange(6)
    b = np.array([3, 4, 1, 2, 5, 0])
    lidx = numpy_utils.create_np_lookup_index_for(a, b)
    np.testing.assert_array_equal(lidx, np.array([5, 2, 3, 0, 1, 4]))


def test_pk_mapper():
    pk = np.array([1, 2, 3, 4, 5, 6])
    to_map = np.array([1.1, 2.1, 3.1, 4.1, 5.1, 6.1])
    content_pk = np.array([0, 0, 15, 3, 4, 0, 0, 1, 1, 15])
    expected = [0, 0, 0, 3.1, 4.1, 0, 0, 1.1, 1.1, 0]
    result = PKMapper(pk, content_pk).apply_on(to_map, 0)
    np.testing.assert_equal(result, expected)


def test_get_smallest_uint_dtype():
    r = get_smallest_uint_dtype(4)
    assert r == np.uint8
    rr = get_smallest_uint_dtype(400)
    assert rr == np.uint16
    rrr = get_smallest_uint_dtype(400000)
    assert rrr == np.uint32
    rrrr = get_smallest_uint_dtype(40000000000)
    assert rrrr == np.uint64


def test_get_smallest_uint_dtype_raises_value_error_neg_input():
    with pytest.raises(ValueError):
        get_smallest_uint_dtype(-1)


def test_get_smallest_uint_dtype_raises_value_error_exceeding_input():
    with pytest.raises(ValueError):
        get_smallest_uint_dtype(400000000000000000000000)


@pytest.mark.skipif(
    sys.version_info < (3, 0), reason="requires Python3")
def test_get_storage_area_bytes_to_float():
    a = np.array(['2.2'], np.bytes_)
    sa_a = _get_storage_area(a)
    assert sa_a == 2.2


@pytest.mark.skipif(
    sys.version_info < (3, 0), reason="requires Python3")
def test_get_storage_area_bytes_to_string():
    b = np.array([''], np.bytes_)
    sa_b = _get_storage_area(b)
    assert sa_b == '--'  # default response
    b = np.array(['0'], np.bytes_)
    sa_b = _get_storage_area(b)
    assert sa_b == '--'  # default response


@pytest.mark.skipif(
    sys.version_info > (3, 0), reason="requires Python2")
def test_get_storage_area_string_input():
    b = np.array([''], np.string_)
    sa_b = _get_storage_area(b)
    assert sa_b == '--'  # default response
    b = np.array(['0'], np.string_)
    sa_b = _get_storage_area(b)
    assert sa_b == '--'  # default response


@pytest.mark.skipif(
    sys.version_info > (3, 0), reason="requires Python2")
def test_get_storage_area_string_to_float():
    b = np.array(['0.5'], np.string_)
    sa_b = _get_storage_area(b)
    assert sa_b == 0.5


def test_get_storage_area_none_input():
    sa_c = _get_storage_area(None)
    assert sa_c == '--'


def test_flatten_dict_values_as_set():
    d = {'a': 1}
    v = _flatten_dict_values(d, as_set=True)
    assert v == {1}


def test_flatten_nested_dict_values_as_set():
    d = {'a': [1]}
    v = _flatten_dict_values(d, as_set=True)
    assert v == {1}


def test_flatten_dict_values_as_list():
    d = {'a': 1}
    v = _flatten_dict_values(d, as_set=False)
    assert v == [1]


def test_flatten_nested_dict_values_as_list():
    d = {'a': [1]}
    v = _flatten_dict_values(d, as_set=False)
    assert v == [1]
