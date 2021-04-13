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
        self.timeseries_filter = kwargs.pop('timeseries_filter', None)
        self.timeseries_sample = kwargs.pop("timeseries_sample", None)
        self.timeseries_mask = None
        self.class_kwargs.update({
            'timeseries_filter': self.timeseries_filter,
            'timeseries_sample': self.timeseries_sample})
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
        id_value = self.get_field_value('id')
        if id_value:
            count = self.get_field_value('id').size
        else:
            # Dummy value
            count = 1024
        for v, k in six.iteritems(self.Meta.subset_fields):
            _source_name = _flatten_dict_values(k)
            if not _source_name:
                continue
            source_name = _source_name[0]

            fields[v] = TimeSeriesSubsetArrayField(
                source_name=source_name, size=count
            )

        self._meta.add_fields(fields, hide_private=True)

    def generate_timeseries_mask(
            self, start_time=None, end_time=None, indexes=None):
        timestamps = self.timestamps
        timeseries_mask = True

        if all((start_time is None, end_time is None, indexes is None)):
            raise KeyError(
                "Please provide either start_time, end_time or indexes")

        if any((start_time is not None, end_time is not None)):
            if start_time is not None:
                timeseries_mask &= timestamps >= start_time
            if end_time is not None:
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

        if self.timeseries_sample:
            num_points = self.timeseries_sample['num_points']
            # Only sample if the required num_points is smaller
            # than the available points
            timestamps_size = self.timestamps.size
            if timestamps_size > num_points:
                if isinstance(self.timeseries_mask, slice):
                    indexes = np.arange(
                        timestamps_size
                    )[self.timeseries_mask].flatten().tolist()
                else:
                    indexes = np.argwhere(
                        self.timeseries_mask).flatten().tolist()

                if hasattr(self._datasource, 'swmr_mode'):
                    # always exclude the last item in swmr_mode, to be sure
                    # that the datasource['time'].size is the same
                    # as of the datasource['xxx'].size datasets that
                    # are going to be sampled.
                    indexes = indexes[:-1]

                self.timeseries_mask = self._get_indexes_subset(
                    indexes,
                    limit=self.timeseries_sample['num_points'],
                    include_end=self.timeseries_sample['include_end'])

    def _get_indexes_subset(self, indexes, limit, include_end=True):
        """
        Get indexes subset with length limit
        """

        # only limit if needed
        if len(indexes) <= limit:
            return indexes

        start = indexes[0]
        end = indexes[-1]
        divider = (end - start) / float(limit)
        indexes = []

        if include_end:
            divider = -divider
            x = end
        else:
            x = start

        while len(indexes) < limit:
            indexes.append(round(x))
            x += divider

        if include_end:
            indexes = indexes[::-1]

        return indexes

    def sample(self, num_points=None, include_end=True):
        """
        Sample the requested timeseries and return at
        maximum 'num_points' amount of points.

        :param num_points: the amount of sample points to return
        :param include_end: if true, the last point is always included,
                            else the first point is always included.
        """
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update({
            'timeseries_sample': {
                'num_points': num_points,
                'include_end': include_end}
        })

        return self.__class__(
            datasource=self._datasource,
            **new_class_kwargs)

    def timeseries(
            self, start_time=None, end_time=None, indexes=None):
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

        # self.generate_timeseries_mask(start_time, end_time, indexes)

        # Create a copy of the class_kwargs
        # and update it with timeseries_mask
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update({
            'timeseries_filter': {
                'start_time': start_time,
                'end_time': end_time,
                'indexes': indexes}
        })

        return self.__class__(
            datasource=self._datasource,
            **new_class_kwargs)

    def get_timeseries_mask_filter(self):
        """
        :return: the timeseries mask to be used for filtering
                 on timeseries
        """
        if self.timeseries_mask is None and self.timeseries_filter is not None:
            self.generate_timeseries_mask(
                **self.timeseries_filter
            )
        if self.timeseries_mask is not None:
            return self.timeseries_mask
        return self.class_kwargs.get('timeseries_chunk_size')

    @property
    def timestamps(self):
        """
        Get the list of timestamps for the results
        """

        # override if datasource has get_timestamps function
        if hasattr(self._datasource, 'get_timestamps'):
            return self._datasource.get_timestamps()

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

    def get_timestamps(self, timeseries_mask):
        time_key = 'time'
        if time_key not in list(self._datasource.keys()):
            raise AttributeError(
                'Result {} has no attribute {}'.format(
                    self._datasource.netcdf_file.filepath(), time_key)
            )
        value = self._datasource['time'][:]
        return value[timeseries_mask]

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
    is_aggregate = True

    def __init__(self, *args, **kwargs):
        super(AggregateResultMixin, self).__init__(*args, **kwargs)

        # Create a copy of the class_kwargs
        # and update it with timeseries_mask
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update({
            'timeseries_mask': self.timeseries_mask})

    def get_timeseries_mask_filter(self):
        """
        :return: the timeseries mask to be used for filtering
                 on timeseries
        """
        if self.timeseries_filter is not None:
            start_time = self.timeseries_filter['start_time']
            end_time = self.timeseries_filter['end_time']
            indexes = self.timeseries_filter['indexes']

            self.timeseries_mask = {}
            field_names = self._meta.get_fields()
            for field_name, field_inst in six.iteritems(field_names):
                if not isinstance(field_inst, TimeSeriesArrayField):
                    continue
                ts = self.get_timestamps(field_name)
                mask = self._get_mask(start_time, end_time, indexes, ts)
                self.timeseries_mask[field_name] = mask
            return self.timeseries_mask
        return None

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
        new_class_kwargs = dict(self.class_kwargs)
        new_class_kwargs.update({
            'timeseries_filter': {
                'start_time': start_time,
                'end_time': end_time,
                'indexes': indexes}
        })
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
        if all((start_time is None, end_time is None, indexes is None)):
            raise KeyError(
                "Please provide either start_time, end_time or indexes")

        timeseries_mask = True
        if any((start_time is not None, end_time is not None)):
            if start_time is not None:
                timeseries_mask &= timestamps >= start_time
            if end_time is not None:
                timeseries_mask &= timestamps <= end_time

            timeseries_mask = timeseries_mask
        else:
            if isinstance(indexes, slice):
                timeseries_mask = indexes
            else:
                raise TypeError(
                    "indexes should either be a slice")

        return timeseries_mask

    @property
    def timestamps(self):
        timestamps_dict = {}

        for field_name, field in self._meta.get_fields().items():
            if isinstance(field, TimeSeriesArrayField):
                try:
                    timestamps_dict[field_name] = self.get_timestamps(
                        field_name)
                except (AttributeError, TypeError):
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
