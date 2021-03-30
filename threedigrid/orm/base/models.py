# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import

import logging
from abc import ABCMeta
from collections import OrderedDict
from itertools import chain
from itertools import tee

import numpy as np
import six
from six.moves import zip

from threedigrid.orm.base.exceptions import OperationNotSupportedError
from threedigrid.orm.base.fields import ArrayField
from threedigrid.orm.base.fields import IndexArrayField
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.orm.base.filters import SliceFilter
from threedigrid.orm.base.filters import get_filter
from threedigrid.orm.base.options import Options

logger = logging.getLogger(__name__)


def extend_instance(obj, cls):
    """Apply mixins to a class instance after creation"""
    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type(base_cls_name, (base_cls, cls), {})


def pairwise(iterable):
    # from https://docs.python.org/2/library/
    # itertools.html#recipes
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


class Model(six.with_metaclass(ABCMeta)):
    id = IndexArrayField()

    _field_names = []

    _exporters = []

    _filter_map = None

    _datasource = None

    def __init__(self, datasource=None, slice_filters=[],
                 epsg_code=None, only_fields=[], reproject_to_epsg=None,
                 has_1d=None, mixin=None, timeseries_chunk_size=None,
                 **kwargs):
        """
        Initialize a Model with a datasource, filters
        and a epsg_code.

        The datasource is a wrapped h5py Group from a H5py file or
        an instance that implements the same interface.
        """

        self._datasource = datasource
        self.slice_filters = slice_filters
        self.only_fields = only_fields
        self.reproject_to_epsg = reproject_to_epsg

        self.class_kwargs = {
            'slice_filters': slice_filters,
            'only_fields': only_fields,
            'reproject_to_epsg': reproject_to_epsg,
            'has_1d': has_1d,
            'mixin': mixin,
            'timeseries_chunk_size': timeseries_chunk_size
        }

        # Extend the class with the mixin, if set
        if mixin:
            extend_instance(self, mixin)
            # pass kwargs to mixin
            super(Model, self).__init__(**kwargs)

        # Cache the boolean filter mask for this instance
        # after it has been computed once
        self._boolean_mask_filter = None
        self._mixin = mixin
        self._epsg_code = epsg_code

        # Cache the field names
        _field_names = [
            x for x in dir(self.__class__)
            if isinstance(
                getattr(self.__class__, x),
                (ArrayField, TimeSeriesArrayField)
            )
        ]
        self._field_names = set(self._field_names).union(set(_field_names))

        self.has_1d = has_1d

    @property
    def epsg_code(self):
        if not self._epsg_code:
            self._epsg_code = self._datasource.getattr('epsg_code')
        return self._epsg_code

    @property
    def count(self):
        """count of all elements (including trash element)"""
        if self.class_kwargs.get('slice_filters'):
            return self.get_filtered_field_value('id').size
        return self.get_field_value('id').size

    @property
    def model_name(self):
        try:
            model_name = '-'.join(
                (self._datasource.getattr('model_name'),
                 self._datasource.getattr('model_slug'),
                 str(self._datasource.getattr('revision_nr')),
                 self._datasource.getattr('revision_hash')))
        except (AttributeError, KeyError, TypeError):
            model_name = 'unknown'
            pass
        return model_name

    def _get_field(self, field_name):
        """
        Returns: the ArrayField with field_name on this instance.
        """
        return super(Model, self).__getattribute__(field_name)

    def get_field_value(self, field_name, **kwargs):
        """
        Returns: the value for the ArrayField with name field_name
        on the instance.

        With this in place we can later override the ArrayField
        get_value method for field specific conversion, if needed.
        """
        update_dict = {
            'model_name': self.__class__.__name__,
        }

        kwargs.update(update_dict)
        return self._meta.get_field(field_name).get_value(
            self._datasource, field_name, **kwargs)

    def _get_subset_idx(self, field_name):
        """
        get an array of indexes for the given subset

        :param field_name: field name
        """
        new_inst = self.__init_class(
            self.__class__, **{'mixin': self.class_kwargs.get('mixin')})
        subset_dict = new_inst.Meta.subset_fields.get(field_name)
        if not subset_dict:
            return
        _subset_name = list(subset_dict.keys())
        if not _subset_name:
            return
        return new_inst.subset(_subset_name[0]).id

    def get_filtered_field_value(
            self, field_name, ts_filter=None, lookup_index=None,
            subset_index=None):
        # Redirect via datasource
        return self._datasource.get_filtered_field_value(
            self, field_name, ts_filter, lookup_index, subset_index)

    def __getattribute__(self, attr_name):
        """
        Override the __getattribute__ methode to return
        the computed values of ArrayField's instead of
        the ArrayField
        instance.
        """
        # Note: don't use getattr(self, XX) in this function,
        # it will lead to a max recursion error
        attr = super(Model, self).__getattribute__(attr_name)
        # Override getting ArrayField attributes
        if isinstance(attr, ArrayField):

            # Return meta directly, we don't want it to
            # to be filtered
            if attr_name == 'meta':
                return attr.get_value(self._datasource, attr_name)

            # Use the get function to retrieve the computed/filtered
            # value for the ArrayField with name: 'name'
            return super(Model, self).__getattribute__(
                'get_filtered_field_value')(attr_name)

        # Default behaviour, return the attribute from superclass
        return attr

    def __init_class(self, klass, **kwargs):
        """
        Returns: a new instance of 'klass' with new filters and
                 same datasource.
        """

        return klass(
            datasource=self._datasource,
            **kwargs)

    def __get_filters(self, **kwargs):
        """
        Parse kwargs for filters.

        For example:
            content_type__in=[1,2,3]

            splitted_key[0] = "content_type"
            splitted_key[1] = "in"
            -> Try to find filter with "in" as key

        """
        new_slice_filters = list(self.slice_filters)  # make copy
        filter_as = kwargs.pop('filter___as', False)

        for key, value in six.iteritems(kwargs):
            # python2/3 combat
            if isinstance(value, str):
                value = str.encode(value)
            splitted_key = key.split('__')
            if splitted_key[0] not in self._field_names:
                raise ValueError(
                    "Field '{}' unknown. Choices are {}".format(
                        splitted_key[0],
                        self._field_names)
                )

            new_slice_filters.append(
                get_filter(
                    splitted_key,
                    self._meta.get_field(splitted_key[0]),
                    value,
                    filter_map=self._filter_map,
                    filter_as=filter_as)
            )

        return new_slice_filters

    def _filter_as(self, klass, **kwargs):
        """
        Same as self.filter, but now return "klass" instance instead of
        self.__class__ instance
        """
        # Inject filter___as, set this on the filters
        # so they can identified as filters that
        # produce submodels
        kwargs['filter___as'] = True
        slice_filters = self.__get_filters(**kwargs)
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update(
            {'slice_filters': slice_filters})

        return self.__init_class(klass, **new_class_kwargs)

    # def _set_subsets(self):
    #     if not hasattr(self, 'Meta'):
    #         return
    #     if not hasattr(self.Meta, 'subset_fields'):
    #         return
    #
    #     _subsets = set(self.Meta.subset_fields.keys())
    #     for sset in _subsets:
    #         idx = self._get_subset_idx(sset)
    #         setattr(self, sset, idx)

    def filter(self, **kwargs):
        """
        Django style filtering, allows multiple filter or chaining filters
        for example:

            line_instance.filter(content_type='v2_weir', content_pk=1)
            line_instance.filter(content_type='v2_weir').filter(content_pk=1)

            Both produce the same result object.


        Returns: a new instance of the object with the extra filters added.
        """
        slice_filters = self.__get_filters(**kwargs)
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update(
            {'slice_filters': slice_filters})

        return self.__init_class(
            self.__class__, **new_class_kwargs)

    def slice(self, start, stop=None, step=None, override_filter_error=False):
        """
        slice by name or slice. See instance.predefined_slices for an overview
        of predefined slices

        :param s: either the name of the slice (see instance.predefined_slices
             for an overview or an slice instance, e.g. slice(<x>, <y>)
        :return: nodes instance with containing the sliced dataset.Example
            usage::
            usage:
            open_water_2d = nodes.slice('2D_open_water')
            open_water_2d.data

                OrderedDict([('content_pk', array([1, 2, 3, ...

        """
        if self.slice_filters and not override_filter_error:
            raise OperationNotSupportedError(
                'You cannot use slices on a filtered dataset')

        if isinstance(start, slice):
            slice_filter = start
        else:
            slice_filter = slice(start, stop, step)

        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update(
            {'slice_filters':
             [SliceFilter(slice_filter)] + self.slice_filters})

        return self.__init_class(
            self.__class__, **new_class_kwargs)

    @property
    def known_subset(self):
        if not hasattr(self, 'SUBSETS'):
            return "has no subsets defined"
        return list(
            chain(*[list(v.keys()) for v in six.itervalues(self.SUBSETS)])
        )

    def subset(self, name):
        """
        get a subset of the data. See instance.subsets for an overview
        of predefined subsets

        :param name: name of the subset (see instance.predefined_slices
             for an overview or an slice instance, e.g. slice(<x>, <y>)
        :return: nodes instance with containing the sliced dataset.Example
            usage::
            open_water_2d = nodes.slice('2D_open_water')
            open_water_2d.data

                OrderedDict([('content_pk', array([1, 2, 3, ...

        """
        if not hasattr(self, 'SUBSETS'):
            raise TypeError("SUBSETS not defined for this type of model")

        if isinstance(name, six.string_types):
            field_filter = [key for key in self.SUBSETS if
                            name.upper() in self.SUBSETS[key]]

            if not field_filter:
                msg = 'Invalid subset name.'
                msg += ' Valid options are: %s ' % (
                    [x for y in self.SUBSETS.values() for x in y], )
                logger.exception(msg)
                raise KeyError(msg)

            if len(field_filter) > 1:
                raise KeyError(
                    'Multiple options found for subset: %s ' % name.upper())

            field_filter = field_filter[0]
        else:
            raise TypeError('Type %s not supported' % type(name,))

        return self.filter(
            **{field_filter: self.SUBSETS[field_filter][name.upper()]})

    def only(self, *args):
        """
        Return only the fields requested

        Usage: line_instance.only('content_pk', 'line')
        """
        if not args:
            raise Exception("Please provide at least one field name")

        for x in args:
            if x not in self._field_names:
                raise Exception("Unknown field name: {0}".format(x))

        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update(
            {'only_fields': self.only_fields + list(args)})

        return self.__init_class(
            self.__class__, **new_class_kwargs)

    def _get_values(self, selection):
        """
        when no filters are specified, we are still operating on the hdf5
        groups so get the values explicitly

        :param selection: ordered dict of selected fields
            with group datasets
        :return: new ordered dict with values from group datasets
        """

        _tmp = OrderedDict()
        for k, v in six.iteritems(selection):
            try:
                _tmp[k] = v[:]
            except TypeError:
                pass
        return _tmp

    def to_dict(self):
        """
        Returns: the filtered values as dictionairy
        """
        return self._datasource.execute_query(self)

    def to_structured_array(self):
        """
        :return: the filtered values as a
        structured (named) array
        """
        selection = self.to_dict()

        # Convert the dictionary to structured array
        dtypes = []
        for key, value in selection.items():
            dtypes.append((key, value.dtype.name, value.shape))

        return np.array(
            [tuple([selection[x[0]] for x in dtypes])],
            dtype=dtypes)[0]

    def to_list(self):
        """
        :return: list of dicts with key's and values
        """

        # Filter results and transform the result to
        # and np.ndarray
        selection = self.to_dict()
        if len(list(selection.values())) > 1:
            array = np.array(list(selection.values()))
        else:
            array = list(selection.values())[0]

        def optional_zip(array_to_zip):
            """
            Optional zip the results of
            array_to_zip if there are more than one
            dimensions.
            """
            # Transform data to list
            array_as_list = array_to_zip.tolist()
            if len(array_to_zip.shape) > 1:
                # Zip the list if there are more than
                # one dimensions.
                array_as_list = zip(*array_as_list)
            return array_as_list

        # Zip the lists of array_lists (does same as a transpose)
        data = zip(*[optional_zip(x) for x in array])

        # Create a list of dictionairies of the data by
        # zipping the selection.keys() (= field_names) for all items
        # in data
        return [dict(zip(list(selection.keys()), x)) for x in data]

    @property
    def boolean_mask_filter(self):
        selection = OrderedDict()

        # Compute the boolean mask filter
        # that can be applied to all array's
        # based on the specified filters

        if self._boolean_mask_filter is None:

            # If no filters are defined
            if not self.slice_filters:
                # Select everything
                return slice(None)

            # Only load the fields that need to be filtered
            filter_field_names = [
                x.get_field_name() for x in self.slice_filters]

            for name in [x for x in filter_field_names if x]:
                selection[name] = self.get_field_value(
                    name)

            boolean_mask_filter = None
            # Compute the the filter
            for filter_instance in self.slice_filters:
                filter_bool_mask = filter_instance.get_boolean_mask_filter(
                        selection, self)

                if boolean_mask_filter is None:
                    boolean_mask_filter = filter_bool_mask
                else:
                    # apply the filter_bool_mask on the boolean_mask_filter
                    # where the boolean_mask_filter is still "True".
                    boolean_mask_filter[
                        boolean_mask_filter == True] &= filter_bool_mask # noqa

            self._boolean_mask_filter = boolean_mask_filter

        return self._boolean_mask_filter

    def to_array(self):
        """
        Returns: the filtered values as a numpy array
        """
        selection = self.to_dict()
        if len(list(selection.values())) > 1:
            return np.array(list(selection.values()))
        return list(selection.values())[0]

    @property
    def data(self):
        """
        Returns: the (filtered) data a dictionairy
        """
        return self.to_dict()

    @property
    def _meta(self):
        """
        meta class that add meta data to a ResultMixin instance. The meta data
        includes entries for the ``_meta_fields`` collection (if found).

            >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
            >>> f = "/code/tests/test_files/results_3di.nc"
            >>> ff = "/code/tests/test_files/gridadmin.h5"
            >>> gr = GridH5ResultAdmin(ff, f)
            >>> gr.nodes._meta.s1
            >>> s1(units=u'm', long_name=u'waterlevel', standard_name=u'water_surface_height_above_reference_datum') # noqa
        """
        return Options(self)

    def __repr__(self):
        """human readable representation of the instance"""
        return "<orm {} instance of {}>".format(
            self.__contenttype__(), self.model_name
        )

    def __contenttype__(self):
        """conent type, e.g. lines, nodes, cells, ..."""
        return self._datasource.group_name
