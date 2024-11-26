# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.


import logging
import re
from collections import defaultdict
from typing import List, Optional, Union

import h5py
import numpy as np

from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.breaches.timeseries_mixin import (
    BreachesAggregateResultsMixin,
    BreachesResultsMixin,
    get_breaches_customized_result_mixin,
)
from threedigrid.admin.constants import DEFAULT_CHUNK_TIMESERIES
from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.h5py_datasource import H5pyResultGroup
from threedigrid.admin.h5py_swmr import H5SwmrFile
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.lines.timeseries_mixin import (
    get_lines_customized_result_mixin,
    LinesAggregateResultsMixin,
    LinesResultsMixin,
)
from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.nodes.timeseries_mixin import (
    get_nodes_customized_results_mixin,
    get_nodes_customized_water_quality_results_mixin,
    get_substance_result_mixin,
    NodesAggregateResultsMixin,
    NodesResultsMixin,
)
from threedigrid.admin.pumps.models import Pumps
from threedigrid.admin.pumps.timeseries_mixin import (
    get_pumps_customized_result_mixin,
    PumpsAggregateResultsMixin,
    PumpsResultsMixin,
)
from threedigrid.admin.structure_controls.models import (
    StructureControl,
    StructureControlSourceTypes,
    StructureControlTypes,
)
from threedigrid.orm.models import Model

logger = logging.getLogger(__name__)

try:
    import asyncio_rpc  # noqa

    asyncio_rpc_support = True
except ImportError:
    asyncio_rpc_support = False


class GridH5ResultAdmin(GridH5Admin):
    """
    Admin interface for threedicore result queries.
    """

    def __init__(self, h5_file_path, netcdf_file_path, file_modus="r", swmr=False):
        """

        :param h5_file_path: path to the hdf5 gridadmin file
        :param netcdf_file_path: path to the netcdf result file (usually
            called subgrid_map.nc)
        :param file_modus: modus in which to open the files
        """
        self._field_model_dict = defaultdict(list)
        self._netcdf_file_path = str(netcdf_file_path)
        super().__init__(str(h5_file_path), file_modus)

        self.result_datasource_class = H5pyResultGroup

        if h5_file_path.startswith("rpc://"):
            if not asyncio_rpc_support:
                raise Exception("Please reinstall this package with threedigrid[rpc]")

            from threedigrid.admin.rpc_datasource import H5RPCResultGroup, RPCFile

            self.netcdf_file = RPCFile(h5_file_path, file_modus)
            self.result_datasource_class = H5RPCResultGroup
        else:
            if swmr:
                self.netcdf_file = H5SwmrFile(netcdf_file_path, file_modus)
            else:
                self.netcdf_file = h5py.File(netcdf_file_path, file_modus)
            self.version_check()
        self.set_timeseries_chunk_size(DEFAULT_CHUNK_TIMESERIES.stop)

    def set_timeseries_chunk_size(self, new_chunk_size):
        """
        overwrite the default chunk size for timeseries queries.
        :param new_chunk_size <int>: new chunk size for
            timeseries queries
        :raises ValueError when the given value is less than 1
        """
        _chunk_size = int(new_chunk_size)
        if _chunk_size < 1:
            raise ValueError("Chunk size must be greater than 0")
        self._timeseries_chunk_size = slice(0, _chunk_size)
        logger.info("New chunk for timeseries size has been set to %d", new_chunk_size)
        self._grid_kwargs.update({"timeseries_chunk_size": self._timeseries_chunk_size})

    @property
    def timeseries_chunk_size(self):
        return self._timeseries_chunk_size.stop

    @property
    def time_units(self):
        return self.netcdf_file["time"].attrs.get("units")

    @property
    def lines(self):
        return Lines(
            self.result_datasource_class(self.h5py_file, "lines", self.netcdf_file),
            **dict(self._grid_kwargs, **{"mixin": LinesResultsMixin}),
        )

    @property
    def nodes(self):
        return Nodes(
            self.result_datasource_class(self.h5py_file, "nodes", self.netcdf_file),
            **dict(self._grid_kwargs, **{"mixin": NodesResultsMixin}),
        )

    @property
    def breaches(self):
        if not self.has_breaches:
            logger.info("Threedimodel has no breaches")
            return
        return Breaches(
            self.result_datasource_class(self.h5py_file, "breaches", self.netcdf_file),
            **dict(self._grid_kwargs, **{"mixin": BreachesResultsMixin}),
        )

    @property
    def pumps(self):
        if not self.has_pumpstations:
            logger.info("Threedimodel has no pumps")
            return
        return Pumps(
            self.result_datasource_class(self.h5py_file, "pumps", self.netcdf_file),
            **dict(self._grid_kwargs, **{"mixin": PumpsResultsMixin}),
        )

    def version_check(self):
        """
        compare versions of grid admin and grid results file.
        Issues a warning if they differ
        """
        return  # TODO implement a different check

        if self.threedicore_result_version != self.threedicore_version:
            logger.warning(
                "[!] threedicore version differ! \n"
                "Version result file has been created with: %s\n"
                "Version gridadmin file has been created with: %s",
                self.threedicore_result_version,
                self.threedicore_version,
            )

    @property
    def _field_model_map(self):
        """
        :return: a dict of {<field name>: [model name, ...]}
        """
        if self._field_model_dict:
            return self._field_model_dict

        model_names = set()
        for attr_name in dir(self):
            # skip private attrs
            if any([attr_name.startswith("__"), attr_name.startswith("_")]):
                continue
            try:
                attr = getattr(self, attr_name)
            except AttributeError:
                logger.warning(
                    "Attribute: '{}' does not " "exist in h5py_file.".format(attr_name)
                )
                continue
            if not issubclass(type(attr), Model):
                continue
            model_names.add(attr_name)

        for model_name in model_names:
            for x in getattr(self, model_name)._field_names:
                self._field_model_dict[x].append(model_name)
        return self._field_model_dict

    def get_model_instance_by_field_name(self, field_name):
        """
        :param field_name: name of a models field
        :return: instance of the model the field belongs to
        :raises IndexError if the field name is not unique across models
        """
        model_name = self._field_model_map.get(field_name)
        if not model_name or len(model_name) != 1:
            raise IndexError(
                "Ambiguous result. Field name {} yields {} model(s)".format(
                    field_name, len(model_name) if model_name else 0
                )
            )
        return getattr(self, model_name[0])

    @property
    def threedicore_result_version(self):
        """
        :return: version of the grid result file (if found), an empty
        string otherwise
        """
        try:
            return self.netcdf_file.attrs.get("threedicore_version")
        except AttributeError:
            logger.error(
                "Attribute threedicore_version could not be found in result file"
            )  # noqa
        return ""

    def close(self):
        super().close()
        self.netcdf_file.close()


