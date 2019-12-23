import re
from uuid import uuid4
from threedigrid.orm.base.datasource import DataSource

try:
    import asyncio_rpc # noqa
except ImportError:
    raise Exception(
        "asyncio_rpc needs to be installed when using this module,"
        "install it with: pip install asyncio_rpc")

from asyncio_rpc.models import RPCStack, RPCCall
from asyncio_rpc.client import RPCClient
from asyncio_rpc.commlayers.redis import RPCRedisCommLayer
from asyncio_rpc.serialization import msgpack


NAMESPACE = 'GRIDRESULTADMIN'
RESULT_EXPIRE_TIME = 30


class Results(object):
    def __init__(self, rpc_file, rpc_stack):
        self.rpc_file = rpc_file
        self.rpc_stack = rpc_stack

    async def resolve(self):
        """
        Resolve this future
        """
        client = await self.rpc_file.client
        return await client.rpc_call(self.rpc_stack)


class RPCAttrs:
    def __init__(self, rpc_file):
        self.rpc_file = rpc_file

    def get(self, key, *args, **kwargs):
        # Use nodes route for now
        stack = [
            RPCCall('nodes', [], {}),
            RPCCall('_datasource', [], {}),
            RPCCall('getattr', [key], {})
        ]

        rpc_stack = RPCStack(
            uuid4().hex, NAMESPACE, RESULT_EXPIRE_TIME, stack)
        return Results(self.rpc_file, rpc_stack)

    def __getitem__(self, key):
        """
        Get item from attrs
        """
        return self.get(key)


class RPCFile:
    def __init__(self, path, file_modus):
        match = re.match(r"rpc://(?P<host>\S+)/(?P<channel>\S+)", path)
        self._redis_host = 'localhost'
        self._redis_port = 6379

        if match:
            data = match.groupdict()
            self._redis_host = data['host']
            self.pubchannel = data['channel']
        else:
            raise Exception(
                "Could not parse path %s" % path)

        self.path = path
        self.file_modus = file_modus
        self._client = None

    @property
    async def client(self):
        if self._client is None:
            subchannel = uuid4().hex
            comm = await RPCRedisCommLayer.create(
                subchannel, self.pubchannel,
                host=self._redis_host,
                port=self._redis_port,
                serialization=msgpack)
            self._client = RPCClient(comm)
        return self._client

    def get_model_extent(self, target_epsg_code='', bbox=[]):
        stack = [
            RPCCall('get_model_extent', [],
                    {'target_epsg_code': target_epsg_code,
                     'bbox': bbox}),
        ]
        rpc_stack = RPCStack(
            uuid4().hex, NAMESPACE, RESULT_EXPIRE_TIME, stack)
        return Results(self, rpc_stack)

    def get_extent_subset(self, subset_name, target_espg_code=''):
        stack = [
            RPCCall('get_extent_subset', [subset_name],
                    {'target_espg_code': target_espg_code}),
        ]
        rpc_stack = RPCStack(
            uuid4().hex, NAMESPACE, RESULT_EXPIRE_TIME, stack)
        return Results(self, rpc_stack)

    def __getitem__(self, key):
        if key == 'meta':
            return self.meta
        else:
            raise Exception("Only [meta] is implemented")

    @property
    def meta(self):
        # Use nodes route for now
        stack = [
            RPCCall('nodes', [], {}),
            RPCCall('_datasource', [], {}),
            RPCCall('getattr', ['meta'], {})
        ]

        rpc_stack = RPCStack(
            uuid4().hex, NAMESPACE, RESULT_EXPIRE_TIME, stack)
        return Results(self, rpc_stack)

    @property
    def attrs(self):
        return RPCAttrs(self)


class H5RPCGroup(DataSource):
    """
    Datasource wrapper for h5py groups,
    adding meta data to all groups.
    """
    def __init__(self, rpc_file, group_name, meta=None, required=False):
        self.rpc_file = rpc_file
        self.group_name = group_name

    def get_rpc_actions(self, model, field_name=None):
        rpc_actions = []
        if model.reproject_to_epsg:
            rpc_actions.append(
                {'reproject_to': model.reproject_to_epsg}
            )
        rpc_actions += [
            x.to_dict() for x in model.slice_filters if not x._filter_as]

        if field_name is None:
            if model.only_fields:
                rpc_actions.append(
                    {'only': model.only_fields}
                )
            rpc_actions.append(
                {'data': {}}
            )
        else:
            rpc_actions.append(
                {field_name: {}})

        return rpc_actions

    def get_asyncio_rpc_stack(self, model, rpc_actions):
        stack = [
            RPCCall(self.group_name, [], {})
        ]

        model_name = model.__class__.__name__.lower()
        if model_name != self.group_name:
            stack.append(
                RPCCall(model_name, [], {})
            )

        for action in rpc_actions:
            for key, value in action.items():
                if isinstance(value, list):
                    stack.append(
                        RPCCall(key, value, {})
                    )
                elif isinstance(value, dict):
                    stack.append(
                        RPCCall(key, [], value)
                    )
                else:
                    stack.append(
                        RPCCall(key, [value], {})
                    )

        return RPCStack(
            uuid4().hex, NAMESPACE, RESULT_EXPIRE_TIME, stack)

    def get_filtered_field_value(
            self, model, field_name, ts_filter=None, lookup_index=None,
            subset_index=None):
        rpc_actions = self.get_rpc_actions(
            model, field_name=field_name)
        rpc_stack = self.get_asyncio_rpc_stack(model, rpc_actions)

        return Results(self.rpc_file, rpc_stack)

    def execute_query(self, model):
        rpc_actions = self.get_rpc_actions(model)
        rpc_stack = self.get_asyncio_rpc_stack(model, rpc_actions)

        return Results(self.rpc_file, rpc_stack)

    def set(self, name, values):
        pass

    def getattr(self, name):
        stack = [
            RPCCall(self.group_name, [], {}),
            RPCCall('_datasource', [], {}),
            RPCCall('getattr', [name], {})
        ]

        rpc_stack = RPCStack(
            uuid4().hex, NAMESPACE, RESULT_EXPIRE_TIME, stack)
        return Results(self.rpc_file, rpc_stack)

    def keys(self):
        return []
