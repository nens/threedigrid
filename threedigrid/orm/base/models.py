# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np
import logging
from itertools import izip
from itertools import tee
from itertools import chain

from h5py._hl.dataset import Dataset

from abc import ABCMeta
from abc import abstractmethod

from collections import OrderedDict

from threedigrid.orm.base.exceptions import OperationNotSupportedError
from threedigrid.orm.base.fields import ArrayField
from threedigrid.orm.base.fields import IndexArrayField
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.orm.base.fields import TimeSeriesCompositeArrayField
from threedigrid.orm import constants

from threedigrid.orm.base.filters import get_filter
from threedigrid.orm.base.filters import SliceFilter
from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.numpy_utils import create_np_lookup_index_for

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
    return izip(a, b)


class Model:
    __metaclass__ = ABCMeta
    id = IndexArrayField()

    _field_names = []

    _exporters = []

    _filter_map = None

    _datasource = None

    def __init__(self, datasource=None, slice_filters=[],
                 epsg_code=None, only_fields=[], reproject_to_epsg=None,
                 has_1d=None, mixin=None, timeseries_chunk_size=None, **kwargs):
        """
        Initialize a Model with a datasource, filters
        and a epsg_code.

        The datasource is a wrapped h5py Group from a H5py file or
        an instance that implements the same interface.
        """

        self._datasource = datasource
        self._lookup = None
        self.slice_filters = slice_filters
        self.only_fields = only_fields
        self.reproject_to_epsg = reproject_to_epsg
        self._kwargs = kwargs

        self.class_kwargs = {
            'slice_filters': slice_filters,
            'only_fields': only_fields,
            'reproject_to_epsg': reproject_to_epsg,
            'mixin': mixin,
            'timeseries_chunk_size': timeseries_chunk_size
        }

        # Extend the class with the mixin, if set
        if mixin:
            extend_instance(self, mixin)
            # pass kwargs to mixin
            if isinstance(mixin, ResultMixin.__class__):
                netcdf_keys = self._datasource.netcdf_file.variables.keys()
                super(Model, self).__init__(netcdf_keys, **kwargs)
            else:
                super(Model, self).__init__(**kwargs)

        # Cache the boolean filter mask for this instance
        # after it has been computed once
        self._boolean_mask_filter = None
        self._mixin = mixin

        if not epsg_code:
            epsg_code = self._datasource.getattr('epsg_code')
        self.epsg_code = epsg_code

        # Cache the field names

        _field_names = [
            x for x in dir(self.__class__)
            if isinstance(getattr(self.__class__, x), (ArrayField, TimeSeriesArrayField))]
        self._field_names = set(self._field_names).union(set(_field_names))

        self.has_1d = has_1d
        self.model_name = '-'.join(
            (self._datasource.getattr('model_name'),
             self._datasource.getattr('model_slug'),
             str(self._datasource.getattr('revision_nr')),
             self._datasource.getattr('revision_hash')))

    def get_field(self, field_name):
        """
        Returns: the ArrayField with field_name on this instance.
        """
        return super(Model, self).__getattribute__(field_name)

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
        f = self.get_field(field_name)
        if not hasattr(f, '_needs_lookup') or not getattr(f, '_needs_lookup'):
            return self._lookup

        if self._lookup is None:
            _id = self.get_field_value('id')
            _mesh_id = self.get_field_value(
                '_mesh_id',
            )
            self._lookup = create_np_lookup_index_for(_id[:], _mesh_id)

        return self._lookup

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
        return self.get_field(field_name).get_value(
            self._datasource, field_name, **kwargs)

    def get_filtered_field_value(self, field_name):
        """
        Gets the values for the given field and applies the
        defined filters

        :param field_name: name of the models field
        :return: numpy array containing the filtered fields values
        """
        timeseries_filter = slice(None)
        if hasattr(self, 'get_timeseries_mask_filter'):
            timeseries_filter = self.get_timeseries_mask_filter()

        kwargs = {
            'lookup_index': self._get_lookup_index(field_name),
            'timeseries_filter': timeseries_filter
        }

        value = self.get_field_value(field_name, **kwargs)

        # Transform the base_filter by prepending slice(None) to
        # match the dimensionality of the nparray_dict[key].shape
        #
        #      shape(100,) => _filter = [base_filter]
        #      shape(2, 100)  => _filter = [slice(None), base_filter]
        #
        #      Note: x[slice(None),[1,2,3]] == x[:,[1,2,3]]
        # if hasattr(self, 'get_timeseries_mask_filter'):
        #     timeseries_filter = self.get_timeseries_mask_filter()
        # else:
        #     timeseries_filter = slice(None)

        # if isinstance(self.get_field(field_name), TimeSeriesArrayField):
        #     # _filter = [timeseries_filter, self.boolean_mask_filter]
        #     # Fast slicing by first using timeseries_filter and
        #     # and than slice based on boolean_mask_filter
        #     # Can use a lot more memory though....
        #
        #     # TODO: if the result is many timeseries, perform boolean_filter
        #     # per batch
        #     value = value[timeseries_filter, :][:, self.boolean_mask_filter]
        # else:
        _filter = [slice(None)] * (
            len(value.shape) - 1) + [self.boolean_mask_filter]

        # By default load all data from H5,
        # this is WAY much faster
        if isinstance(value, Dataset):
            value = value[:]

        # Perform slicing by applying the mask
        value = value[_filter]

        # Reproject any coordinates if a reproject_to_epsg is set and
        # there are coordinatefields in the selection
        if self.reproject_to_epsg and self._is_coords(field_name):
            value = self.__do_reproject_value(
                    value, field_name, self.reproject_to_epsg)

        if isinstance(value, np.ma.core.MaskedArray):
            # Always return the data of a masked array
            value = value.data

        return value

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

    @property
    def fields(self):
        """
        Returns: a list of ArrayFields names (excluding 'meta')
        """
        return [unicode(x) for x in self._field_names if x != 'meta']

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

        for key, value in kwargs.iteritems():
            splitted_key = key.split('__')
            if splitted_key[0] not in self.fields:
                raise ValueError(
                    "Field '{}' unknown. Choices are {}".format(
                        splitted_key[0],
                        self.fields)
                )

            new_slice_filters.append(
                get_filter(
                    splitted_key,
                    self.get_field(splitted_key[0]),
                    value,
                    filter_map=self._filter_map)
            )

        return new_slice_filters

    def _filter_as(self, klass, **kwargs):
        """
        Same as self.filter, but now return "klass" instance instead of
        self.__class__ instance
        """
        slice_filters = self.__get_filters(**kwargs)
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update(
            {'slice_filters': slice_filters})

        return self.__init_class(klass, **new_class_kwargs)

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

    def slice(self, s, override_filter_error=False):
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

        slice_filter = s

        if not isinstance(s, slice):
            raise TypeError(
                'Type %s not supported, must be a slice' % type(s,)
            )

        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update(
            {'slice_filters':
             [SliceFilter(slice_filter)] + self.slice_filters})

        return self.__init_class(
            self.__class__, new_class_kwargs)

    @property
    def known_subset(self):
        if not hasattr(self, 'SUBSETS'):
            return "has no subsets defined"
        return list(
            chain(*[v.keys() for v in self.SUBSETS.itervalues()])
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

        if isinstance(name, basestring):
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
            if x not in self.fields:
                raise Exception("Unknown field name: {0}".format(x))

        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update(
            {'only_fields': self.only_fields + list(args)})

        return self.__init_class(
            self.__class__, **new_class_kwargs)

    def __do_filter(self):
        """
        Performs: the filters defined in self._filters

        Returns: a dictionairy with filtered values
        """

        # No cached data
        # filter all the data using the defined filters.

        selection = OrderedDict()

        for n in self.fields:
            selection[n] = self.get_field_value(n)

        # Apply all filters sequential on the selection dict
        # Every filter can, when matches are found, remove items
        # from the values in the dict.
        #
        # For example filtering on content_pk=2 works like:
        #      1. Get the boolean mask:
        #              mask = selection['content_pk'][
        #                  selection['content_pk'] ==  2]
        #      2. Apply it to all values in selection.
        #              selection[x] = selection[x][mask]
        #              (for x in selection.keys())
        for filter_instance in self.slice_filters:
            filter_instance.filter_dict(selection, self)

        # Reproject any coordinates if a reproject_to_epsg is set and
        # there are coordinatefields in the selection
        if self.reproject_to_epsg and self._includes_coords(selection):
            selection = self.__do_reproject(
                    selection, self.reproject_to_epsg)

        # Prune all unwanted fields
        if self.only_fields:
            for key in [x for x in selection.keys()
                        if x not in self.only_fields]:
                selection.pop(key)
        if not self.slice_filters:
            selection = self._get_values(selection)
        return selection

    def _get_values(self, selection):
        """
        when no filters are specified, we are still operating on the hdf5
        groups so get the values explicitly

        :param selection: ordered dict of selected fields
            with group datasets
        :return: new ordered dict with values from group datasets
        """

        _tmp = OrderedDict()
        for k, v in selection.iteritems():
            try:
                _tmp[k] = v[:]
            except TypeError:
                pass
        return _tmp

    def to_dict(self):
        """
        Returns: the filtered values as dictionairy
        """
        # Note: the __do_filter functions returns
        # a dictionairy by default.

        selection = OrderedDict()

        for n in self.fields:
            if not self.only_fields or n in self.only_fields:
                selection[n] = self.get_filtered_field_value(n)

        return selection

    def to_list(self):
        """
        :return: list of dicts with key's and values
        """

        # Filter results and transform the result to
        # and np.ndarray
        selection = self.to_dict()
        if len(selection.values()) > 1:
            array = np.array(selection.values())
        else:
            array = selection.values()[0]

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
        return [dict(zip(selection.keys(), x)) for x in data]

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

            timeseries_filter = slice(None)
            if hasattr(self, 'get_timeseries_mask_filter'):
                timeseries_filter = self.get_timeseries_mask_filter()
            # kwargs = {
            #     'lookup_index': self._lookup_index,
            #     'timeseries_filter': timeseries_filter
            # }

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
        if len(selection.values()) > 1:
            return np.array(selection.values())
        return selection.values()[0]

    @property
    def data(self):
        """
        Returns: the (filtered) data a dictionairy
        """
        return self.to_dict()

    def __repr__(self):
        """human readable representation of the instance"""
        return "<orm {} instance of {}>".format(
            self.__contenttype__(), self.model_name
        )

    def __contenttype__(self):
        """conent type, e.g. lines, nodes, cells, ..."""
        return self._datasource.group_name