class GridH5AggregateResultAdmin(GridH5ResultAdmin):
    """
    Admin interface for threedicore result queries.
    """

    def __init__(self, h5_file_path, netcdf_file_path, file_modus="r"):
        """

        :param h5_file_path: path to the hdf5 gridadmin file
        :param netcdf_file_path: path to the netcdf result file (usually
            called subgrid_map.nc)
        :param file_modus: modus in which to open the files
        """
        super().__init__(h5_file_path, netcdf_file_path, file_modus)

    @property
    def lines(self):
        model_name = "lines"
        return Lines(
            H5pyResultGroup(self.h5py_file, model_name, self.netcdf_file),
            **dict(self._grid_kwargs, **{"mixin": LinesAggregateResultsMixin}),
        )

    @property
    def nodes(self):
        return Nodes(
            H5pyResultGroup(self.h5py_file, "nodes", self.netcdf_file),
            **dict(self._grid_kwargs, **{"mixin": NodesAggregateResultsMixin}),
        )

    @property
    def breaches(self):
        if not self.has_breaches:
            logger.info("Threedimodel has no breaches")
            return
        model_name = "breaches"
        return Breaches(
            H5pyResultGroup(self.h5py_file, model_name, self.netcdf_file),
            **dict(self._grid_kwargs, **{"mixin": BreachesAggregateResultsMixin}),
        )

    @property
    def pumps(self):
        if not self.has_pumpstations:
            logger.info("Threedimodel has no pumps")
            return
        model_name = "pumps"
        return Pumps(
            H5pyResultGroup(self.h5py_file, model_name, self.netcdf_file),
            **dict(self._grid_kwargs, **{"mixin": PumpsAggregateResultsMixin}),
        )

    @property
    def time_units(self):
        logger.info("Time units are not defined globally for aggregated results")
        return None

    def close(self) -> None:
        super().close()
        self.netcdf_file.close()


