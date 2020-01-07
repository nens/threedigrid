import numpy as np

from threedigrid.admin.h5py_datasource import H5pyGroup
from threedigrid.orm.base.datasource import DataSource
from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.levees.models import Levees
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.pumps.models import Pumps
from threedigrid.orm.base.filters import get_filter_from_dict

try:
    from autobahn.asyncio import ApplicationSession
    from autobahn.asyncio.wamp import ApplicationRunner
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


class WampBackendGroup(H5pyGroup):

    def __init__(self, h5py_file, group_name, meta=None, required=False):
        super().__init__(h5py_file, group_name, meta, required)

    def get_filtered_field_value(
            self,
            model,
            field_name,
            ts_filter=None,
            lookup_index=None,
            subset_index=None
    ):
        if type(model) == dict:
            klass = self.group_name
            model_klass = MODEL_KLASS_MAP[klass]
            filters = [get_filter_from_dict(f) for f in model.get('slice_filters')]
            model['slice_filters'] = filters
            model = model_klass(datasource=self, **model)

        data = super().get_filtered_field_value(
            model, field_name, ts_filter, lookup_index, subset_index
        )
        return data.tolist()

    def execute_query(self, model):
        if type(model) == dict:
            model_klass = MODEL_KLASS_MAP[self.group_name]
            filters = [get_filter_from_dict(f) for f in model.get('slice_filters')]
            model['slice_filters'] = filters

            model = model_klass(datasource=self, **model)

        data = super().execute_query(model)
        return data


class WampClientGroup(DataSource):

    def __init__(self, data_source, group_name):
        self.data_source = data_source
        self.group_name = group_name

    def serialize_model(self, class_kwargs):
        serialized_model = {**class_kwargs}
        slice_filters = serialized_model.get('slice_filters', [])
        slice_filters = [f.to_dict() for f in slice_filters]
        serialized_model['slice_filters'] = slice_filters
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


class WAMPFile:
    def __init__(self, session):
        self.session = session

    async def get(self, item):
        res = await self.session.call(
            'ga.__getattribute__', item
        )
        return res

    def keys(self):
        return ['nodes']
