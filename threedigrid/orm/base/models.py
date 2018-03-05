# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np
import logging
from itertools import izip
from itertools import tee
from itertools import chain

from abc import ABCMeta
from collections import OrderedDict

from threedigrid.orm.base.exceptions import OperationNotSupportedError
from threedigrid.orm.base.fields import ArrayField
from threedigrid.orm.base.fields import IndexArrayField
from threedigrid.orm.base.filters import get_filter
from threedigrid.orm.base.filters import SliceFilter

logger = logging.getLogger(__name__)


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
                 has_1d=None, **kwargs):
        """
        Initialize a Model with a datasource, filters
        and a epsg_code.

        The datasource is a wrapped h5py Group from a H5py file or
        an instance that implements the same interface.
        """
        self._datasource = datasource
        self.starts_at = 0  # 0 or 1 based array
        self.slice_filters = slice_filters
        self.only_fields = only_fields
        self.reproject_to_epsg = reproject_to_epsg

        if not epsg_code:
            epsg_code = self._datasource.getattr('epsg_code')
        self.epsg_code = epsg_code

        # Cache the field names
        self._field_names = [
            x for x in dir(self.__class__)
            if isinstance(getattr(self.__class__, x), ArrayField)]
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

    def get_field_value(self, field_name):
        """
        Returns: the value for the ArrayField with name field_name
        on the instance.

        With this in place we can later override the ArrayField
        get_value method for field specific conversion, if needed.
        """
        return self.get_field(field_name).get_value(
            self._datasource, field_name)

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
            get_func = super(Model, self).__getattribute__('to_dict')
            return get_func()[attr_name]

        # Default behaviour, return the attribute from superclass
        return attr

    @property
    def fields(self):
        """
        Returns: a list of ArrayFields names (excluding 'meta')
        """
        return [x for x in self._field_names if x != 'meta']

    def __init_class(self, klass, slice_filters, only_fields=[],
                     reproject_to_epsg=None):
        """
        Returns: a new instance of 'klass' with new filters and
                 same datasource.
        """
        return klass(
            datasource=self._datasource,
            slice_filters=slice_filters,
            only_fields=only_fields,
            epsg_code=self.epsg_code,
            reproject_to_epsg=reproject_to_epsg,
            has_1d=self.has_1d)

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
        return self.__init_class(klass, slice_filters)

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
        return self.__init_class(self.__class__, slice_filters)

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

        return self.__init_class(
            self.__class__, [SliceFilter(slice_filter)] + self.slice_filters)

    @property
    def has_groundwater(self):
        req = self.subset('2D_GROUNDWATER').data
        return len(req['id']) > 0

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

        return self.__init_class(
            self.__class__, self.slice_filters,
            only_fields=self.only_fields + list(args))

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
        return self.__do_filter()

    def to_list(self):
        """
        :return: list of dicts with key's and values
        """

        # Filter results and transform the result to
        # and np.ndarray
        selection = self.__do_filter()
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

    def to_array(self):
        """
        Returns: the filtered values as a numpy array
        """
        selection = self.__do_filter()
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