class GridH5StructureControl(GridH5Admin):
    """Interface for structure control netcdf

    This interface is different from the GridH5ResultAdmin and
    GridH5AggregateResultAdmin, as it resembles less the Nodes and Lines data compared
    to those interfaces. This interface should be viewed as a CSV file interface
    which can be used to extract the different control structures by control type and
    output data. It supplies interfaces to Nodes, Lines, Weirs, etc but does not
    provide the same timeseries filter capabilities as the GridH5ResultAdmin and
    GridH5AggregateResultAdmin.

        >>> gst = GridH5StructureControl(gridadmin_path, struct_control_actions_3di.nc)
        >>> gst.table_control
        >>> gst.timed_control
        >>> gst.memory_control
        >>> gst.table_control.id
        >>> struct_control = gst.table_control.group_by_id(ga.table_control.id[0])
        >>> struct_control.time
        >>> struct_control.action_value_1
    """

    def __init__(
        self,
        h5_file_path: str,
        netcdf_file_path: str,
        file_modus: str = "r",
        swmr: bool = False,
    ):
        """
        :param h5_file_path: path to the hdf5 gridadmin file
        :param netcdf_file_path: path to the netcdf structure control result file
            (usually structure_control_actions_3di.nc)
        :param file_modus: modus in which to open the files
        """
        self._netcdf_file_path: str = netcdf_file_path
        super().__init__(h5_file_path, file_modus)

        if swmr:
            self.netcdf_file = H5SwmrFile(netcdf_file_path, file_modus)
        else:
            self.netcdf_file = h5py.File(netcdf_file_path, file_modus)

    @property
    def table_control(self) -> "_GridH5NestedStructureControl":
        """Get the table control actions as ``_GridH5NestedStructureControl`` object"""
        return _GridH5NestedStructureControl(self, StructureControlTypes.table_control)

    @property
    def memory_control(self) -> "_GridH5NestedStructureControl":
        """Get the memory control actions as ``_GridH5NestedStructureControl`` object"""
        return _GridH5NestedStructureControl(self, StructureControlTypes.memory_control)

    @property
    def timed_control(self) -> "_GridH5NestedStructureControl":
        """Get the timed control actions as ``_GridH5NestedStructureControl`` object"""
        return _GridH5NestedStructureControl(self, StructureControlTypes.timed_control)

    def get_source_table(self, action_type, grid_id):
        """Get source_table and source_table_id based on action_type and grid_id"""
        if action_type == "set_pump_capacity":
            source_table = "v2_pumpstation"
            source_table_id = grid_id
        else:
            source_table = self.lines.content_type[grid_id].decode("utf-8")
            source_table_id = self.lines.content_pk[grid_id]

        return source_table, source_table_id

    def get_source_type(self, action_type):
        """Indicates whether the action is applied on a line, pump (or node) feature"""
        if action_type == "set_pump_capacity":
            return StructureControlSourceTypes.PUMPS
        elif action_type in [
            "set_discharge_coefficients",
            "set_crest_level",
            "set_gate_level",
        ]:
            return StructureControlSourceTypes.LINES
        else:
            raise NotImplementedError


