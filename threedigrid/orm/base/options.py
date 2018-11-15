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

from __future__ import absolute_import
from collections import defaultdict
from collections import namedtuple
from itertools import product


import logging

from threedigrid.numpy_utils import create_np_lookup_index_for
from threedigrid.orm.base.fields import TimeSeriesCompositeArrayField
from threedigrid.orm.base.utils import _flatten_dict_values
import six

logger = logging.getLogger(__name__)


class Options(object):
    """
    class that adds meta data to a model instance. Accessible
    through the _meta API. To retrieve meta data of a field, say ``s1``:

        >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
        >>> f = "/code/tests/test_files/results_3di.nc"
        >>> ff = "/code/tests/test_files/gridadmin.h5"
        >>> gr = GridH5ResultAdmin(ff, f)
        >>> gr.nodes._meta.s1
        >>> s1(units=u'm', long_name=u'waterlevel',
        ...     standard_name=u'water_surface_height_above_reference_datum')

    ``s1`` is a namedtuple so you can retrieve the units attribute by the ``.``
    notation ``gr.nodes._meta.s1.units`` or using the ``_as_dict`` method
    ``gr.nodes._meta.s1._asdict()['units']``

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

        :returns: a dict of the models {field name: Field instance}. If
            the only_names flag is given a list of the models field
            names is returned
        """
        fields = {
            x: self.get_field(x)
            for x in self.inst._field_names if x != 'meta'
        }
        if only_names:
            return list(fields.keys())
        return fields

    def get_field(self, field_name):
        """
        :returns: the ArrayField with field_name on this instance.

        """
        return self.inst._get_field(field_name)

    def add_field(self, field_name, field, hide_private=True):
        """
        add field names to the model instance

        :param field_names: iterable of field names
        :param hide_private: fields starting with '_' will be added to the
            instance but excluded from the list of field names
        """
        if not self._source_exists(field_name):
            return
        setattr(self.inst, field_name, field)
        # remove private fields
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

        for field_name, field in six.iteritems(fields):
            self.add_field(field_name, field, hide_private)

    def _source_exists(self, field_name):
        """
        Checks whether field_name exists in the data source.
        Also can check composite fields

        :param field_name: name of the source field name
        :return: True if it exists False otherwise
        """
        _has_comp = hasattr(self.inst.Meta, 'composite_fields')
        _has_sub = hasattr(self.inst.Meta, 'subset_fields')
        if not _has_comp and not _has_sub:
            return field_name in list(self.inst._datasource.keys())

        sources = self.inst.Meta.composite_fields.get(field_name)
        if sources:
            return any(x in list(self.inst._datasource.keys())
                       for x in sources)
        sources = self.inst.Meta.subset_fields.get(field_name)
        if sources:
            _sources = _flatten_dict_values(sources, as_set=True)
            return any(x in set(self.inst._datasource.keys())
                       for x in _sources)

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
            if self._is_type_composite_field(field_name):
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

        # add the meta information to the instance. Uses the field name as
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

    def _get_composite_meta(self, field_name, attr_name):
        """
        get the attr entry for a composite field from the datasource

        :param field_name: field name of the model
        :param attr_name: name of the attribute from the
            ``Meta.field_attrs`` list
        :return: the attr entry from the datasource or an empty string if the
            entries in datasource are not identical for the composite fields.
            If s1 for example points to 'Mesh2D_s1' and 'Mesh1D_s1' both
            datasets must have the value 'm' for the 'units' attribute
        """
        source_names = self.inst.Meta.composite_fields.get(field_name)
        meta_attrs = [self.inst._datasource.attr(source_name, attr_name)
                      for source_name in source_names]

        if len(meta_attrs) < 2:
            return ''

        try:
            assert all(x == meta_attrs[0] for x in meta_attrs), \
                'composite fields must have the same {}. ' \
                'Failed to get meta info for field_name {} '.format(
                    attr_name, field_name)
        except AssertionError:
            return ''
        return meta_attrs[0]

    def _is_type_composite_field(self, field_name):
        """
        checks if the field is a composite field,
        like TimeSeriesCompositeArrayField
        :param field_name: name of the field
        """
        field = self.get_field(field_name)
        return isinstance(field, TimeSeriesCompositeArrayField)


class ModelMeta(type):
    """
    Metaclass for defining model meta classes.

    If you have a complexer setup you can make use of the ``ModelMeta``
    meta class that provides some field constructors behind the scenes.
    Aggregation files potentially contain a lot of different aggregation
    variables resulting in a lot of different source fields. You don't
    manually have to define all those combinations simply define a
    ``base_composition`` and a ``composition_vars`` dictionary. This computes
    all necessary composite_fields automatically.

    """

    def __new__(mcs, name, bases, namespace, **kwds):
        new_mixin = type.__new__(mcs, name, bases, dict(namespace))
        # composite_fields has been set directly, do not try to compose
        composite_fields = namespace.get('composite_fields')
        if composite_fields:
            return new_mixin

        # get base composition and vars to combine with
        base_composition = namespace.get('base_composition')
        composition_vars = namespace.get('composition_vars')
        lookup_fields = namespace.get('lookup_fields')
        base_subset_fields = namespace.get('base_subset_fields')

        # simple results
        if not composition_vars and base_composition:
            new_mixin.composite_fields = base_composition
            return new_mixin

        if composition_vars and not base_composition:
            raise AttributeError(
                'Missing base_composition attribute for the composition_vars'
            )
        # produce all possible combinations and add composite_fields
        # attribute to the class
        new_mixin.composite_fields = {}

        for k, v in six.iteritems(composition_vars):
            c_field = base_composition.get(k)
            if not c_field:
                continue
            for p in v:
                new_key = k + '_' + p
                agg_fields = ModelMeta.combine_vars(c_field, {p})
                new_mixin.composite_fields[new_key] = agg_fields

        if base_subset_fields:
            new_mixin.subset_fields = {}
            for k, v in six.iteritems(composition_vars):
                subset_dict = base_subset_fields.get(k)
                if not subset_dict:
                    continue
                s_field = list(subset_dict.values())[0]
                s_name = list(subset_dict.keys())[0]
                for p in v:
                    new_key = k + '_' + p
                    agg_fields = ModelMeta.combine_vars({s_field}, {p})
                    new_mixin.subset_fields[new_key] = {s_name: agg_fields}

        if not lookup_fields:
            return new_mixin
        lookup_field = lookup_fields[1]
        v = base_composition.get(lookup_field)
        if v:
            new_mixin.composite_fields[lookup_field] = v
        return new_mixin

    @staticmethod
    def combine_vars(prod_a, prod_b, join_str='_'):
        """Return the cartesian product of prod_a with prod_b, combined together with
        join_str.

        >>> combine_vars({'a', 'b'}, {'c', 'd'})
        ['a_c', 'a_d', 'b_c', 'b_d']

        :param prod_a: (iterable)
        :param prod_b: (iterable)
        :param join_str: (string)
        :return: (list) ∏ (set_a, set_b)
        """
        return [x[0] + join_str + x[1] for x in product(prod_a, prod_b)]
