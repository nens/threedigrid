# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from collections import defaultdict
from collections import namedtuple

from threedigrid.numpy_utils import create_np_lookup_index_for
from threedigrid.orm.base.fields import TimeSeriesCompositeArrayField


class Options(object):
    """
    class that adds meta data to a ResultMixin instance. The meta data includes
    entries for the ``_meta_fields`` collection (if found).

        >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
        >>> f = "/code/tests/test_files/results_3di.nc"
        >>> ff = "/code/tests/test_files/gridadmin.h5"
        >>> gr = GridH5ResultAdmin(ff, f)
        >>> gr.nodes._meta.s1
        >>> s1(units=u'm', long_name=u'waterlevel', standard_name=u'water_surface_height_above_reference_datum')

    """
    _lookup = None

    def __init__(self, inst):
        """
        :param inst: model instance
        """
        self.inst = inst

    def get_fields(self):
        """
        Returns: a list of ArrayFields names (excluding 'meta')
        """
        return {x: self.get_field(x) for x in self.inst._field_names if x != 'meta'}

    def get_field(self, field_name):
        """
        Returns: the ArrayField with field_name on this instance.
        """
        return self.inst._get_field(field_name)

    def update_field_names(self, field_names, exclude_private=True):
        """

        :param field_names: iterable of field names
        :param exclude_private: fields starting with '_' will be excluded
        """
        # remove private fields
        fnames = [x for x in field_names if
                  exclude_private and not x.startswith('_')]

        # self.inst._field_names
        # combine with existing fields
        updated_field_names = set(
            fnames).union(set(self.inst._field_names))
        self.inst._field_names = updated_field_names

    def _get_meta_values(self, field):
        meta_values = defaultdict(list)
        for m in self.inst.Meta.field_attrs:
            if self._is_type_composite(field):
                meta_values[field].append(
                    self._get_composite_meta(field, m)
                )
            else:
                meta_values[field].append(
                    self.inst._datasource.attr(field, m)
                )
        return meta_values

    def _set_field_attrs(self):
        if not hasattr(self.inst.Meta, "field_attrs"):
            return

        for _field in self.inst._field_names:
            meta_values = self._get_meta_values(_field)
            nt = namedtuple(_field, ','.join(self.inst.Meta.field_attrs))
            setattr(self, _field, nt(*meta_values[_field]))

    def _get_lookup_index(self, field_name):
        """
        creates a look up index array for the model fields which
        can be used to align result arrays to the ordering of
        grid admin arrays because it is not guaranteed  that their
        ordering is identical

        :return: numpy lookup index array
            (see ``threedigrid.numpy_utils.create_np_lookup_index_for()``
            for details) or None if the field does not have a the
            ``_needs_lookup`` attribute or if the attribute is False
        """
        if self._lookup is None:
            values = [self.inst.get_field_value(x) for x in self.inst.lookup_fields]
            self._lookup = create_np_lookup_index_for(*values)

        return self._lookup

    def _is_type_composite(self, field_name):
        """
        :param field_name: name of the field
        """
        field = self.get_field(field_name)
        return isinstance(field, TimeSeriesCompositeArrayField)

    def _get_composite_meta(self, name, meta_field, exclude={'rain'}):

        source_names = self.inst.Meta.composite_fields.get(name)
        meta_attrs = [self.inst._datasource.attr(source_name, meta_field)
                      for source_name in source_names]
        try:
            assert all(x == meta_attrs[0] for x in meta_attrs) == True, \
                'composite fields must have the same {}'.format(meta_field)
        except AssertionError:
            if name not in exclude:
                raise
            pass
        return meta_attrs[0]
