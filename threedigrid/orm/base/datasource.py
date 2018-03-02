# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function


class DataSource:
    """
    Datasource containing a 'dict' like object
    acting as the main datasource for the gridadmin
    models.
    """
    meta = None
    _source = None

    def __init__(self, source, meta=None):
        self.meta = meta
        self._source = source

    def keys(self):
        keys = self._source.keys()
        # Append meta to keys if not present
        if 'meta' not in keys:
            keys.append('meta')
        return keys

    def set(self, name, value):
        raise NotImplemented()

    def get(self, name):
        # meta is special
        if name == 'meta':
            return self.meta
        return self._source.get(name)

    def __getitem__(self, name):
        # meta is special
        if name == 'meta':
            return self.meta
        return self._source[name]
