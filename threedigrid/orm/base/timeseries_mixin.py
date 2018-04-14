# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from collections import defaultdict
from collections import namedtuple

import numpy as np

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
    def __init__(self, inst):
        """
        :param inst: model instance
        """
        self.inst = inst
        if hasattr(self.inst.Meta, "field_attrs"):
            self._set_field_attrs()

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

        for _field in self.inst.fields:
            meta_values = self._get_meta_values(_field)
            nt = namedtuple(_field, ','.join(self.inst.Meta.field_attrs))
            setattr(self, _field, nt(*meta_values[_field]))

    def _is_type_composite(self, field_name):
        """
        :param field_name: name of the field
        """
        field = self.inst.get_field(field_name)
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


class ResultMixin(object):
    """
    Subclass this mixin and add the result
    fields as 'TimeSeriesArrayField'
    """
    timeseries_mask = None
    done_composition = False

    def __init__(self, *args, **kwargs):
        # pop mixin specific fields and store them
        # in the class_kwargs
        self.timeseries_mask = kwargs.pop('timeseries_mask', None)
        self.class_kwargs.update({
            'timeseries_mask': self.timeseries_mask})
        if not self.done_composition:
            self._set_composite_field_names()

    def _set_composite_field_names(self):

        # composite_field_name_dict = '{model_name}_COMPOSITE_FIELDS'.format(
        #         model_name=self.__class__.__name__.upper())
        # if not hasattr(constants, composite_field_name_dict):
        #     return
        if not self.Meta.composite_fields:
            return

        for var in self.Meta.composite_fields.keys():
            setattr(
                self, var, TimeSeriesCompositeArrayField(
                    needs_lookup=True, meta=self.Meta)
            )
        self.update_field_names(
            self.Meta.composite_fields.keys(), exclude_private=True
        )
        self.done_composition = True

    def update_field_names(self, field_names, exclude_private=True):
        """

        :param field_names: iterable of field names
        :param exclude_private: fields starting with '_' will be excluded
        """
        # remove private fields
        fnames = [x for x in field_names if
                  exclude_private and not x.startswith('_')]

        # combine with existing fields
        self._field_names = set(
            fnames).union(set(self.fields))

    def timeseries(self, start_time=None, end_time=None, indexes=None):
        """
        Allows filtering on timeseries.

        You can either filter by start_time and end_time or indexes.

        Example usage for start_time and end_time filter::

            >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
            >>> nc = "/code/tests/test_files/subgrid_map.nc"
            >>> f = "/code/tests/test_files/gridadmin.h5"
            >>> gr = GridH5ResultAdmin(f, nc)
            >>> gr.nodes.timeseries(start_time=0, end_time=10).s1

        Example usage for index filter::

            >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
            >>> nc = "/code/tests/test_files/subgrid_map.nc"
            >>> f = "/code/tests/test_files/gridadmin.h5"
            >>> gr = GridH5ResultAdmin(f, nc)
            >>> qs_s1 = gr.nodes.timeseries(indexes=[1, 2, 3]).s1
            >>> qs_s1.shape
            >>> (3, 25156)

        A more complex example combining filters::

            >>> breaches_u1 = gr.lines.filter(kcu__eq=55).timeseries(indexes=[10, 11, 12, 13]).u1  # noqa
            >>> breaches_u1.shape
            >>> (4, 16)

        Filtering by indexes works with both lists (like in the examples above)
        and slices. This code yields exactly the same result

            >>> breaches_u1_slice = gr.lines.filter(kcu__eq=55).timeseries(indexes=slice(10,14)).u1  # noqa
            >>> breaches_u1_slice.shape
            >>> (4, 16)
            >>> assert np.all(breaches_u1 == breaches_u1_slice)

        :return: new instance with filtering options enabled
        """

        timestamps = self.timestamps

        timeseries_mask = True

        if not any((start_time, end_time, indexes)):
            raise KeyError(
                "Please provide either start_time, end_time or indexes")

        if any((start_time, end_time)):
            if start_time:
                timeseries_mask &= timestamps >= start_time
            if end_time:
                timeseries_mask &= timestamps <= end_time

            self.timeseries_mask = timeseries_mask
        else:
            if isinstance(indexes, list) or isinstance(indexes, tuple):
                self.timeseries_mask = np.array(indexes)
            elif isinstance(indexes, slice):
                self.timeseries_mask = indexes
            else:
                raise TypeError(
                    "indexes should either be a list/tuple or a slice")

        # Create a copy of the class_kwargs
        # and update it with timeseries_mask
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update({
            'timeseries_mask': self.timeseries_mask})

        return self.__class__(
            datasource=self._datasource,
            **new_class_kwargs)

    def get_timeseries_mask_filter(self):
        """
        :return: the timeseries mask to be used for filtering
                 on timeseries
        """
        if self.timeseries_mask is not None:
            return self.timeseries_mask
        return self.class_kwargs.get('timeseries_chunk_size')

    @property
    def timestamps(self):
        """
        Get the list of timestamps for the results
        """
        value = self._datasource['time'][:]
        if self.timeseries_mask is not None:
            value = value[self.timeseries_mask]
        return value

    @property
    def _meta(self):
        """
        meta class that add meta data to a ResultMixin instance. The meta data includes
        entries for the ``_meta_fields`` collection (if found).

            >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
            >>> f = "/code/tests/test_files/results_3di.nc"
            >>> ff = "/code/tests/test_files/gridadmin.h5"
            >>> gr = GridH5ResultAdmin(ff, f)
            >>> gr.nodes._meta.s1
            >>> s1(units=u'm', long_name=u'waterlevel', standard_name=u'water_surface_height_above_reference_datum')
        """
        return Options(self)
