# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import

import json
import logging
import os

import numpy as np
import six

from threedigrid.admin.h5py_datasource import H5pyGroup
from threedigrid.admin.idmapper import IdMapper
from threedigrid.admin import constants
from threedigrid.admin.gridadmin import GridH5Admin

from threedigrid.admin.breaches.prepare import PrepareBreaches
from threedigrid.admin.lines.prepare import (
    PrepareLines, PrepareChannels, PreparePipes, PrepareWeirs,
    PrepareOrifices, PrepareCulverts)

from threedigrid.admin.levees.prepare import PrepareLevees
from threedigrid.admin.nodes.prepare import (
    PrepareNodes, PrepareManholes, PrepareConnectionNodes, PrepareCells)
from threedigrid.admin.pumps.prepare import PreparePumps
from threedigrid.admin.levees.models import Levees
from threedigrid.orm.base.encoder import NumpyEncoder
from threedigrid.orm.constants import EXPORT_METHOD_TO_EXTENSION_MAP

logger = logging.getLogger(__name__)


def is_prepared(h5py_file, group_name, attr_name):
    if group_name not in h5py_file:
        return False
    return h5py_file[group_name].attrs.get(attr_name, 0) == 1


def skip_prepare(h5py_file, group_name, attr_name, overwrite):
    if overwrite:
        return False
    return is_prepared(h5py_file, group_name, attr_name)


def prepare_lines_onedee(
        h5py_file, threedi_datasource, klass, attr_name, overwrite=False):

    if skip_prepare(h5py_file, 'lines', attr_name, overwrite):
        return

    klass.prepare_datasource(h5py_file, threedi_datasource)

    h5py_file['lines'].attrs[attr_name] = 1


