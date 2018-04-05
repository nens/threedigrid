# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Base fields
"""
from __future__ import unicode_literals
from __future__ import print_function
import numpy as np


class ArrayField:
    """
    Generic field that can be used to describe values
    to be retrieved from a Datasource.
    """
    @staticmethod
    def get_value(datasource, name):
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
    pass


class MappedSubsetTimeSeriesArrayField(TimeSeriesArrayField):
    def __init__(self, mapping=[], null_value=-9999):
        """
        Timeseries field that maps a timeserie array onto a
        subset of the gridadmin array's. For example ucx which
        is only defined for subset 2D_open_water.

        :param mapping: list of dicts with the mapping of fields like
                        [{'source': 'ucx', 'subset': '2D_open_water'}]

        :param null_value: null value to use outside the subset.
        """
        self.mapping = mapping
        self.null_value = null_value

    def get_mappings(self, value, model_instance):
        SUBSETS = model_instance.SUBSETS

        mappings = []

        for subset_def in value:
            name = subset_def['subset'].upper()
            field_filter = [key for key in SUBSETS if
                            name in SUBSETS[key]]
            field_filter = field_filter[0]
            splitted_key = field_filter.split('__')

            value = SUBSETS[field_filter][name]
            slice_filter = model_instance._get_filter(
                splitted_key,
                model_instance.get_field(splitted_key[0]),
                value,
                filter_map=model_instance._filter_map)

            selection = {}
            subset_field_name = slice_filter.get_field_name()
            selection[subset_field_name] = model_instance.get_field_value(
                subset_field_name)

            subset_mask = slice_filter.get_boolean_mask_filter(
                selection, model_instance)

            # mapped_mask = boolean_mask[filter_bool_mask]
            mappings.append([subset_mask, subset_def['value']])

        # Return the boolean mask and the mappings
        return mappings

    def get_value(self, datasource, name):
        """
        Returns: a list with the netCDF datasets.
        """
        return [
            {'value': datasource[map_def['source']],
             'null_value': self.null_value,
             'subset': map_def['subset']}
            for map_def in self.mapping
            if map_def['source'] in datasource.keys()]
