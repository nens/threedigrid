# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np
from . import constants
import logging

from threedigrid.admin.utils import get_or_create_group
from threedigrid.admin.constants import TYPE_CODE_MAP
import six

logger = logging.getLogger(__name__)


def get_id_map(objs_for_id_map, breach_dict):
    if not objs_for_id_map:
        return

    id_map = {}

    class_map = {TYPE_CODE_MAP[arg[0].__tablename__]: arg
                 for arg in objs_for_id_map if arg}
    for name, collection in six.iteritems(class_map):
        collection_map = {
            entry.pk: abs(entry.id) for entry in collection
        }
        id_map[name] = collection_map

    if breach_dict:
        id_map[TYPE_CODE_MAP['v2_breach']] = breach_dict
    return id_map


class IdMapper(object):

    LINE_TYPES = [
        constants.TYPE_V2_PIPE, constants.TYPE_V2_CHANNEL,
        constants.TYPE_V2_CULVERT,
        constants.TYPE_V2_ORIFICE, constants.TYPE_V2_WEIR]

    def __init__(self, id_mapping):
        self._id_mapping = id_mapping
        self.obj_slices = None
        self._define_id_obj_slices()

    @property
    def id_mapping(self):
        return self._id_mapping.value

    def get_by_name(self, obj_name):
        """
        get a slice of ``obj_slices``. That is, a structured array for
        one specific object type (like v2_channels)

        :param obj_name: name of a given object, for example v2_channel

        :return: a structured array with fields
            'obj_code', '<i4',
            ('pk', '<i4'),
            ('seq_id', '<i4')
        """
        obj_code = constants.TYPE_CODE_MAP[obj_name]
        idx = self.obj_slices[obj_code]
        return self.id_mapping[idx]

    def get_by_code(self, obj_code):
        """
        get a slice of ``obj_slices``. That is, a structured array for
        one specific object type (like v2_channels)

        :param obj_code: code for a given object, for example 2 for
            v2_channel. See TYPE_CODE_MAP in threedigrid.admin.constants
        :return: a structured array with fields
            'obj_code', '<i4',
            ('pk', '<i4'),
            ('seq_id', '<i4')

        """
        idx = self.obj_slices[obj_code]
        return self.id_mapping[idx]

    def get_pk(self, obj_name, seq_id):
        obj_code = constants.TYPE_CODE_MAP[obj_name]
        sl = self.obj_slices[obj_code]
        return self.id_mapping[sl]['pk'][np.where(
            self.id_mapping[sl]['seq_id'] == seq_id)][0]

    def _define_id_obj_slices(self):
        obj_codes = np.unique(self.id_mapping['obj_code'])
        self.obj_slices = {
            n: np.where(self.id_mapping['obj_code'] == n)
            for n in obj_codes
        }

    @staticmethod
    def prepare_mapper(h5py_file, threedi_datasource):
        id_map = get_id_map(
            threedi_datasource.objs_for_id_map,
            threedi_datasource.breach_dict)

        def _get_id_mapping_entry():
            for k, v in six.iteritems(id_map):
                for pk, seq_id in six.iteritems(v):
                    yield k, pk, seq_id

        dtype_dict = {'formats': [
                'i4', 'i4', 'i4'],
                'names': ['obj_code', 'pk', 'seq_id']
        }
        id_mapping = np.fromiter(
            _get_id_mapping_entry(),
            dtype=dtype_dict,
            count=sum(len(v) for v in six.itervalues(id_map))
        )
        try:
            gr = get_or_create_group(
                h5py_file, constants.GROUP_MAPPINGS
            )
            dset = gr.get(constants.DSET_ID_MAPPING, None)
            if not dset:
                gr.create_dataset(
                    constants.DSET_ID_MAPPING,
                    id_mapping.shape,
                    dtype=dtype_dict, data=id_mapping
                )
            logger.info(
                '[+] Successfully added {} id mapping data to grid admin file'
            )
        except Exception:
            logger.exception('Failed to add levee to hdf5')
            raise
