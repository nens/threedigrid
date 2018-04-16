# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Options
+++++++

The model _meta API is inspired by the Django _meta API. It is accessible
through the _meta attribute of a model instance, which in turn is an instance
of an threedigrid.orm.base.options.Options object.

Public methods primarily act on fields:

  - get all field instances of a model
  - get a single field instance of a model by name
  - add a single field instance to a model
  - add a field instances to a model

"""
from __future__ import unicode_literals
from __future__ import print_function

from collections import defaultdict
from collections import namedtuple

from threedigrid.numpy_utils import create_np_lookup_index_for
from threedigrid.orm.base.fields import TimeSeriesCompositeArrayField


class Options(object):
    """
    class that adds meta data to a model instance. Accessible
    through the _meta API. To retrieve meta data of a field, say ``s1``:

        >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
        >>> f = "/code/tests/test_files/results_3di.nc"
        >>> ff = "/code/tests/test_files/gridadmin.h5"
        >>> gr = GridH5ResultAdmin(ff, f)
        >>> gr.nodes._meta.s1
        >>> s1(units=u'm', long_name=u'waterlevel', standard_name=u'water_surface_height_above_reference_datum')

    """
    _lookup = None  # placeholder for lookup index array

    def __init__(self, inst):
        """
        :param inst: model instance
        """
        self.inst = inst
        self._set_field_attrs()

    def get_fields(self, only_names=False):
        """
        :param only_names: omit the field instances and return a list of
        field names instead

        Returns: a dict of the models {field name: Field instance}. If the
            only_names flag is given a list of the models field names
            is returned
        """
        fields = {
            x: self.get_field(x)
            for x in self.inst._field_names if x != 'meta'
        }
        if only_names:
            return fields.keys()
        return fields

    def get_field(self, field_name):
        """
        Returns: the ArrayField with field_name on this instance.
        """
        return self.inst._get_field(field_name)

    def add_field(self, field_name, field, hide_private=True):
        """
        add field names to the model instance

        :param field_names: iterable of field names
        :param hide_private: fields starting with '_' will be added to the
            instance but excluded from the list of field names
        """
        # remove private fields
        setattr(self.inst, field_name, field)
        if hide_private and field_name.startswith('_'):
            return
        _union = set(self.inst._field_names).union({field_name})
        self.inst._field_names = _union

    def add_fields(self, fields, hide_private=True):
        """
        add fields to the models instance

        :param fields: dict of field names and fields
        :param hide_private: fields starting with '_' will be added to the
            instance but excluded from the list of field names
        """

        for field_name, field in fields.iteritems():
            self.add_field(field_name, field, hide_private)
        #     setattr(self, field_name, field)
        # self._meta.update_field_names(variables, exclude_private=True)
        # # combine with existing fields
        #
        # fnames = [x for x in field_names if
        #           exclude_private and not x.startswith('_')]
        # updated_field_names = set(
        #     fnames).union(set(self.inst._field_names))
        # self.inst._field_names = updated_field_names

    def _get_meta_values(self, field_name):
        """
        fetches the values for the ``field_attrs`` entries
        of the models ``Meta`` instance
        :param field_name: name of the field
        :return: dict with field names as keys and a list with the
            corresponding meta values::

            {'s1':
                ['m', 'waterlevel',
                'water_surface_height_above_reference_datum']
            }
        """

        meta_values = defaultdict(list)
        for attr_name in self.inst.Meta.field_attrs:
            if self._is_type_composite(field_name):
                meta_values[field_name].append(
                    self._get_composite_meta(field_name, attr_name)
                )
            else:
                meta_values[field_name].append(
                    self.inst._datasource.attr(field_name, attr_name)
                )
        return meta_values

    def _set_field_attrs(self):
        # not all models must have a Meta instance
        if not hasattr(self.inst, 'Meta'):
            return

        # not all models with a Meta class must have a field_attrs attribute
        if not hasattr(self.inst.Meta, "field_attrs"):
            return

        # add the meta information the instance. Uses the field name as
        # name. ``s1`` will be accessible like so for
        # example: ``gr.nodes._meta.s1``
        for _field in self.inst._field_names:
            meta_values = self._get_meta_values(_field)
            nt = namedtuple(_field, ','.join(self.inst.Meta.field_attrs))
            setattr(self, _field, nt(*meta_values[_field]))

    def _get_lookup_index(self):
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
            values = [self.inst.get_field_value(x)
                      for x in self.inst.Meta.lookup_fields]
            self._lookup = create_np_lookup_index_for(*values)

        return self._lookup

    def _is_type_composite(self, field_name):
        """
        checks if the field is a composite field,
        like TimeSeriesCompositeArrayField

        :param field_name: name of the field
        """
        field = self.get_field(field_name)
        return isinstance(field, TimeSeriesCompositeArrayField)

    def _get_composite_meta(self, field_name, attr_name,
                            exclude_fields={'rain'}):
        """
        get the attr entry for a composite field from the datasource

        :param field_name: field name of the model
        :param attr_name: name of the attribute from the
            ``Meta.field_attrs`` list
        :param exclude_fields: set of fields to exclude
        :return: the attr entry from the datasource
        :raises: AssertionError if the entries in datasource are not
            identical for the composite fields. If s1 for example points to
            'Mesh2D_s1' and 'Mesh1D_s1' both datasets must have the value 'm'
            for the 'units' attribute
        """

        source_names = self.inst.Meta.composite_fields.get(field_name)
        meta_attrs = [self.inst._datasource.attr(source_name, attr_name)
                      for source_name in source_names]
        try:
            assert all(x == meta_attrs[0] for x in meta_attrs) == True, \
                'composite fields must have the same {}'.format(attr_name)
        except AssertionError:
            if field_name not in exclude_fields:
                raise
            pass
        return meta_attrs[0]