class _GridH5NestedStructureControl:
    def __init__(
        self,
        structure_control: GridH5StructureControl,
        control_type: StructureControlTypes,
    ):
        """
        This class is not to be instantiated seperately.
        Calling the ``GridH5StructureControl`` properties ``table_control``, ``memory_control``,
        or ``timed_control`` returns a ``_GridH5NestedStructureControl`` instance.

        :param structure_control: GridH5StructureControl(GridH5ResultAdmin)
        :param control_type: str [table_control, memory_control, timed_control]
        :param h5_file_path: path to the hdf5 gridadmin file
        :param netcdf_file_path: path to the netcdf structure control result file
            (usually structure_control_actions_3di.nc)
        :param file_modus: modus in which to open the files
        """
        if control_type not in StructureControlTypes.__members__.values():
            raise ValueError(f"Unknown control type: {control_type}")

        self.struct_control = structure_control
        self.control_type: str = control_type.value

    @property
    def action_type(self) -> np.ndarray:
        """Get the action types"""
        # binary character arrays from Netcdf Fortran to numpy object arrays
        return np.array(
            [
                action_type.tobytes().decode("utf-8").strip()
                for action_type in self.struct_control.netcdf_file[
                    f"{self.control_type}_action_type"
                ][:]
            ],
            dtype=object,
        )

    @property
    def action_value_1(self) -> np.ndarray:
        """Get the action values"""
        return self.struct_control.netcdf_file[f"{self.control_type}_action_value_1"][:]

    @property
    def action_value_2(self) -> np.ndarray:
        """Get the second action values (negative discharge for ``action_type == 'set_discharge_coefficients'``)"""
        return self.struct_control.netcdf_file[f"{self.control_type}_action_value_2"][:]

    @property
    def grid_id(self) -> np.ndarray:
        """Get the grid ID's, i.e. the ID of the Node or Line upon which the structure control action acts"""
        return self.struct_control.netcdf_file[f"{self.control_type}_grid_id"][:]

    @property
    def id(self) -> np.ndarray:
        """Get the ID's of the structure control action"""
        # binary character arrays from Netcdf Fortran to numpy object arrays"
        return np.array(
            [
                id.tobytes().decode("utf-8").strip()
                for id in self.struct_control.netcdf_file[f"{self.control_type}_id"][:]
            ],
            dtype=object,
        )

    @property
    def is_active(self) -> np.ndarray:
        """Get the boolean values indicating if the structure control action is active"""
        return self.struct_control.netcdf_file[f"{self.control_type}_is_active"][:]

    @property
    def time(self) -> np.ndarray:
        """Get the times (in s since start of simulation) at which the structure controls acted"""
        return self.struct_control.netcdf_file[f"{self.control_type}_time"][:]

    def group_by_id(self, id: str) -> Optional[StructureControl]:
        """
        Get the structure control action with given ``id``.

        ID is unique. Get content_type and content_pk from gridadmin. All controls are
        on lines except set_pump_capacity
        """
        mask = np.isin(self.id, id)
        if np.all(~mask):
            return

        grid_id = self.grid_id[mask][0]
        action_type = self.action_type[mask][0]
        source_table, source_table_id = self.struct_control.get_source_table(
            action_type, grid_id
        )
        source_type = self.struct_control.get_source_type(action_type)

        return StructureControl(
            id=id,
            grid_id=grid_id,
            source_table=source_table,
            source_table_id=source_table_id,
            source_type=source_type,
            time=self.time[mask],
            action_type=action_type,
            action_value_1=self.action_value_1[mask],
            action_value_2=self.action_value_2[mask],
            is_active=self.is_active[mask],
        )

    def group_by_grid_id(self, value: int) -> List[StructureControl]:
        """
        Get all structure control actions with ``grid_id == value``
        """
        return self._group_by("grid_id", value)

    def group_by_action_type(self, value: str) -> List[StructureControl]:
        """
        Get all structure control actions with ``action_type == value``
        """
        return self._group_by("action_type", value)

    def group_by_is_active(self, value: int) -> List[StructureControl]:
        """
        Get all structure control actions with ``is_active == value``
        """
        return self._group_by("is_active", value)

    def group_by_time(self, min: float, max: float) -> List[StructureControl]:
        """Get all structure control actions where ``min <= time <= max``"""
        return self._group_by_in_between("time", min, max)

    def group_by_action_value_1(self, min: float, max: float) -> List[StructureControl]:
        """Get all structure control actions where ``min <= action_value_1 <= max``"""
        return self._group_by_in_between("action_value_1", min, max)

    def group_by_action_value_2(self, min: float, max: float) -> List[StructureControl]:
        """Get all structure control actions where ``min <= action_value_2 <= max``"""
        return self._group_by_in_between("action_value_2", min, max)

    def _group_by(
        self, type: str, value: Union[int, float, str]
    ) -> List[StructureControl]:
        """Group control action by a type, and sort them by unique id

        Args:
            type (str): is_active, action_type, id
            value (Union[int, float, str]): corresponding value for type

        Returns:
            List[StructureControl]: unique structures found from type, value combination
        """
        if not hasattr(self, type):
            return []

        values = getattr(self, type)
        mask = np.isin(values, value)
        ids = np.unique(self.id[mask])
        return [self.group_by_id(id) for id in ids]

    def _group_by_in_between(
        self, type: str, min: Union[int, float], max: Union[int, float]
    ) -> List[StructureControl]:
        """Find values between min and max

        Args:
            type (str): time, action_value_1, action_value_2
            value (Union[int, float, str]): corresponding value for type

        Returns:
            List[StructureControl]: unique structures found from type, value combination
        """
        if not hasattr(self, type):
            return []

        values = getattr(self, type)
        mask = (values >= min) & (values <= max)
        ids = np.unique(self.id[mask])
        return [self.group_by_id(id) for id in ids]


