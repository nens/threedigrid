import numpy as np

from threedigrid.admin.h5py_datasource import H5pyGroup
from threedigrid.admin.nodes.timeseries_mixin import NodesResultsMixin
from threedigrid.orm.base.datasource import DataSource
from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.levees.models import Levees
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.pumps.models import Pumps
from threedigrid.orm.base.filters import get_filter_from_dict

try:
    from autobahn.asyncio.component import Component, run  # noqa
    autobahn_support = True
except ImportError:
    autobahn_support = False


MODEL_KLASS_MAP = {
    'breaches': Breaches,
    'levees': Levees,
    'lines': Lines,
    'nodes': Nodes,
    'pumps': Pumps
}

MIXIN_MAP = {
    'NodesResultsMixin': NodesResultsMixin
}


class WampBackendGroup(H5pyGroup):

    def __init__(self, h5py_file, group_name, meta=None, required=False):
        super().__init__(h5py_file, group_name, meta, required)

    def deserialize_model(self, model):
        model_klass = MODEL_KLASS_MAP[self.group_name]
        model_kwargs = {**model}

        # Serialize slice_filters:
        filters = [get_filter_from_dict(f) for f in model.get('slice_filters')]
        model_kwargs['slice_filters'] = filters

        # serialize mixin:
        mixin = model_kwargs.get('mixin')
        if mixin:
            model_kwargs['mixin'] = MIXIN_MAP[mixin]

        # timeseries_chunk_size
        timeseries_chunk_size = model_kwargs.get('timeseries_chunk_size')
        if timeseries_chunk_size:
            model_kwargs['timeseries_chunk_size'] = slice(
                timeseries_chunk_size['start'],
                timeseries_chunk_size['stop'],
                timeseries_chunk_size['step']
            )

        return model_klass(datasource=self, **model_kwargs)

    def get_filtered_field_value(
            self,
            model,
            field_name,
            ts_filter=None,
            lookup_index=None,
            subset_index=None
    ):
        if type(model) == dict:
            model = self.deserialize_model(model)

        data = super().get_filtered_field_value(
            model, field_name, ts_filter, lookup_index, subset_index
        )
        return data.tolist()

    def execute_query(self, model):
        if type(model) == dict:
            model = self.deserialize_model(model)

        data = super().execute_query(model)
        if 'timestamps' in data:
            data['timestamps'] = data['timestamps'].tolist()
        return data


class WampBackendResultGroup(WampBackendGroup):

    def __init__(self, h5py_file, group_name, netcdf_file, meta=None, required=False):
        super().__init__(h5py_file, group_name, meta, required)
        self.netcdf_file = netcdf_file

    def keys(self):
        keys = list(super().keys())
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


class WampClientGroup(DataSource):

    def __init__(self, data_source, group_name):
        self.data_source = data_source
        self.group_name = group_name

    def serialize_model(self, class_kwargs):
        serialized_model = {**class_kwargs}

        # Serialize slice_filters:
        slice_filters = serialized_model.get('slice_filters', [])
        slice_filters = [f.to_dict() for f in slice_filters]
        serialized_model['slice_filters'] = slice_filters

        # serialize mixin:
        mixin = serialized_model.get('mixin')
        if mixin:
            serialized_model['mixin'] = mixin.__name__

        # timeseries_chunk_size
        timeseries_chunk_size = serialized_model.get('timeseries_chunk_size')
        if timeseries_chunk_size:
            serialized_model['timeseries_chunk_size'] = {
                'start': timeseries_chunk_size.start,
                'stop': timeseries_chunk_size.stop,
                'step': timeseries_chunk_size.step
            }

        return serialized_model

    async def get_filtered_field_value(
            self,
            model,
            field_name,
            ts_filter=None,
            lookup_index=None,
            subset_index=None
    ):
        serialized_model = self.serialize_model(model.class_kwargs)
        res = await self.session.call(
            '%s.get_filtered_field_value' % self.group_name, serialized_model, field_name,
            ts_filter, lookup_index, subset_index
        )
        return np.array(res)

    async def execute_query(self, model):
        serialized_model = self.serialize_model(model.class_kwargs)
        res = await self.session.call(
            '%s.execute_query' % self.group_name, serialized_model
        )
        return res

    def keys(self):
        return []

    def has_any(self, sources):
        return True



class WampClientResultGroup(WampClientGroup):

    def __init__(self, data_source, group_name, netcdf_file):
        self.data_source = data_source
        self.group_name = group_name
        self.netcdf_file = netcdf_file

    def attr(self, var_name, attr_name):
        pass
        # res = await self.session.call(
        #     '%s.attr' % self.group_name, var_name, attr_name
        # )
        # return res



class WAMPFile:
    def __init__(self, session):
        self.session = session

    async def get(self, item):
        res = await self.session.call(
            'ga.__getattribute__', item
        )
        return res

    def keys(self):
        return []
