# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import logging
import numpy as np
from threedigrid.orm.base.datasource import DataSource
from collections import OrderedDict
from h5py._hl.dataset import Dataset
from threedigrid.admin.h5py_swmr import H5SwmrFile


logger = logging.getLogger(__name__)


class H5pyGroup(DataSource):
    """
    Datasource wrapper for h5py groups,
    adding meta data to all groups.
    """
    _group_name = None
    _h5py_file = None

    def get_filtered_field_value(
            self, model, field_name, ts_filter=None, lookup_index=None,
            subset_index=None):

        kwargs = {}
        if ts_filter is None:
            if hasattr(model, 'get_timeseries_mask_filter'):
                timeseries_filter = model.get_timeseries_mask_filter()
                ts_filter = timeseries_filter
                if isinstance(timeseries_filter, dict):
                    ts_filter = timeseries_filter.get(field_name)

        if ts_filter is not None:
            kwargs.update(
                {'timeseries_filter': ts_filter}
            )

        if lookup_index is None:
            if model._mixin and hasattr(model.Meta, 'lookup_fields'):
                lookup_index = model._meta._get_lookup_index()

        if lookup_index is not None:
            kwargs.update({'lookup_index': lookup_index})

        if subset_index is None:
            if model._mixin and hasattr(model.Meta, 'subset_fields'):
                subset_index = model._get_subset_idx(field_name)

        if subset_index is not None:
            kwargs.update({'subset_index': model._get_subset_idx(field_name)})

        value = model.get_field_value(field_name, **kwargs)

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

        # Return a numpy array with None as only element when
        # the value is None.
        if value is None or value.size == 0:
            return np.array([])

        _filter = [slice(None)] * (
            len(value.shape) - 1) + [model.boolean_mask_filter]

        # By default load all data from H5,
        # this is WAY much faster
        if isinstance(value, Dataset):
            value = value[:]

        # Perform slicing by applying the mask
        value = value[tuple(_filter)]

        # Reproject any coordinates if a reproject_to_epsg is set and
        # there are coordinatefields in the selection
        if model.reproject_to_epsg and model._is_coords(field_name):
            value = model._do_reproject_value(
                    value, field_name, model.reproject_to_epsg)

        if isinstance(value, np.ma.core.MaskedArray):
            # Always return the data of a masked array
            value = value.data

        return value

    def execute_query(self, model):
        """
        Process a query on the model
        """
        selection = OrderedDict()

        ts_filter = None
        timeseries_filter = None
        lookup_index = None
        has_subsets = False

        if hasattr(model, 'get_timeseries_mask_filter'):
            timeseries_filter = model.get_timeseries_mask_filter()

        if model._mixin and hasattr(model.Meta, 'lookup_fields'):
            lookup_index = model._meta._get_lookup_index()

        if model._mixin and hasattr(model.Meta, 'subset_fields'):
            has_subsets = True

        for n in model._field_names:
            if not model.only_fields or n in model.only_fields:
                if isinstance(timeseries_filter, dict):
                    ts_filter = timeseries_filter.get(n)
                else:
                    ts_filter = timeseries_filter

                if has_subsets:
                    subset_index = model._get_subset_idx(n)
                else:
                    subset_index = None

                selection[n] = model.get_filtered_field_value(
                    n, ts_filter=ts_filter, lookup_index=lookup_index,
                    subset_index=subset_index)

        # Inject timestamps automatically
        if hasattr(model, 'get_timestamps'):
            if getattr(model, 'is_aggregate', False):
                # Output one array of timestamps per field
                for n in model._field_names:
                    if not model.only_fields or n in model.only_fields:
                        field_name = '%s_%s' % (n, 'timestamps')
                        try:
                            selection[field_name] = model.get_timestamps(n)
                        except (AttributeError, TypeError):
                            selection[field_name] = np.array([])

            else:
                # Output one array with timestamps for all fields
                selection['timestamps'] = model.get_timestamps(
                    timeseries_filter)

        return selection

    def __init__(self, h5py_file, group_name, meta=None, required=False):
        self.group_name = group_name
        self._h5py_file = h5py_file

        if group_name not in list(h5py_file.keys()) and not required:
            logger.info(
                '[*] {0} not found in file {1}, not required...'.format(
                    group_name, h5py_file)
            )
            return

        try:
            self._source = h5py_file.require_group(group_name)
        except TypeError:
            self._source = h5py_file[group_name]

        self.meta = dict(
            [(y, [x[()]]) for y, x in self._h5py_file.get('meta').items()])
        self.meta['trash'] = [1]

    def set(self, name, values):
        if name in self._source:
            # Overwrite
            self._source[name][:] = values
        else:
            # Create
            self._source.create_dataset(name, data=values)

    def getattr(self, name):
        attr = self._h5py_file.attrs[name]
        if isinstance(attr, bytes):
            attr = attr.decode('utf-8')
        return attr

    def keys(self):
        if self._source is None:
            return []
        return list(self._source.keys())

    def has_any(self, sources):
        """
        Check if the any of the sources can be found in
        the file
        """
        return any(x in list(self.keys())
                   for x in sources)


class H5pyResultGroup(H5pyGroup):
    def __init__(self, h5py_file, group_name, netcdf_file,
                 meta=None, required=False):
        super(H5pyResultGroup, self).__init__(
            h5py_file, group_name, meta, required)
        self.netcdf_file = netcdf_file

        if isinstance(netcdf_file, H5SwmrFile):
            self.swmr_mode = True

    def keys(self):
        keys = list(super(H5pyResultGroup, self).keys())
        keys += list(self.netcdf_file.keys())
        return list(set(keys))

    def get(self, name):
        # meta is special
        if name == 'meta':
            return self.meta

        if name in self._source:
            return self._source.get(name)

        if name in self.netcdf_file.keys():
            return self.netcdf_file.get(name)

        return None

    def attr(self, var_name, attr_name):
        v = self.get(var_name)
        if v is None:
            return ''
        try:
            return v.attrs.get(attr_name)
        except AttributeError:
            pass
        return ''

    def __getitem__(self, name):
        # meta is special
        if name == 'meta':
            return self.meta

        if name in self._source:
            return self._source[name]

        if name in self.netcdf_file.keys():
            return self.netcdf_file.get(name)