class GridH5WaterQualityResultAdmin(GridH5Admin):
    def __init__(
        self,
        h5_file_path: str,
        netcdf_file_path: str,
        file_modus: str = "r",
        swmr: bool = False,
        substances: List[str] = [],
    ) -> None:
        """
        :param h5_file_path: path to the hdf5 gridadmin file
        :param netcdf_file_path: path to the water quality result file
            (usually structure_control_actions_3di.nc)
        :param file_modus: modus in which to open the files
        """
        self._netcdf_file_path: str = netcdf_file_path
        super().__init__(h5_file_path, file_modus)

        if swmr:
            self.netcdf_file = H5SwmrFile(netcdf_file_path, file_modus)
        else:
            self.netcdf_file = h5py.File(netcdf_file_path, file_modus)

        self.set_timeseries_chunk_size(DEFAULT_CHUNK_TIMESERIES.stop)

        # Set substances as attributes
        substances = set()
        for key in self.netcdf_file.keys():
            regex_match = re.search(r"substance\d+", key)
            if regex_match:
                substance = regex_match.group()
                if substance not in substances:
                    substances.add(substance)
                    self.__setattr__(
                        substance,
                        Nodes(
                            H5pyResultGroup(self.h5py_file, "nodes", self.netcdf_file),
                            **dict(
                                self._grid_kwargs,
                                **{"mixin": get_substance_result_mixin(substance)},
                            ),
                        ),
                    )

                    # Set substance attributes on Nodes object
                    attrs_map = [("name", "substance_name"), ("units", "units")]
                    for attr, name in attrs_map:
                        value = self.netcdf_file[key].attrs.get(name)
                        if isinstance(value, bytes):
                            value = value.decode("utf-8")
                        elif isinstance(value, h5py.Empty):
                            value = ""
                        self.__getattribute__(substance).__setattr__(attr, value)
        self.substances = list(substances)

    def get_model_instance_by_field_name(self, field_name):
        """
        :param field_name: name of a models field
        :return: instance of the model the field belongs to
        :raises AttributeError if the model instance cannot be found
        """
        try:
            model_instance = self.__getattribute__(field_name)
            return model_instance
        except AttributeError:
            raise AttributeError(
                f"Model instance with field name {field_name} not found"
            )

    def set_timeseries_chunk_size(self, new_chunk_size: int) -> None:
        """
        overwrite the default chunk size for timeseries queries.
        :param new_chunk_size <int>: new chunk size for
            timeseries queries
        :raises ValueError when the given value is less than 1
        """
        _chunk_size = int(new_chunk_size)
        if _chunk_size < 1:
            raise ValueError("Chunk size must be greater than 0")
        self._timeseries_chunk_size = slice(0, _chunk_size)
        logger.info("New chunk for timeseries size has been set to %d", new_chunk_size)
        self._grid_kwargs.update({"timeseries_chunk_size": self._timeseries_chunk_size})

    def close(self) -> None:
        super().close()
        self.netcdf_file.close()


