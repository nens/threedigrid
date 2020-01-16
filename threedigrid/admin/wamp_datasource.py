import asyncio
import logging

import numpy as np

from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.breaches.timeseries_mixin import BreachesResultsMixin
from threedigrid.admin.h5py_datasource import H5pyGroup
from threedigrid.admin.levees.models import Levees
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.lines.timeseries_mixin import LinesResultsMixin
from threedigrid.admin.nodes.models import Nodes, Grid
from threedigrid.admin.nodes.timeseries_mixin import NodesResultsMixin
from threedigrid.admin.pumps.models import Pumps
from threedigrid.admin.pumps.timeseries_mixin import PumpsResultsMixin
from threedigrid.orm.base.datasource import DataSource
from threedigrid.orm.base.filters import get_filter_from_dict
from threedigrid.orm.base.timeseries_mixin import AggregateResultMixin

try:
    from autobahn.asyncio.component import Component, run  # noqa
    autobahn_support = True
except ImportError:
    autobahn_support = False

logger = logging.getLogger(__name__)

MODEL_KLASS_MAP = {
    'breaches': Breaches,
    'lines': Lines,
    'nodes': Nodes,
    'grid': Grid,
    'pumps': Pumps,
    'levees': Levees
}
RESULT_MIXIN_MAP = {
    'AggregateResultMixin': AggregateResultMixin,
    'BreachesResultsMixin': BreachesResultsMixin,
    'LinesResultsMixin': LinesResultsMixin,
    'NodesResultsMixin': NodesResultsMixin,
    'PumpsResultsMixin': PumpsResultsMixin
}


class ThreedigridWampComponent(Component):
    def __init__(self, gridadmin, transports, realm, allow_pubsub=False):
        super().__init__(transports=transports, realm=realm)
        self.ga = gridadmin
        self.allow_pubsub = allow_pubsub
        self.on_join(self.on_session_ready)
        self.last_observed_timestamp = None

    async def on_session_ready(self, session, details):
        await self.register_endpoints(session, details)
        if self.allow_pubsub:
            while True:
                self.ga.netcdf_file.refresh_datasets()
                last_timestamp = self.ga.nodes.timestamps[-1]
                if last_timestamp != self.last_observed_timestamp:
                    logger.info("new_data %s" % last_timestamp)
                    session.publish("new_data", last_timestamp)
                    self.last_observed_timestamp = last_timestamp
                await asyncio.sleep(1)

    def has_new_data(self):
        last_timestamp = self.ga.nodes.timestamps[-1]
        return last_timestamp != self.last_observed_timestamp

    async def register_endpoints(self, session, details):
        print("Backend session ready")
        session.register(
            self.ga.breaches._datasource.get_filtered_field_value,
            'breaches.get_filtered_field_value'
        )
        session.register(
            self.ga.breaches._datasource.execute_query,
            'breaches.execute_query'
        )
        session.register(
            self.ga.levees._datasource.get_filtered_field_value,
            'levees.get_filtered_field_value'
        )
        session.register(
            self.ga.levees._datasource.execute_query,
            'levees.execute_query'
        )
        session.register(
            self.ga.lines._datasource.get_filtered_field_value,
            'lines.get_filtered_field_value'
        )
        session.register(
            self.ga.lines._datasource.execute_query,
            'lines.execute_query'
        )
        session.register(
            self.ga.nodes._datasource.get_filtered_field_value,
            'nodes.get_filtered_field_value'
        )
        session.register(
            self.ga.nodes._datasource.execute_query,
            'nodes.execute_query'
        )
        session.register(
            self.ga.pumps._datasource.get_filtered_field_value,
            'pumps.get_filtered_field_value'
        )
        session.register(
            self.ga.pumps._datasource.execute_query,
            'pumps.execute_query'
        )
        session.register(
            self.ga.h5py_file.attrs.__getitem__,
            'ga.attrs.__getitem__'
        )
        session.register(
            self.ga.h5py_file.__getitem__,
            'ga.__getitem__'
        )
        if hasattr(self.ga, 'netcdf_file'):
            session.register(
                self.ga.netcdf_file.attrs.__getitem__,
                'gr.attrs.__getitem__'
            )
            # Needed for timestamps
            session.register(
                self.ga.netcdf_file.__getitem__,
                'gr.__getitem__'
            )


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
            model_kwargs['mixin'] = RESULT_MIXIN_MAP[mixin]

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
        super().__init__(data_source)
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
        logger.debug(
            "'%s.get_filtered_field_value', [%s, %s, %s, %s, %s]" %
            (self.group_name, serialized_model, field_name, ts_filter, lookup_index,
             subset_index)
        )
        res = await self.session.call(
            '%s.get_filtered_field_value' % self.group_name, serialized_model, field_name,
            ts_filter, lookup_index, subset_index
        )
        return np.array(res)

    async def execute_query(self, model):
        serialized_model = self.serialize_model(model.class_kwargs)
        logger.debug("'%s.execute_query', [%s]" % (self.group_name, serialized_model))
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
        super().__init__(netcdf_file, group_name)
        self.netcdf_file = netcdf_file

    def attr(self, var_name, attr_name):
        pass


class WAMPFile:
    def __init__(self, session, file_type='ga'):
        self.session = session
        self.file_type = file_type

    def __getitem__(self, item):
        return self.get(item)

    def get(self, item):
        logger.info("'%s.attrs.__getitem__', ['%s']" % (self.file_type, item))
        future = self.session.call(
            '%s.attrs.__getitem__' % self.file_type, item
        )
        return future

    def keys(self):
        return []

    @property
    def attrs(self):
        return self
