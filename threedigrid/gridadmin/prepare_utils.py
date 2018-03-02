# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np
from .utils import PKMapper


FIELD_NULL_VALUES = {
    'display_name':  b'',
    'code': b'',
}

DEFAULT_NULL_VALUE = -9999


def db_objects_to_numpy_array_dict(db_objects, field_names):
    numpy_array_dict = {}

    for field_name in field_names:
        numpy_array_dict[field_name] = [0] * len(db_objects)

    for index, db_object in enumerate(db_objects):
        for field_name in field_names:
            if '__' in field_name:
                # Allow to get attrs of child objects
                # by using field__attr
                splitted = field_name.split('__')
                db_object_attr = getattr(db_object, splitted[0])
                value = getattr(db_object_attr, splitted[1])
            else:
                value = getattr(db_object, field_name)

            if field_name == 'the_geom':
                value = np.fromstring(str(value.wkb), dtype='uint8')

            # Convert unicode to str
            if isinstance(value, unicode):
                value = value.encode('utf8')
            if value is not None:
                numpy_array_dict[field_name][index] = value

    for key in numpy_array_dict:
        numpy_array_dict[key] = np.array(numpy_array_dict[key])

    return numpy_array_dict


def add_or_update_datasets(h5py_group, numpy_array_dict, field_names,
                           pk, content_pk, ignore_mask=None,
                           field_name_override=None):

    # map pk onto content_pk
    pk_mapper = PKMapper(pk, content_pk, ignore_mask)
    for field_name in field_names:
        if field_name == 'pk':
            # Never store pk
            continue

        np_array = numpy_array_dict[field_name]

        null_value = FIELD_NULL_VALUES.get(
            field_name, DEFAULT_NULL_VALUE)

        data = pk_mapper.apply_on(
            np_array, null_value)

        if field_name_override:
            # By default use field_name if there is no override
            dataset_name = field_name_override.get(field_name, field_name)
        else:
            dataset_name = field_name

        if dataset_name not in h5py_group.keys():
            h5py_group.create_dataset(
                dataset_name, data=data)
        else:
            values = h5py_group[dataset_name].value
            mask = data != null_value
            values[mask] = data[mask]
            h5py_group[dataset_name][:] = values

    del data
