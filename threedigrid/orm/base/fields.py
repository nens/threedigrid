# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Base fields
"""
from __future__ import unicode_literals
from __future__ import print_function

from threedigrid.orm import constants

import numpy as np


class ArrayField:
    """
    Generic field that can be used to describe values
    to be retrieved from a Datasource.
    """
    @staticmethod
    def get_value(datasource, name, **kwargs):
        """
        Returns: the data from the datasource
                 or None if 'name' is not in the datasource

        Optional transforms can be done here.
        """
        if name in datasource.keys():
            return datasource[name]

        return None


class IndexArrayField(ArrayField):
    """
    Simple pointer
    """
    def __init__(self, to=None):
        self.to = to


class TimeSeriesArrayField(ArrayField):

    @staticmethod
    def get_value(datasource, name, **kwargs):
        timeseries_filter = kwargs.get('timeseries_filter', slice(None))
        v = datasource[name][timeseries_filter]
        if v.size > 0:
            return v
        return np.array([])


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

    def __init__(self, needs_lookup=True, meta=None):
        self._needs_lookup = needs_lookup
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
        timeseries_filter = kwargs.get('timeseries_filter', slice(None))
        lookup_index = kwargs.get('lookup_index')

        values = []
        source_names = self._meta.composite_fields.get(name)
        for source_name in source_names:
            if source_name not in datasource.keys():
                continue
            values.append(datasource[source_name][timeseries_filter])

        if not values:
            return np.array([])
        # combine the two source to a single source
        # if timeseries_filter is None and lookup_index is None:
        #     return np.hstack([x[:,] for x in values])
        hs = np.hstack(values)
        del values
        # sort the stacked array by lookup
        if self._needs_lookup and lookup_index is not None:
            return hs[:, lookup_index]
        return hs
