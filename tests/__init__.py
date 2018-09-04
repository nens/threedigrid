# -*- coding: utf-8 -*-

"""Unit test package for threedigrid."""
from __future__ import absolute_import
import threedigrid
import six


def test_version():
    v = threedigrid.__version__
    assert isinstance(v, six.string_types) and len(v) > 0