class GridAdminH5Prepare(object):
    @staticmethod
    def prepare(h5py_file, threedi_datasource, extra_attrs=None):
        # Step 1: Set optional extra attrs like epsg code,
        # model_name, revision_number, revision_hash
        # and possible other meta data..
        if extra_attrs:
            for key, value in six.iteritems(extra_attrs):
                if isinstance(value, six.string_types):
                    value = np.string_(value)
                h5py_file.attrs[key] = value

        # Step 3: prepare the ID mapper
        IdMapper.prepare_mapper(
            h5py_file, threedi_datasource)

        # Step 4: Prepare nodes/lines
        GridAdminH5Prepare.prepare_nodes(h5py_file, threedi_datasource)
        GridAdminH5Prepare.prepare_lines(h5py_file, threedi_datasource)

        # Step 5: Prepare onedee lines/nodes/pumps
        GridAdminH5Prepare.prepare_onedee_lines(h5py_file, threedi_datasource)
        GridAdminH5Prepare.prepare_onedee_nodes(h5py_file, threedi_datasource)
        GridAdminH5Prepare.prepare_pumps(h5py_file, threedi_datasource)

        # Step 6: prepare levees
        GridAdminH5Prepare.prepare_levees(h5py_file, threedi_datasource)

        # Step 7: prepare breaches
        GridAdminH5Prepare.prepare_breaches(h5py_file, threedi_datasource)

    @staticmethod
    def prepare_levees(h5py_file, threedi_datasource, overwrite=False):
        if not threedi_datasource.levees:
            return

        if skip_prepare(h5py_file, 'levees', 'prepared', overwrite):
            return

        PrepareLevees.prepare_datasource(h5py_file, threedi_datasource)

        h5py_file['levees'].attrs['prepared'] = 1

    @staticmethod
    def prepare_onedee_nodes(h5py_file, threedi_datasource, overwrite=False):
        has_1d = h5py_file.attrs.get('has_1d', 0) == 1

        if not has_1d:
            return

        if not is_prepared(h5py_file, 'nodes', 'prepared'):
            # Line data is missing, prepare line data first.
            GridAdminH5Prepare.prepare_nodes(h5py_file, threedi_datasource)

        if skip_prepare(h5py_file, 'nodes', 'connectionnodes_prepared',
                        overwrite):
            return

        PrepareConnectionNodes.prepare_datasource(
                h5py_file, threedi_datasource)

        h5py_file['nodes'].attrs['connectionnodes_prepared'] = 1

        if skip_prepare(h5py_file, 'nodes', 'manholes_prepared', overwrite):
            return

        PrepareManholes.prepare_datasource(h5py_file, threedi_datasource)

        h5py_file['nodes'].attrs['manholes_prepared'] = 1

    @staticmethod
    def prepare_nodes(h5py_file, threedi_datasource, overwrite=False):
        if skip_prepare(h5py_file, 'nodes', 'prepared', overwrite):
            return

        has_1d = h5py_file.attrs.get('has_1d', 0) == 1

        if has_1d:
            mapping1d = H5pyGroup(h5py_file, 'mapping1d')
        else:
            mapping1d = None

        id_mapper = IdMapper(H5pyGroup(h5py_file, 'mappings')['id_map'])

        # Prepare nodes
        node_group = H5pyGroup(h5py_file, 'nodes')
        PrepareNodes.prepare_datasource(
            node_group, mapping1d, id_mapper, has_1d=has_1d)

        PrepareCells.prepare_datasource(h5py_file, threedi_datasource)

        h5py_file['nodes'].attrs['prepared'] = 1

    @staticmethod
    def prepare_lines(h5py_file, threedi_datasource, overwrite=False):
        # Prepare lines
        if skip_prepare(h5py_file, 'lines', 'lines_prepared', overwrite):
            return

        has_1d = h5py_file.attrs.get('has_1d', 0) == 1

        line_group = H5pyGroup(h5py_file, 'lines')
        node_group = H5pyGroup(h5py_file, 'nodes')

        id_mapper = IdMapper(H5pyGroup(h5py_file, 'mappings')['id_map'])

        PrepareLines.prepare_datasource(
            line_group,
            id_mapper, threedi_datasource,
            [node_group['x_coordinate'], node_group['y_coordinate']],
            has_1d=has_1d
        )

        h5py_file['lines'].attrs['lines_prepared'] = 1

    @staticmethod
    def prepare_breaches(h5py_file, threedi_datasource, overwrite=True):
        if skip_prepare(h5py_file, 'breaches', 'prepared', overwrite):
            return

        if not is_prepared(h5py_file, 'lines', 'line_prepared'):
            # Line data is missing, prepare line data first.
            GridAdminH5Prepare.prepare_lines(h5py_file, threedi_datasource)

        if not is_prepared(h5py_file, 'levees', 'prepared'):
            # Levee data is missing, prepare levee data first.
            GridAdminH5Prepare.prepare_levees(h5py_file, threedi_datasource)

        has_breaches = h5py_file.attrs.get('has_breaches', 0) == 1
        levees = None
        if 'levees' in h5py_file:
            levees = Levees(H5pyGroup(h5py_file, 'levees'))

        id_mapper = IdMapper(H5pyGroup(h5py_file, 'mappings')['id_map'])
        line_group = H5pyGroup(h5py_file, 'lines')

        # Prepare breaches
        if has_breaches:
            PrepareBreaches.prepare_datasource(
                H5pyGroup(h5py_file, 'breaches', required=True),
                line_group['kcu'], id_mapper, levees,
                line_group['line_coords']
            )

            h5py_file['breaches'].attrs['prepared'] = 1

    @staticmethod
    def prepare_onedee_lines(h5py_file, threedi_datasource, overwrite=False):
        has_1d = h5py_file.attrs.get('has_1d', 0) == 1

        if not has_1d:
            return

        if not is_prepared(h5py_file, 'lines', 'lines_prepared'):
            # Line data is missing, prepare line data first.
            GridAdminH5Prepare.prepare_lines(h5py_file, threedi_datasource)

        # Load data from threedi_datasource into the h5py_file on
        # the lines group.
        prepare_lines_onedee(
            h5py_file, threedi_datasource, PrepareChannels,
            'channels_prepared', overwrite)

        prepare_lines_onedee(
            h5py_file, threedi_datasource, PreparePipes,
            'pipes_prepared', overwrite)

        prepare_lines_onedee(
            h5py_file, threedi_datasource, PrepareWeirs,
            'weirs_prepared', overwrite)

        prepare_lines_onedee(
            h5py_file, threedi_datasource, PrepareOrifices,
            'orifices_prepared', overwrite)

        prepare_lines_onedee(
            h5py_file, threedi_datasource, PrepareCulverts,
            'culverts_prepared', overwrite)

    @staticmethod
    def prepare_pumps(h5py_file, threedi_datasource, overwrite=False):
        has_1d = h5py_file.attrs.get('has_1d', 0) == 1
        has_pumpstations = h5py_file.attrs.get('has_pumpstations', 0) == 1

        if not has_1d or not has_pumpstations:
            return

        if skip_prepare(h5py_file, 'pumps', 'prepared', overwrite):
            return

        # if not h5py_file.attrs.get('has_pumpstations'):
        #    logger.info('[*] Datasource does not have pumps, skipping...')
        #    return

        if not is_prepared(h5py_file, 'nodes', 'prepared'):
            # Node data is missing, prepare node data first.
            GridAdminH5Prepare.prepare_nodes(h5py_file, threedi_datasource)

        PreparePumps.prepare_datasource(
            h5py_file, threedi_datasource, H5pyGroup(h5py_file, 'pumps'))

        h5py_file['pumps'].attrs['prepared'] = 1


