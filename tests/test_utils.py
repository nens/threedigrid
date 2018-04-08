from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import pytest

from threedigrid.admin.utils import combine_vars


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
