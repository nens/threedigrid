from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import numpy as np

import pytest

from threedigrid.admin.utils import combine_vars
from threedigrid.admin.utils import PKMapper
from threedigrid.admin.utils import get_smallest_uint_dtype
from threedigrid import numpy_utils

def test_combine_vars():
    a = {'a', 'b'}
    b = {'c', 'd'}
    result = combine_vars(a, b, '_')
    assert result == ['a_c', 'a_d', 'b_c', 'b_d']


def test_combine_vars_empty_set():
    a = {'a', 'b'}
    b = {}
    result = combine_vars(a, b, '_')
    assert result == []


def test_combine_vars_invalid_combinator():
    a = {'a', 'b'}
    b = {'c'}
    with pytest.raises(TypeError):
        combine_vars(a, b, 5)

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
