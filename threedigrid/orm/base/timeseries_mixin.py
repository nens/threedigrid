# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np
# optional install results
try:
    from cftime import num2date
except ImportError:
    pass

from threedigrid.orm.base.fields import TimeSeriesCompositeArrayField
from threedigrid.orm.base.fields import TimeSeriesSubsetArrayField
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.orm.base.utils import _flatten_dict_values

import six


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
            self._set_composite_fields()
            self._set_subset_fields()

    def _set_composite_fields(self):
        """
        add composite fields to the instance
        """

        if not hasattr(self.Meta, 'composite_fields'):
            return

        fields = {
            v: TimeSeriesCompositeArrayField(meta=self.Meta)
            for v in self.Meta.composite_fields.keys()
        }
        self._meta.add_fields(fields, hide_private=True)
        self._done_composition = True

    def _set_subset_fields(self):
        """
        add subset fields to the instance
        """
        if not hasattr(self, 'Meta'):
            return

        if not hasattr(self.Meta, 'subset_fields'):
            return

        fields = {}
        count = self.get_field_value('id').size
        for v, k in six.iteritems(self.Meta.subset_fields):
            _source_name = _flatten_dict_values(k)
            if not _source_name:
                continue
            source_name = _source_name[0]

            fields[v] = TimeSeriesSubsetArrayField(
                source_name=source_name, size=count
            )

        self._meta.add_fields(fields, hide_private=True)

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
        if time_key not in list(self._datasource.keys()):
            raise AttributeError(
                'Result {} has no attribute {}'.format(
                    self._datasource.netcdf_file.filepath(), time_key)
            )
        value = self._datasource['time'][:]
        if self.timeseries_mask is not None:
            value = value[self.timeseries_mask]
        return value

    @property
    def dt_timestamps(self):
        return [
            t.isoformat() for t in num2date(
                self.timestamps,
                units=self._datasource['time'].attrs.get(
                    'units').decode('utf-8'))
        ]


class AggregateResultMixin(ResultMixin):
    """
    Subclass this mixin and add the result
    fields as 'TimeSeriesArrayField' or TimeSeriesCompositeArrayField
    """
    def __init__(self, *args, **kwargs):
        super(AggregateResultMixin, self).__init__(*args, **kwargs)

    def timeseries(self, start_time=None, end_time=None, indexes=None):
        """
        Allows filtering on timeseries.

        :param start_time: start_time in seconds
        :param end_time: end_time in seconds
        :param indexes: a slice, e.g. slice(<start>, <stop>, <step>)

        You can either filter by start_time and end_time or indexes. Indexes,
        unlike the GridH5ResultAdmin timeseries filter, allows only for slices
        when used with aggregated results.

        Example usage for start_time and end_time filter::

            >>> from threedigrid.admin.gridresultadmin import GridH5AggregateResultAdmin # noqa
            >>> nc = "/code/tests/test_files/aggregate_results_3di.nc"
            >>> f = "/code/tests/test_files/gridadmin.h5"
            >>> gr = GridH5AggregateResultAdmin(f, nc)
            >>> gr.nodes.timeseries(start_time=0, end_time=800).s1_max

        Example usage for index filter::

            >>> from threedigrid.admin.gridresultadmin import GridH5AggregateResultAdmin # noqa
            >>> nc = "/code/tests/test_files/aggregate_results_3di.nc"
            >>> f = "/code/tests/test_files/gridadmin.h5"
            >>> gr = GridH5AggregateResultAdmin(f, nc)
            >>> qs_s1 = gr.nodes.timeseries(indexes=slice(0,3)).s1
            >>> qs_s1.shape[0]
            >>> 3

        """
        self.timeseries_mask = {}
        field_names = self._meta.get_fields()
        for field_name, field_inst in six.iteritems(field_names):
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
        """

        :param start_time: start_time in seconds
        :param end_time: end_time in seconds
        :param indexes: a slice, e.g. slice(<start>, <stop>, <step>)
        :param timestamps: array of timestamps in seconds
        :return:
        """
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
            if isinstance(indexes, slice):
                timeseries_mask = indexes
            else:
                raise TypeError(
                    "indexes should either be a slice")

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
        timestamps_dict = {}

        for field_name, field in self._meta.get_fields().items():
            if isinstance(field, TimeSeriesArrayField):
                try:
                    timestamps_dict[field_name] = self.get_timestamps(
                        field_name)
                except AttributeError:
                    timestamps_dict[field_name] = np.array([])

        return timestamps_dict

    def get_timestamps(self, field_name):
        """
        Get the array of timestamps for a result field

        :param field_name: name of the field
        :return: array of timestamps
        :raises AttributeError when no the field has no timestamps
        """

        time_key = 'time_' + field_name

        if time_key in list(self._datasource.keys()):
            field_timestamps = self._datasource[time_key][:]
            # Mask the field_timestamps with the timeseries_mask of
            # that field when available
            if ((hasattr(self, 'timeseries_mask') and
                 self.timeseries_mask is not None)):
                if field_name in self.timeseries_mask:
                    field_timestamps = field_timestamps[
                        self.timeseries_mask[field_name]]
            return field_timestamps
        raise AttributeError('No timestamps found for {}'.format(field_name))

    def get_time_unit(self, field_name):
        """
        Get the time unit for a result field
        :param field_name: name of the field
        :return: <string> time unit
        :raises AttributeError when the field has no time unit attribute
        """

        time_key = 'time_' + field_name

        if time_key in list(self._datasource.keys()):
            arr = self._datasource[time_key]
            try:
                return arr.attrs.get('units')
            except AttributeError:
                raise AttributeError(
                    'No time unit found for field {}'.format(field_name)
                )
