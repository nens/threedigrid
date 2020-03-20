import pytest

from threedigrid.admin.h5py_datasource import H5pyGroup


def test_init_existing_h5py_group(h5py_file):
    datasource = H5pyGroup(h5py_file, 'nodes')
    assert datasource is not None


def test_init_missing_h5py_group(h5py_file):
    with pytest.raises(AttributeError):
        H5pyGroup(h5py_file, 'doesnotexist')
