# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
Base fields
"""

import numpy as np

from threedigrid.admin.constants import NO_DATA_VALUE


class ArrayField:
    """
    Generic field that can be used to describe values
    to be retrieved from a Datasource.
    """

    def __init__(self, type=None):
        if not hasattr(self, "type"):
            # Optional type that can be used for serializing
            self.type = type

    @staticmethod
    def get_value(datasource, name, **kwargs):
        """
        Returns: the data from the datasource
                 or None if 'name' is not in the datasource

        Optional transforms can be done here.
        """
        if name in list(datasource.keys()):
            return datasource[name]

        return np.array([])

    def __repr__(self):
        return self.__class__.__name__


class BooleanArrayField(ArrayField):
    """
    Generic array field for boolean values.

    Because HDF5 does not support boolean datatype. No data fields are
    interpreted as False.
    """

    def __init__(self):
        self.type = bool

    @staticmethod
    def get_value(datasource, name, **kwargs):
        """
        Returns: the data from the datasource
                 or None if 'name' is not in the datasource

        Optional transforms can be done here.
        """
        if name in list(datasource.keys()):
            data = datasource[name][:]
            data[data == NO_DATA_VALUE] = 0
            return data

        return np.array([])

    def __repr__(self):
        return self.__class__.__name__


class IndexArrayField(ArrayField):
    """
    Simple pointer
    """

    def __init__(self, to=None):
        self.to = to
        self.type = int

    def __repr__(self):
        return self.__class__.__name__


class TimeSeriesArrayField(ArrayField):
    @staticmethod
    def get_value(datasource, name, **kwargs):
        timeseries_filter = kwargs.get("timeseries_filter", slice(None))
        timeseries_filter_to_use = timeseries_filter

        if isinstance(timeseries_filter, np.ndarray):
            if timeseries_filter.dtype == np.dtype(bool):
                # Convert to integer index array
                # to support h5py >= 3.1.0
                timeseries_filter_to_use = np.argwhere(timeseries_filter).flatten()

        if (
            isinstance(timeseries_filter_to_use, np.ndarray)
            and len(datasource[name].shape) > 1
        ):
            v = datasource[name][timeseries_filter_to_use, :]
        else:
            v = datasource[name][timeseries_filter_to_use]
        if v.size > 0:
            return v
        return np.array([])

    def __repr__(self):
        return self.__class__.__name__


class TimeSeriesCompositeArrayField(TimeSeriesArrayField):
    """
    Field for composite arrays.

    Result (netCDF) files split their data into subsets, e.g. 1D and 2D.
    A composite field can be used to combine several data source fields
    into a single model field by specifying a composition dict. Example::

        LINE_COMPOSITE_FIELDS = {
            'au': ['Mesh1D_au', 'Mesh2D_au'],
            'u1': ['Mesh1D_u1', 'Mesh2D_u1'],
            'q': ['Mesh1D_q', 'Mesh2D_q']
        }

    """

    def __init__(self, meta=None):
        self._meta = meta

    def get_value(self, datasource, name, **kwargs):
        """
        :param datasource: a datasource object that can return data on
            __getitem__()
        :param name: the name of the section to read, e.g a HF5
            group or netCDF variable
        :param kwargs:
            timeseries_filter (optional): read only a slice of
                the time dimension
            model_name: name of the model the field belongs to.
                Is used for a reverse lookup of the composite fields
            lookup_index (optional): a numpy array that will be used
                to sort the values by this lookup index

        Returns: the data from the datasource
                 or None if 'name' is not in the datasource

        Optional transforms can be done here.
        """
        timeseries_filter = kwargs.get("timeseries_filter", slice(None))
        # timeseries_filter contains only [False, False,...]
        # (empty) slices pass the condition
        if isinstance(timeseries_filter, np.ndarray):
            if timeseries_filter.dtype == np.dtype(bool) and not np.any(
                timeseries_filter
            ):
                return np.array([])
        lookup_index = kwargs.get("lookup_index")
        values = []
        source_names = self._meta.composite_fields.get(name)

        timeseries_filter_to_use = timeseries_filter

        if isinstance(timeseries_filter, np.ndarray):
            if timeseries_filter.dtype == np.dtype(bool):
                # Convert to integer index array
                # to support h5py >= 3.1.0
                timeseries_filter_to_use = np.argwhere(timeseries_filter).flatten()

        for source_name in source_names:
            if source_name not in list(datasource.keys()):
                continue

            if (
                isinstance(timeseries_filter_to_use, np.ndarray)
                and len(datasource[source_name].shape) > 1
            ):
                values.append(datasource[source_name][timeseries_filter_to_use, :])
            else:
                values.append(datasource[source_name][timeseries_filter_to_use])

        if not values:
            return np.array([])
        # combine the two source to a single source
        hs = np.hstack(values)
        axs = 1 if len(hs.shape) == 2 else 0
        hs = np.insert(hs, 0, 0, axis=axs)
        del values
        # sort the stacked array by lookup
        if lookup_index is not None:
            return hs[:, lookup_index]
        return hs

    def __repr__(self):
        return self.__class__.__name__


class TimeSeriesSubsetArrayField(TimeSeriesArrayField):
    """
    Field for subset arrays (for example only spanning the 2d section)
    """

    def __init__(self, source_name=None, size=None):
        self._source_name = source_name
        self._size = size

    def get_value(self, datasource, name, **kwargs):
        """
        :param datasource: a datasource object that can return data on
            __getitem__()
        :param name: the name of the section to read, e.g a HF5
            group or netCDF variable
        :param kwargs:
            timeseries_filter (optional): read only a slice of
                the time dimension
            subset_index: index array where to store the subset
                values
            lookup_index (optional): a numpy array that will be used
                to sort the values by this lookup index

        Returns: the data from the datasource or None if 'name' is not
            in the datasource

        Optional transforms can be done here.
        """
        timeseries_filter = kwargs.get("timeseries_filter", slice(None))
        subset_index = kwargs["subset_index"]
        # timeseries_filter contains only [False, False,...]
        # (empty) slices pass the condition
        if isinstance(timeseries_filter, np.ndarray):
            if timeseries_filter.dtype == np.dtype(bool) and not np.any(
                timeseries_filter
            ):
                return np.array([])

        timeseries_filter_to_use = timeseries_filter

        if isinstance(timeseries_filter, np.ndarray):
            if timeseries_filter.dtype == np.dtype(bool):
                # Convert to integer index array
                # to support h5py >= 3.1.0
                timeseries_filter_to_use = np.argwhere(timeseries_filter).flatten()

        if self._source_name not in list(datasource.keys()):
            return np.array([])
        source_data = datasource[self._source_name][timeseries_filter_to_use, :]
        shp = (source_data.shape[0], self._size)
        templ = np.zeros(shp, dtype=source_data.dtype)

        # Fix trash element mis-aligments
        if source_data.shape[1] == subset_index.shape[0] - 1:
            subset_index = subset_index[1:]

        # Note: subset_index already contains correct sorting
        # that matches with the NetCDF timeseries.
        templ[:, subset_index] = source_data

        return templ

    def __repr__(self):
        return self.__class__.__name__


def resolve_h5py_file_datasource(h5py_file, dotted_path):
    # Follow the 'path' with dots to get a datasource
    # in the h5py_file
    # For example:
    #    dotted_path = 'lines.id'
    res = h5py_file
    for key in dotted_path.split("."):
        try:
            res = res.get(key)
        except AttributeError:
            return np.array([])
    return res[:]
