import numpy as np
import pytest

from threedigrid.admin import prepare_utils
from threedigrid.admin.prepare_utils import add_or_update_datasets


@pytest.fixture(params=[[b''], [b'foo', b'bar'], [1, 2, 3], [-1.3, 0.0, 3.4],
                        [b'a_very_long_string_'*100]])
def np_array_dict(request):
    data = np.array(request.param)
    pk = range(len(data))
    numpy_array_dict = {
        'pk': np.array(pk),
        'mydataset': data
    }

    # set the DEFAULT_NULL_VALUE based on the type of params.
    if type(request.param[0]) == bytes:
        prepare_utils.DEFAULT_NULL_VALUE = b''
    else:
        prepare_utils.DEFAULT_NULL_VALUE = -9999
    return numpy_array_dict


def test_add_or_update_datasets_new_data(empty_hdf5_file, np_array_dict):
    """Add some new data to an hdf5 file"""
    h5py_group = empty_hdf5_file.create_group('mygroup')
    field_names = np_array_dict.keys()
    content_pk = pk = np_array_dict['pk']
    add_or_update_datasets(h5py_group, np_array_dict, field_names, pk,
                           content_pk)
    assert list(h5py_group.keys()) == ['mydataset']
    assert h5py_group['mydataset'].dtype == np_array_dict['mydataset'].dtype
    assert all(h5py_group['mydataset'][:] == np_array_dict['mydataset'])


def test_add_or_update_datasets_existing_data(empty_hdf5_file, np_array_dict):
    """Update existing data"""
    h5py_group = empty_hdf5_file.create_group('mygroup')
    h5py_group.create_dataset(name='mydataset',
                              data=np_array_dict['mydataset'])
    field_names = np_array_dict.keys()
    content_pk = pk = np_array_dict['pk']
    add_or_update_datasets(h5py_group, np_array_dict, field_names, pk,
                           content_pk)
    assert list(h5py_group.keys()) == ['mydataset']
    assert h5py_group['mydataset'].dtype == np_array_dict['mydataset'].dtype
    assert all(h5py_group['mydataset'][:] == np_array_dict['mydataset'])
