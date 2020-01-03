import numpy as np

from threedigrid.admin.h5py_datasource import H5pyGroup
from threedigrid.orm.base.datasource import DataSource
from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.levees.models import Levees
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.pumps.models import Pumps

try:
    from autobahn.asyncio import ApplicationSession
    from autobahn.asyncio.wamp import ApplicationRunner
    from autobahn.asyncio.component import Component, run  # noqa
    autobahn_support = True
except ImportError:
    autobahn_support = False


MODEL_KLASS_MAP = {
    'Breaches': Breaches,
    'Levees': Levees,
    'Lines': Lines,
    'Nodes': Nodes,
    'Pumps': Pumps
}


class WampBackendGroup(H5pyGroup):

    def __init__(self, h5py_file, group_name, meta=None, required=False):
        super().__init__(h5py_file, group_name, meta, required)

    def get_filtered_field_value(
            self, model, field_name, ts_filter=None, lookup_index=None,
            subset_index=None):
        klass = model.pop('klass')
        model_klass = MODEL_KLASS_MAP[klass]
        model = model_klass(datasource=self, **model)

        data = super().get_filtered_field_value(
            model, field_name, ts_filter, lookup_index, subset_index
        )
        return data.tolist()

    def execute_query(self, model):
        return super().execute_query(model)


class WampClientGroup(DataSource):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def get_filtered_field_value(
            self, model, field_name, ts_filter=None, lookup_index=None,
            subset_index=None):
        klass = type(model).__name__

        filters = None

        class_kwargs = model.class_kwargs
        class_kwargs['klass'] = klass

        res = await self.session.call(
            '%s.get_filtered_field_value' % klass, class_kwargs, field_name, ts_filter,
            lookup_index, subset_index)
        return np.array(res)

    async def execute_query(self, model):
        res = await self.session.call(
            'nodes.execute_query', model
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