class CustomizedResultAdmin(GridH5Admin):
    """Interface for customized 3Di result files

    Customized 3Di result files are result files where users can specify nodes, lines,
    and pumps of interest, combined with specific output variables and intervals.
    This interface can be used to extract data from customized result files. It
    contains functions to extract data from nodes, lines, breaches, and pumps.
    Additionally, it can be used to extract data from the result area of interest.

        >>> cra = CustomizedResultAdmin(gridadmin_path, customized_results_3di.nc)
        >>> cra.nodes.id
        >>> cra.lines.id
        >>> cra.area1.nodes.subset("1D_ALL").id
        >>> cra.area1.lines.subset("2D_ALL").s1
        >>> cra.area1.breaches.id
        >>> cra.area2.pumps.id
    """

    def __init__(
        self,
        h5_file_path: str,
        netcdf_file_path: str,
        file_modus: str = "r",
        swmr: bool = False,
    ) -> None:
        """
        :param h5_file_path: path to the hdf5 gridadmin file
        :param netcdf_file_path: path to the water quality result file
            (usually structure_control_actions_3di.nc)
        :param file_modus: modus in which to open the files
        """
        super().__init__(h5_file_path, file_modus)

        self._netcdf_file_path: str = netcdf_file_path
        if swmr:
            self.netcdf_file = H5SwmrFile(netcdf_file_path, file_modus)
        else:
            self.netcdf_file = h5py.File(netcdf_file_path, file_modus)

        self.set_timeseries_chunk_size(DEFAULT_CHUNK_TIMESERIES.stop)
        self.netcdf_keys = self.netcdf_file.keys()

        self.areas = []
        for key in self.netcdf_keys:
            regex_match = re.search(r"Mesh(1|2)D(Node|Line|Pump)_id_area\d+", key)
            if regex_match:
                # Set area as attribute and create area result admin
                dataset_name = regex_match.group().split("_")[-1]
                area_name = self.netcdf_file[key].attrs.get("area_name", dataset_name)
                if not hasattr(self, dataset_name):
                    self.areas += [dataset_name]
                    self.__setattr__(
                        dataset_name,
                        _CustomizedAreaResultAdmin(self, dataset_name, area_name),
                    )

    def close(self) -> None:
        super().close()
        self.netcdf_file.close()

    @property
    def nodes(self):
        """Build nodes interface if there are nodes present in the result file."""
        if not hasattr(self, "_nodes"):
            self._nodes = self._build_nodes_result_group("")
        return self._nodes

    @property
    def lines(self):
        """Build lines interface if there are lines present in the result file."""
        if not hasattr(self, "_lines"):
            self._lines = self._build_lines_result_group("")
        return self._lines

    @property
    def breaches(self):
        if not hasattr(self, "_breaches"):
            if not self.has_breaches:
                self._breaches = None
            else:
                self._breaches = self._build_breaches_result_group("")

        if self._breaches is None:
            logger.info("Threedimodel has no breaches")

        return self._breaches

    @property
    def pumps(self):
        if not hasattr(self, "_pumps"):
            if not self.has_pumpstations:
                self._pumps = None
            else:
                self._pumps = self._build_pumps_result_group("")

        if self._pumps is None:
            logger.info("Threedimodel has no pumps")

        return self._pumps

    @property
    def levees(self):
        return None

    @property
    def nodes_embedded(self):
        return None

    @property
    def cross_sections(self):
        return None

    @property
    def cells(self):
        return None

    def _build_nodes_result_group(self, area: str) -> Optional[Nodes]:
        size = self.result_group_size(f"nMesh2D_nodes{area}", f"nMesh1D_nodes{area}")
        if size == 0:
            return None

        return Nodes(
            H5pyResultGroup(self.h5py_file, "nodes", self.netcdf_file),
            **dict(
                self._grid_kwargs,
                **{"mixin": get_nodes_customized_results_mixin(self.netcdf_keys, area)},
            ),
        )

    def _build_lines_result_group(self, area: str) -> Optional[Lines]:
        size = self.result_group_size(f"nMesh2D_lines{area}", f"nMesh1D_lines{area}")
        if size == 0:
            return None

        return Lines(
            H5pyResultGroup(self.h5py_file, "lines", self.netcdf_file),
            **dict(
                self._grid_kwargs,
                **{
                    "mixin": get_lines_customized_result_mixin(
                        self.netcdf_keys,
                        area,
                    )
                },
            ),
        )

    def _build_breaches_result_group(self, area: str) -> Breaches:
        return Breaches(
            H5pyResultGroup(self.h5py_file, "breaches", self.netcdf_file),
            **dict(
                self._grid_kwargs,
                **{
                    "mixin": get_breaches_customized_result_mixin(
                        self.netcdf_keys,
                        area,
                    )
                },
            ),
        )

    def _build_pumps_result_group(self, area: str) -> Pumps:
        return Pumps(
            H5pyResultGroup(self.h5py_file, "pumps", self.netcdf_file),
            **dict(
                self._grid_kwargs,
                **{
                    "mixin": get_pumps_customized_result_mixin(
                        self.netcdf_keys,
                        area,
                    ),
                },
            ),
        )

    def result_group_size(self, field_name_2d: str, field_name_1d) -> np.ndarray:
        two_d_size = self.netcdf_file.get(field_name_2d, np.array([])).size
        one_d_size = self.netcdf_file.get(field_name_1d, np.array([])).size
        return two_d_size + one_d_size

    def set_timeseries_chunk_size(self, new_chunk_size):
        """overwrite the default chunk size for timeseries queries"""
        _chunk_size = int(new_chunk_size)
        if _chunk_size < 1:
            raise ValueError("Chunk size must be greater than 0")
        self._timeseries_chunk_size = slice(0, _chunk_size)
        logger.info("New chunk for timeseries size has been set to %d", new_chunk_size)
        self._grid_kwargs.update({"timeseries_chunk_size": self._timeseries_chunk_size})


