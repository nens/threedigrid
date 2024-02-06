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
)
from threedigrid.admin.constants import DEFAULT_CHUNK_TIMESERIES
from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.h5py_datasource import H5pyResultGroup
from threedigrid.admin.h5py_swmr import H5SwmrFile
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.lines.timeseries_mixin import (
    LinesAggregateResultsMixin,
    LinesResultsMixin,
)
from threedigrid.admin.nodes.models import Nodes
from threedigrid.admin.nodes.timeseries_mixin import (
    get_substance_result_mixin,
    NodesAggregateResultsMixin,
    NodesResultsMixin,
)
from threedigrid.admin.pumps.models import Pumps
from threedigrid.admin.pumps.timeseries_mixin import (
    PumpsAggregateResultsMixin,
    PumpsResultsMixin,
)
from threedigrid.admin.structure_controls.models import (
    StructureControl,
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
        self._netcdf_file_path = netcdf_file_path
        super().__init__(h5_file_path, file_modus)

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

        return StructureControl(
            id=id,
            source_table=source_table,
            source_table_id=source_table_id,
            time=self.time[mask],
            action_type=action_type,
            action_value_1=self.action_value_1[mask],
            action_value_2=self.action_value_2[mask],
            is_active=self.is_active[mask],
        )

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
        """Get all structure control actions with ``action_value_1 == value``"""
        return self._group_by_in_between("action_value_1", min, max)

    def group_by_action_value_2(self, min: float, max: float) -> List[StructureControl]:
        """Get all structure control actions with ``action_value_2 == value``"""
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
                    # Set substance name on Nodes
                    self.__getattribute__(substance).__setattr__(
                        "name", self.netcdf_file[key].attrs.get("substance_name")
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
