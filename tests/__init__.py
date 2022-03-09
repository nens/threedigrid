"""Unit test package for threedigrid."""
import threedigrid


def test_version():
    v = threedigrid.__version__
    assert isinstance(v, str) and len(v) > 0
