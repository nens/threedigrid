# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import numpy as np

from threedigrid.orm.base.fields import TimeSeriesCompositeArrayField
from threedigrid.orm.base.fields import TimeSeriesArrayField


class ResultMixin(object):
    """
    Subclass this mixin and add the result
    fields as 'TimeSeriesArrayField'
    """
    timeseries_mask = None
    _done_composition = False

    def __init__(self, *args, **kwargs):
        # pop mixin specific fields and store them
        # in the class_kwargs
        self.timeseries_mask = kwargs.pop('timeseries_mask', None)
        self.class_kwargs.update({
            'timeseries_mask': self.timeseries_mask})
        if not self._done_composition and hasattr(self, 'Meta'):
            self._set_composite_field_names()

    def _set_composite_field_names(self):

        # composite_field_name_dict = '{model_name}_COMPOSITE_FIELDS'.format(
        #         model_name=self.__class__.__name__.upper())
        # if not hasattr(constants, composite_field_name_dict):
        #     return
        if not hasattr(self.Meta, 'composite_fields'):
            return

        fields = {
            v: TimeSeriesCompositeArrayField(meta=self.Meta)
            for v in self.Meta.composite_fields.keys()
        }
        self._meta.add_fields(fields, hide_private=True)
        self.done_composition = True

    def timeseries(self, start_time=None, end_time=None, indexes=None):
        """
        Allows filtering on timeseries.

        You can either filter by start_time and end_time or indexes.

        Example usage for start_time and end_time filter::

            >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
            >>> nc = "/code/tests/test_files/results_3di.nc"
            >>> f = "/code/tests/test_files/gridadmin.h5"
            >>> gr = GridH5ResultAdmin(f, nc)
            >>> gr.nodes.timeseries(start_time=0, end_time=10).s1

        Example usage for index filter::

            >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
            >>> nc = "/code/tests/test_files/results_3di.nc"
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
        time_key = 'time'
        if not time_key in self._datasource.keys():
            raise AttributeError(
                'Result {} has no attribute {}'.format(
                    self._datasource.netcdf_file.filepath(), time_key)
            )
        value = self._datasource['time'][:]
        if self.timeseries_mask is not None:
            value = value[self.timeseries_mask]
        return value



class AggregateResultMixin(ResultMixin):
    """
    Subclass this mixin and add the result
    fields as 'TimeSeriesArrayField'
    """
    def __init__(self, *args, **kwargs):
        super(AggregateResultMixin, self).__init__(*args, **kwargs)

    def timeseries(self, start_time=None, end_time=None, indexes=None):
        """
        """
        self.timeseries_mask = {}
        field_names = self._meta.get_fields()
        for field_name, field_inst in field_names.iteritems():
            if not isinstance(field_inst, TimeSeriesArrayField):
                continue
            ts = self.get_timestamps(field_name)
            mask = self._get_mask(start_time, end_time, indexes, ts)
            self.timeseries_mask[field_name] = mask

        # Create a copy of the class_kwargs
        # and update it with timeseries_mask
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update({
            'timeseries_mask': self.timeseries_mask})

        return self.__class__(
            datasource=self._datasource,
            **new_class_kwargs)

    def _get_mask(self, start_time, end_time, indexes, timestamps):
        if not any((start_time, end_time, indexes)):
            raise KeyError(
                "Please provide either start_time, end_time or indexes")

        timeseries_mask = True
        if any((start_time, end_time)):
            if start_time:
                timeseries_mask &= timestamps >= start_time
            if end_time:
                timeseries_mask &= timestamps <= end_time

            timeseries_mask = timeseries_mask
        else:
            if isinstance(indexes, list) or isinstance(indexes, tuple):
                timeseries_mask = np.array(indexes)
            elif isinstance(indexes, slice):
                timeseries_mask = indexes
            else:
                raise TypeError(
                    "indexes should either be a list/tuple or a slice")

        return timeseries_mask

    def get_timeseries_mask_filter(self):
        """
        :return: the timeseries mask to be used for filtering
                 on timeseries
        """
        if self.timeseries_mask:
            return self.timeseries_mask
        return self.class_kwargs.get('timeseries_chunk_size')

    @property
    def timestamps(self):
        raise AttributeError(
            'Aggregation results do not have a global "timestamps" attribute. '
            'Use get_timestamp(<field_name>) instead'
        )

    def get_timestamps(self, field_name):
        """
        Get the array of timestamps for a result field

        :param field_name: name of the field
        :return: array of timestamps
        :raises AttributeError when no the field has no timestamps
        """

        time_key = 'time_' + field_name

        if time_key in self._datasource.keys():
            arr = self._datasource[time_key][:]
            # TODO: threedicore will implement this as an common array not an
            # masked array soon, change accordingly
            if hasattr(arr, 'data'):
                return arr.data
            return arr
        raise AttributeError('No timestamps found for {}'.format(field_name))

    def get_time_unit(self, field_name):
        """
        Get the time unit for a result field
        :param field_name: name of the field
        :return: <string> time unit
        :raises AttributeError when the field has no time unit attribute
        """

        time_key = 'time_' + field_name

        if time_key in self._datasource.keys():
            arr = self._datasource[time_key]
            try:
                return arr.getncattr('units')
            except AttributeError:
                raise AttributeError(
                    'No time unit found for field {}'.format(field_name)
                )
