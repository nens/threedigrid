# -*- coding: utf-8 -*-

"""Unit test package for threedigrid."""
import threedigrid

def test_version():
    v = threedigrid.__version__
    assert isinstance(v, basestring) and len(v) > 0
