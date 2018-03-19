import numpy as np

DEFAULT_TIMESERIES = slice(0, 10)


class ResultMixin(object):
    """
    Subclass this mixin and add the result
    fields as 'TimeSeriesArrayField'
    """

    timeseries_mask = None

    def __init__(self, *args, **kwargs):
        # pop mixin specific fields and store them
        # in the class_kwargs
        print('__init__', args, kwargs)
        self.timeseries_mask = kwargs.pop('timeseries_mask', None)
        self.class_kwargs.update({
            'timeseries_mask': self.timeseries_mask})

    def timeseries(self, start_time=None, end_time=None, indexes=None):
        """
        Allows filtering on timeseries.

        :return: new instance with filtering options enabled
        """

        timestamps = self.timestamps

        timeseries_mask = True

        if not any((start_time, end_time, indexes)):
            raise Exception(
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
                raise Exception(
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

        return DEFAULT_TIMESERIES

    @property
    def timestamps(self):
        """
        Get the list of timestamps for the results
        """
        value = self._datasource['time'][:]
        if self.timeseries_mask is not None:
            value = value[self.timeseries_mask]
        return value