class GridAdminH5Export(object):
    """
    Exporter that saves shapefiles/geopackage/geojson to destination folder
    """

    def __init__(
            self,
            gridadmin_file,
            export_method='to_shape',
            target_epsg_code=None,
            destination=None,
            indent=None
    ):
        """

        :param gridadmin_file: hdf5 file (full path)
        :param export_method: (str) 'to_shape', 'to_gpkg' or 'to_geojson'
        :param target_epsg_code: (str) epsg code
        :param destination: path to folder the export folder, defaults to
            the same folder as the gridadmin_file
        """
        self.ga = GridH5Admin(gridadmin_file)
        self._export_method = export_method
        self._extension = EXPORT_METHOD_TO_EXTENSION_MAP[export_method]
        if not target_epsg_code:
            self._epsg = self.ga.epsg_code
        else:
            self._epsg = target_epsg_code
        if not destination:
            self._dest = os.path.split(gridadmin_file)[0]
        else:
            self._dest = destination
        self._indent = indent

    def export_all(self):
        """convenience function to run all exports"""
        self.export_nodes()
        self.export_lines()
        self.export_grid()
        self.export_levees()
        self.export_2d_groundwater_lines()
        self.export_2d_openwater_lines()
        self.export_2d_vertical_infiltration_lines()

    def export_frontend(self):
        self.export_breaches()
        self.export_channels()
        self.export_pipes()
        self.export_weirs()
        self.export_culverts()
        self.export_orifices()
        self.export_manholes()
        self.export_nodes()
        self.export_pumps()
        self.export_levees()
        self.export_grid()
        self._combine(
            output_name="all",
            file_names={
                'breaches', 'channels', 'pipes', 'weirs', 'culverts',
                'orifices', 'manholes', constants.NODES, 'pumps', 'levees'
            }
        )
        self._combine(
            output_name="cells",
            file_names={constants.OPEN_WATER, constants.GROUNDWATER}
        )

    def _combine(self, output_name, file_names):
        """Combine the `file_names` into a new file called `output_name`.

        The files are simply appended. Only works for geojson.

        :param output_name: name of the new file
        :param file_names: file names to combine
        :return:
        """
        if self._extension not in ('.json', '.geojson'):
            logger.info("Can only combine exports with geojson")
            return

        dest = os.path.join(self._dest, output_name + self._extension)
        with open(dest, 'w') as output_file:
            features = []
            for file_name in file_names:
                intermediate_result = os.path.join(
                    self._dest, file_name + self._extension
                )
                if not os.path.exists(intermediate_result):
                    continue

                with open(intermediate_result, 'r') as ir:
                    geojson = json.load(ir)
                    im_features = geojson['features']
                    features += im_features

            json.dump(
                {"type": "FeatureCollection", "features": features},
                output_file,
                indent=self._indent,
                cls=NumpyEncoder,
            )

    def export_1d_all(self):
        self.export_nodes()
        self.export_lines()
        self.export_levees()

    def export_nodes(self):
        """
        writes shapefile of all 1D nodes
        """
        if not self.ga.has_1d:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export nodes...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, constants.NODES + self._extension)
        getattr(
            self.ga.nodes.subset(
                constants.SUBSET_1D_ALL
            ).reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_lines(self):
        """
        writes shapefile of all 1D lines
        """
        if not self.ga.has_1d:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export lines...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, constants.LINES + self._extension)
        getattr(
            self.ga.lines.subset(
                constants.SUBSET_1D_ALL
            ).reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_breaches(self):
        if self.ga.breaches.id.size == 0:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export breaches...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, 'breaches' + self._extension)
        getattr(
            self.ga.breaches.reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_channels(self):
        if self.ga.lines.channels.id.size == 0:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export channels...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, 'channels' + self._extension)
        getattr(
            self.ga.lines.channels.reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_pipes(self):
        if self.ga.lines.pipes.id.size == 0:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export pipes...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, 'pipes' + self._extension)
        getattr(
            self.ga.lines.pipes.reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_weirs(self):
        if self.ga.lines.weirs.id.size == 0:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export weirs...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, 'weirs' + self._extension)
        getattr(
            self.ga.lines.weirs.reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_culverts(self):
        if self.ga.lines.culverts.id.size == 0:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export culverts...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, 'culverts' + self._extension)
        getattr(
            self.ga.lines.culverts.reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_orifices(self):
        if self.ga.lines.orifices.id.size == 0:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export orifices...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, 'orifices' + self._extension)
        getattr(
            self.ga.lines.orifices.reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_manholes(self):
        if self.ga.nodes.manholes.id.size == 0:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export manholes...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, 'manholes' + self._extension)
        getattr(
            self.ga.nodes.manholes.reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_pumps(self):
        if self.ga.pumps.id.size == 0:
            logger.info(
                "[*] Model {} does not have 1D, "
                "skipping export pumps...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, 'pumps' + self._extension)
        getattr(
            self.ga.pumps.reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_levees(self):
        """
        writes shapefile of levees
        """
        if not self.ga.has_levees:
            logger.info(
                "[*] Model {} does not have levees, "
                "skipping export levees...".format(self.ga.model_name)
            )
            return
        dest = os.path.join(self._dest, constants.LEVEES + self._extension)
        getattr(
            self.ga.levees.reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_grid(self):
        """
        writes shapefile of all 2D groundwater and open water
        cells (if present)
        """
        self._export_2d_grid()
        self._export_groundwater_grid()

    def export_2d_groundwater_lines(self):
        if not (self.ga.has_groundwater and self.ga.has_2d):
            logger.info(
                "[*] Model {} does not have 2d groundwater lines, "
                "skipping export 2d groundwater lines...".format(
                    self.ga.model_name)
            )
            return
        dest = os.path.join(
            self._dest, constants.GROUNDWATER_LINES + self._extension
        )
        getattr(
            self.ga.lines.subset(
                constants.SUBSET_2D_GROUNDWATER).reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_2d_openwater_lines(self):
        if not self.ga.has_2d:
            logger.info(
                "[*] Model {} does not have 2D, "
                "skipping export 2d open water lines...".format(
                    self.ga.model_name)
            )
            return
        dest = os.path.join(
            self._dest, constants.OPEN_WATER_LINES + self._extension
        )
        getattr(
            self.ga.lines.subset(
                constants.SUBSET_2D_OPEN_WATER).reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def export_2d_vertical_infiltration_lines(self):
        if not self.ga.has_2d:
            logger.info(
                "[*] Model {} does not have 2D, "
                "skipping export 2d vertical infiltration lines...".format(
                    self.ga.model_name)
            )
            return
        dest = os.path.join(
            self._dest,
            constants.VERTICAL_INFILTRATION_LINES + self._extension
        )
        getattr(
            self.ga.lines.subset(
                constants.SUBSET_2D_VERTICAL_INFILTRATION
            ).reproject_to(self._epsg),
            self._export_method
        )(dest, indent=self._indent)

    def _export_groundwater_grid(self):
        if not self.ga.has_groundwater:
            logger.info(
                "[*] Model {} does not have groundwater, "
                "skipping export groundwater cells...".format(
                    self.ga.model_name
                )
            )
            return
        dest_gw = os.path.join(
            self._dest, constants.GROUNDWATER + self._extension
        )
        getattr(
            self.ga.cells.subset(
                constants.SUBSET_2D_GROUNDWATER).reproject_to(self._epsg),
            self._export_method
        )(dest_gw, indent=self._indent)

    def _export_2d_grid(self):
        if not self.ga.has_2d:
            logger.info(
                "[*] Model {} does not have 2D, "
                "skipping export 2d cells...".format(
                    self.ga.model_name)
            )
            return

        dest_ow = os.path.join(
            self._dest, constants.OPEN_WATER + self._extension
        )
        getattr(
            self.ga.cells.subset(
                constants.SUBSET_2D_OPEN_WATER).reproject_to(self._epsg),
            self._export_method
        )(dest_ow, indent=self._indent)