class _CustomizedAreaResultAdmin:
    """Nested class for customized 3Di result files to interact with specific areas"""

    def __init__(
        self,
        customized_result_admin: CustomizedResultAdmin,
        dataset_name: str,
        area_name: str,
    ) -> None:
        self.cra = customized_result_admin
        self.dataset_name = dataset_name
        self.name = area_name
        self._timeseries_chunk_size = customized_result_admin._timeseries_chunk_size
        self._grid_kwargs = customized_result_admin._grid_kwargs

    @property
    def nodes(self):
        """Build nodes interface if there are nodes present in the result file."""
        if not hasattr(self, "_nodes"):
            self._nodes = self.cra._build_nodes_result_group(f"_{self.dataset_name}")
        return self._nodes

    @property
    def lines(self):
        """Build lines interface if there are lines present in the result file."""
        if not hasattr(self, "_lines"):
            self._lines = self.cra._build_lines_result_group(f"_{self.dataset_name}")
        return self._lines

    @property
    def breaches(self):
        if not hasattr(self, "_breaches"):
            self._breaches = self.cra._build_breaches_result_group(
                f"_{self.dataset_name}"
            )
        return self._breaches

    @property
    def pumps(self):
        if not hasattr(self, "_pumps"):
            self._pumps = self.cra._build_pumps_result_group(f"_{self.dataset_name}")
        return self._pumps


