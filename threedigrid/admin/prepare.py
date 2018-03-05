# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import logging
import os
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
    PrepareNodes, PrepareManholes, PrepareConnectionNodes)
from threedigrid.admin.pumps.prepare import PreparePumps
from threedigrid.admin.levees.models import Levees

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
            for key, value in extra_attrs.iteritems():
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

        if not is_prepared(h5py_file, 'lines', 'line_prepared'):
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
    Exporter that saves shapefiles to the model's /preprocessed dir
    """

    def __init__(self, gridadmin_file, export_method='to_shape'):
        """

        :param gridadmin_file: hdf5 file (full path)
        """
        self.ga = GridH5Admin(gridadmin_file)
        self._dest = os.path.split(gridadmin_file)[0]
        self._export_method = export_method

    def export_all(self):
        """convenience function to run all exports"""
        self.export_nodes()
        self.export_lines()
        self.export_grid()
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
        dest = os.path.join(self._dest, constants.NODES_SHP)
        getattr(self.ga.nodes.subset(
            constants.SUBSET_1D_ALL), self._export_method)(dest)

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
        dest = os.path.join(self._dest, constants.LINES_SHP)
        getattr(self.ga.lines.subset(
            constants.SUBSET_1D_ALL), self._export_method)(dest)

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
        dest = os.path.join(self._dest, constants.LEVEES_SHP)
        getattr(self.ga.levees, self._export_method)(dest)

    def export_grid(self):
        """
        writes shapefile of all 2D groundwater and open water
        cells (if present)
        """
        self._export_2d_grid()
        self._export_groundwater_grid()

    def _export_groundwater_grid(self):
        if not self.ga.has_groundwater:
            logger.info(
                "[*] Model {} does not have groundwater, "
                "skipping export groundwater cells...".format(self.ga.model_name)
            )
            return
        dest_gw = os.path.join(self._dest, constants.GROUNDWATER_SHP)
        getattr(self.ga.cells.subset(
            constants.SUBSET_2D_GROUNDWATER), self._export_method)(dest_gw)

    def _export_2d_grid(self):
        if not self.ga.has_2d:
            logger.info(
                "[*] Model {} does not have 2D, "
                "skipping export 2d cells...".format(
                    self.ga.model_name)
            )
            return

        dest_ow = os.path.join(self._dest, constants.OPEN_WATER_SHP)

        getattr(self.ga.cells.subset(
            constants.SUBSET_2D_OPEN_WATER), self._export_method)(dest_ow)
