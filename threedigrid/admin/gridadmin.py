# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
Main entry point for threedigrid applications.
"""

import logging

import h5py
import numpy as np

from threedigrid.admin.breaches.models import Breaches
from threedigrid.admin.crosssections.models import CrossSections
from threedigrid.admin.h5py_datasource import H5pyGroup
from threedigrid.admin.levees.models import Levees
from threedigrid.admin.lines.models import Lines
from threedigrid.admin.nodes.models import Cells, EmbeddedNodes, Grid, Nodes
from threedigrid.admin.pumps.models import Pumps
from threedigrid.geo_utils import raise_import_exception, transform_bbox

try:
    import pyproj
except ImportError:
    pyproj = None

try:
    import asyncio

    import asyncio_rpc  # noqa

    asyncio_rpc_support = True
except ImportError:
    asyncio_rpc_support = False


from . import constants

logger = logging.getLogger(__name__)


class GridH5Admin:
    """
    Parses the hdf5 gridadmin file and exposes the model instances, e.g.::

        >>> ga = GridH5Admin(file_path)
        >>> ga.nodes
        >>> ga.lines
        >>> ...
    """

    def __init__(self, h5_file_path, file_modus="r", set_props=False):
        """
        :param h5_file_path: path to the gridadmin file
        :param file_modus: mode with which to open the file
            (defaults to r=READ)
        """

        self.grid_file = h5_file_path
        self.datasource_class = H5pyGroup
        self.is_rpc = False

        if type(h5_file_path) in (str, bytes) and h5_file_path.startswith("rpc://"):
            if not asyncio_rpc_support:
                raise Exception("Please reinstall this package with threedigrid[rpc]")

            from threedigrid.admin.rpc_datasource import H5RPCGroup, RPCFile

            self.h5py_file = RPCFile(h5_file_path, file_modus)
            self.datasource_class = H5RPCGroup
            self._grid_kwargs = {}
            self.is_rpc = True
            self.has_1d = True
        else:
            self.h5py_file = h5py.File(h5_file_path, file_modus)
            set_props = True

        if set_props:
            self._set_props()

        self._grid_kwargs = {"has_1d": self.has_1d}

    @property
    def grid(self):
        if self.is_rpc:
            raise Exception("RPC not available for grid")
        kwargs = self._grid_kwargs.copy()
        kwargs["n2dtot"] = self.get_from_meta("n2dtot")
        return Grid(
            self.datasource_class(self.h5py_file, "grid_coordinate_attributes"),
            **kwargs
        )

    @property
    def levees(self):
        if self.is_rpc:
            raise Exception("RPC no available for levees")

        return Levees(
            self.datasource_class(self.h5py_file, "levees"), **self._grid_kwargs
        )

    @property
    def nodes(self):
        return Nodes(
            self.datasource_class(self.h5py_file, "nodes"), **self._grid_kwargs
        )

    @property
    def nodes_embedded(self):
        return EmbeddedNodes(
            self.datasource_class(self.h5py_file, "nodes_embedded"), **self._grid_kwargs
        )

    @property
    def lines(self):
        return Lines(
            self.datasource_class(self.h5py_file, "lines"), **self._grid_kwargs
        )

    @property
    def cross_sections(self):
        return CrossSections(
            self.datasource_class(self.h5py_file, "cross_sections"), **self._grid_kwargs
        )

    @property
    def pumps(self):
        return Pumps(
            self.datasource_class(self.h5py_file, "pumps"), **self._grid_kwargs
        )

    @property
    def breaches(self):
        return Breaches(
            self.datasource_class(self.h5py_file, "breaches", gridadmin=self),
            **self._grid_kwargs
        )

    @property
    def cells(self):
        # treated as nodes
        return Cells(
            self.datasource_class(self.h5py_file, "nodes"), **self._grid_kwargs
        )

    @property
    def revision_hash(self):
        """mercurial revision hash of the model"""
        return self._to_str(self.h5py_file.attrs["revision_hash"])

    @property
    def revision_nr(self):
        """mercurial revision nr or id of the model"""
        return self._to_str(self.h5py_file.attrs["revision_nr"])

    @property
    def model_name(self):
        """name of the model the gridadmin file belongs to"""
        return self._to_str(self.h5py_file.attrs["model_name"])

    @property
    def epsg_code(self):
        return self._to_str(self.h5py_file.attrs["epsg_code"])

    @property
    def crs(self):
        if pyproj is None:
            raise_import_exception("pyproj")
        try:
            return pyproj.CRS(self._to_str(self.h5py_file.attrs["crs_wkt"]))
        except KeyError:
            # Fallback for older gridadmins without crs_wkt
            return pyproj.CRS.from_epsg(int(self.h5py_file.attrs["epsg_code"]))

    @property
    def model_slug(self):
        return self._to_str(self.h5py_file.attrs["model_slug"])

    @property
    def threedicore_version(self):
        return self._to_str(self.h5py_file.attrs["threedicore_version"])

    @property
    def threedi_version(self):
        return self._to_str(self.h5py_file.attrs["threedi_version"])

    @property
    def has_levees(self):
        if not hasattr(self, "levees"):
            return False
        return bool(self.levees.id.size)

    def get_extent_subset(self, subset_name, target_epsg_code=""):
        """

        :param subset_name: name of the node subset for which the extent
            should be calculated.
            Valid input: '1D_all', '2D_groundwater'
        :param target_epsg_code: string representation of the desired
            output epsg code
        :return: numpy array of xy-min/xy-max pairs
        """
        if self.is_rpc:
            # Proxy function via RPC
            return self.h5py_file.get_extent_subset(
                subset_name, target_espg_code=target_epsg_code
            )

        attr_name = constants.SUBSET_NAME_H5_ATTR_MAP.get(subset_name.upper())
        extent = self.h5py_file.attrs.get(attr_name, None)
        if extent is None:
            raise AttributeError(
                "The grid admin file %s does not have %s attribute"
                % (self.grid_file, attr_name)
            )
        if attr_name == constants.EXTENT_1D_KEY and not self.has_1d:
            logger.info("[*] The model has no 1D returning...")
            return
        if attr_name == constants.EXTENT_2D_KEY and not self.has_2d:
            logger.info("[*] The model has no 2D returning...")
            return

        if target_epsg_code and target_epsg_code != self.epsg_code:
            extent = transform_bbox(
                extent,
                self.epsg_code,
                target_epsg_code,
            )
        return extent

    def get_model_extent(self, target_epsg_code="", **kwargs):
        """
        get the extent of the model. Combines the extent of 1d and 2d node
        coordinates. If target_epsg_code is different from the models epsg
        code it projects the coordinates to projection of the given
        target epsg code.

        :param target_epsg_code: string representation of the desired
            output epsg code
        :param kwargs:
            extra_extent: list of xy-min/xy-max pairs that need to be
            taken into account in the model extent calculation

        :return: numpy array of xy-min/xy-max pairs

        """
        bbox = kwargs.get("extra_extent", [])
        if self.is_rpc:
            # Proxy function via RPC
            return self.h5py_file.get_model_extent(
                target_epsg_code=target_epsg_code, bbox=bbox
            )

        for k in constants.SUBSET_NAME_H5_ATTR_MAP.keys():
            sub_extent = self.get_extent_subset(
                subset_name=k, target_epsg_code=target_epsg_code
            )
            if sub_extent is None:
                continue
            bbox.append(sub_extent)

        x = np.array(bbox)[:, [0, 2]]
        y = np.array(bbox)[:, [1, 3]]

        return np.array([np.min(x), np.min(y), np.max(x), np.max(y)])

    def _set_props(self):
        if not self.is_rpc:
            for prop, value in self.h5py_file.attrs.items():
                if prop and prop.startswith("has_"):
                    try:
                        setattr(self, prop, bool(value))
                    except AttributeError:
                        logger.warning(
                            "Can not set property {}, already exists".format(prop)
                        )
                        pass
        else:
            from threedigrid.admin.rpc_datasource import _set_property

            properties = ["has_1d", "has_2d", "has_breaches", "has_pumpstations"]
            futures = [_set_property(self, prop) for prop in properties]
            return asyncio.gather(*futures)

    def get_from_meta(self, prop_name):
        if prop_name not in list(self.h5py_file["meta"].keys()):
            return None

        return self.h5py_file["meta"][prop_name][()]

    @staticmethod
    def _to_str(x):
        try:
            return x.decode("utf-8")
        except AttributeError:
            return x

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.h5py_file.close()

    def close(self):
        self.h5py_file.flush()
        self.h5py_file.close()