class CustomizedWaterQualityResultAdmin(GridH5Admin):
    """Interface for customized 3Di water quality result files

    Customized water quality 3Di result files are result files where users can specify
    nodes, lines, and pumps of interest. This interface can be used to extract data from
    customized water quality result files. It can be used to extract data from the
    result area of interest.

        >>> cwqa = CustomizedWaterQualityResultAdmin(gridadmin_path, customized_water_quality_results_3di.nc)
        >>> cwqa.substance1.concentration
        >>> cwqa.substance2.name
        >>> cwqa.area1.substance1.subset("1D_ALL").id
        >>> cwqa.area2.substance2.subset("2D_ALL").concentration
    """

    def __init__(
        self,
        h5_file_path: str,
        netcdf_file_path: str,
        file_modus: str = "r",
        swmr: bool = False,
    ) -> None:
        """
        :param h5_file_path: path to the hdf5 gridadmin file
        :param netcdf_file_path: path to the water quality result file
            (usually structure_control_actions_3di.nc)
        :param file_modus: modus in which to open the files
        """
        self._netcdf_file_path: str = netcdf_file_path
        super().__init__(h5_file_path, file_modus)

        if swmr:
            self.netcdf_file = H5SwmrFile(netcdf_file_path, file_modus)
        else:
            self.netcdf_file = h5py.File(netcdf_file_path, file_modus)
        self.netcdf_keys = self.netcdf_file.keys()

        self._timeseries_chunk_size = slice(0, DEFAULT_CHUNK_TIMESERIES.stop)
        self._grid_kwargs.update({"timeseries_chunk_size": self._timeseries_chunk_size})

        # Get substances, sets substances as attributes: cwqa.substance1
        self.substances = []
        for key in self.netcdf_keys:
            regex_match = re.search(r"substance\d+", key)
            if regex_match:
                substance = regex_match.group()
                self.substances.append(substance)
                result_group = self._build_substance_result_group(substance, "")
                self.__setattr__(substance, result_group)
                self._set_substance_attributes_on_result_group(result_group, substance)

        # Get areas, sets areas as attributes: cwqa.area1
        self.areas = []
        self._add_area_groups()

    def get_model_instance_by_field_name(self, field_name):
        """
        :param field_name: name of a models field
        :return: instance of the model the field belongs to
        :raises AttributeError if the model instance cannot be found
        """
        try:
            model_instance = self.__getattribute__(field_name)
            return model_instance
        except AttributeError:
            raise AttributeError(
                f"Model instance with field name {field_name} not found"
            )

    def set_timeseries_chunk_size(self, new_chunk_size: int) -> None:
        """
        overwrite the default chunk size for timeseries queries.
        :param new_chunk_size <int>: new chunk size for
            timeseries queries
        :raises ValueError when the given value is less than 1
        """
        _chunk_size = int(new_chunk_size)
        if _chunk_size < 1:
            raise ValueError("Chunk size must be greater than 0")
        self._timeseries_chunk_size = slice(0, _chunk_size)
        logger.info("New chunk for timeseries size has been set to %d", new_chunk_size)
        self._grid_kwargs.update({"timeseries_chunk_size": self._timeseries_chunk_size})

        # Update timeseries chunk size for all substances
        for substance in self.substances:
            result_group = self.__getattribute__(substance)
            result_group.class_kwargs.update(
                {"timeseries_chunk_size": self._timeseries_chunk_size}
            )

        # Update timeseries chunk size for all substances per area
        for area in self.areas:
            for substance in self.substances:
                result_group = self.__getattribute__(area).__getattribute__(substance)
                result_group.class_kwargs.update(
                    {"timeseries_chunk_size": self._timeseries_chunk_size}
                )

    def _build_substance_result_group(self, substance: str, area: str) -> None:
        return Nodes(
            H5pyResultGroup(self.h5py_file, "nodes", self.netcdf_file),
            **dict(
                self._grid_kwargs,
                **{
                    "mixin": get_nodes_customized_water_quality_results_mixin(
                        substance, self.netcdf_keys, area
                    )
                },
            ),
        )

    def _set_substance_attributes_on_result_group(
        self, result_group: Nodes, substance: str
    ) -> None:
        for key in self.netcdf_keys:
            regex_match = re.search(rf"{substance}_(1|2)D", key)
            if regex_match:
                dataset = regex_match.group()
                attrs_map = [("name", "substance_name"), ("units", "units")]
                for attr, name in attrs_map:
                    value = self.netcdf_file[dataset].attrs.get(name)
                    if isinstance(value, bytes):
                        value = value.decode("utf-8")
                    elif isinstance(value, h5py.Empty):
                        value = ""

                    result_group.__setattr__(attr, value)

    def _add_area_groups(self) -> None:
        for key in self.netcdf_keys:
            regex_match = re.search(r"Mesh\d{1,2}DNode_id_area\d+", key)
            if regex_match:
                # Set area as attribute and create area result admin
                dataset_name = regex_match.group().split("_")[-1]
                area_name = self.netcdf_file[key].attrs.get("area_name", dataset_name)
                if not hasattr(self, dataset_name):
                    self.areas += [dataset_name]
                    self.__setattr__(
                        dataset_name,
                        _CustomizedWaterQualityAreaResultAdmin(
                            self, dataset_name, area_name
                        ),
                    )

    def close(self) -> None:
        super().close()
        self.netcdf_file.close()

    @property
    def nodes(self):
        return None

    @property
    def lines(self):
        return None

    @property
    def breaches(self):
        return None

    @property
    def pumps(self):
        return None

    @property
    def levees(self):
        return None

    @property
    def nodes_embedded(self):
        return None

    @property
    def cross_sections(self):
        return None

    @property
    def cells(self):
        return None


class _CustomizedWaterQualityAreaResultAdmin:
    """Nested class for customized water quality 3Di result files to interact with
    specific areas"""

    def __init__(
        self,
        customized_result_admin: CustomizedWaterQualityResultAdmin,
        dataset_name: str,
        area_name: str,
    ) -> None:
        self.cwqra = customized_result_admin
        self.name = area_name
        self._timeseries_chunk_size = customized_result_admin._timeseries_chunk_size
        self._grid_kwargs = customized_result_admin._grid_kwargs

        for substance in self.cwqra.substances:
            result_group = self.cwqra._build_substance_result_group(
                substance, f"_{dataset_name}"
            )
            self.__setattr__(substance, result_group)
            self.cwqra._set_substance_attributes_on_result_group(
                result_group, substance
            )
