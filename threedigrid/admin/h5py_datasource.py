# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import logging
from threedigrid.orm.base.datasource import DataSource


logger = logging.getLogger(__name__)


class H5pyGroup(DataSource):
    """
    Datasource wrapper for h5py groups,
    adding meta data to all groups.
    """
    _group_name = None
    _h5py_file = None

    def __init__(self, h5py_file, group_name, meta=None, required=False):
        if group_name not in list(h5py_file.keys()) and not required:
            logger.info(
                '[*] {0} not found in file {1}, not required...'.format(
                    group_name, h5py_file)
            )
            return

        self.group_name = group_name

        self._h5py_file = h5py_file
        try:
            self._source = h5py_file.require_group(group_name)
        except TypeError:
            self._source = h5py_file[group_name]

        self.meta = dict(
            [(y, [x.value]) for y, x in self._h5py_file.get('meta').items()])
        self.meta['trash'] = [1]

    def set(self, name, values):
        if name in self._source:
            # Overwrite
            self._source[name][:] = values
        else:
            # Create
            self._source.create_dataset(name, data=values)

    def getattr(self, name):
        attr = self._h5py_file.attrs[name]
        if isinstance(attr, bytes):
            attr = attr.decode('utf-8')
        return attr

    def keys(self):
        return list(self._source.keys())


class H5pyResultGroup(H5pyGroup):
    def __init__(self, h5py_file, group_name, netcdf_file,
                 meta=None, required=False):
        super(H5pyResultGroup, self).__init__(
            h5py_file, group_name, meta, required)
        self.netcdf_file = netcdf_file

    def keys(self):
        keys = list(super(H5pyResultGroup, self).keys())
        keys += list(self.netcdf_file.keys())
        return list(set(keys))

    def get(self, name):
        # meta is special
        if name == 'meta':
            return self.meta

        if name in self._source:
            return self._source.get(name)

        if name in self.netcdf_file.keys():
            return self.netcdf_file.get(name)

        return None

    def attr(self, var_name, attr_name):
        v = self.get(var_name)
        if v is None:
            return ''
        try:
            return v.attrs.get(attr_name)
        except AttributeError:
            pass
        return ''

    def __getitem__(self, name):
        # meta is special
        if name == 'meta':
            return self.meta

        if name in self._source:
            return self._source[name]

        if name in self.netcdf_file.keys():
            return self.netcdf_file[name]
