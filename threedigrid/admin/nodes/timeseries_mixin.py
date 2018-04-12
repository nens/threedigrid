from threedigrid.orm.base.timeseries_mixin import ResultMixin
from threedigrid.orm.base.fields import TimeSeriesArrayField
from threedigrid.orm.base.fields import TimeSeriesCompositeArrayField
# from threedigrid.admin.constants import AGGREGATION_OPTIONS
# from threedigrid.admin.constants import NODE_VARIABLES
# from threedigrid.admin.constants import NODE_MESH_VARS
from threedigrid.orm.constants import NODES_COMPOSITE_FIELDS
from threedigrid.admin.utils import combine_vars


class NodeResultsMixin(ResultMixin):

    def __init__(self, netcdf_keys, **kwargs):
        """Instantiate a node with netcdf results.

        Variables stored in the netcdf and related to nodes are dynamically
        added as attributes as TimeSeriesArrayField.

        :param netcdf_keys: list of netcdf variables
        :param kwargs:
        """
        super(NodeResultsMixin, self).__init__(**kwargs)
        # possible_node_mesh_vars = combine_vars(NODE_MESH_VARS, NODE_VARIABLES)
        # # # possible_vars = combine_vars(
        # # #     possible_node_mesh_vars, AGGREGATION_OPTIONS
        # # # )
        # # possible_vars += possible_node_mesh_vars
        # # variables = set(possible_vars).intersection(netcdf_keys)
        # variables = set(possible_node_mesh_vars).intersection(netcdf_keys)
        # for var in variables:
        #     setattr(self, var, MArrayField())
        #
        #
        # # To add result fields to the instance
        # self._field_names = variables.union(set(self.fields))
        # self.composit = NODE_COMPOSITE_FIELDS
        for var in NODES_COMPOSITE_FIELDS.keys():
            setattr(self, var, TimeSeriesCompositeArrayField())
        # remove private fields
        fnames = [x for x in NODES_COMPOSITE_FIELDS.keys()
                  if not x.startswith('_')]
        self._field_names = set(
            fnames).union(set(self.fields))
