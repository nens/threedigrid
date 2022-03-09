# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

import logging

import numpy as np

from threedigrid.admin.prepare_utils import db_objects_to_numpy_array_dict
from threedigrid.admin.utils import PKMapper

logger = logging.getLogger(__name__)


class PreparePumps:
    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource, pump_group):
        node_group = h5py_file["nodes"]
        datasource = pump_group

        # Step 1: Load data from threedi_datasource
        pumpstations_field_names = [
            "pk",
            "display_name",
            "type",
            "start_level",
            "lower_stop_level",
            "capacity",
            "connection_node_start_pk",
            "connection_node_end_pk",
            "zoom_category",
        ]

        pumpstations_numpy_array_dict = db_objects_to_numpy_array_dict(
            threedi_datasource.v2_pumpstations, pumpstations_field_names
        )

        ids = np.array([False])
        for field_name in pumpstations_field_names:
            data = pumpstations_numpy_array_dict[field_name]
            dataset_name = field_name

            if dataset_name == "pk":
                dataset_name = "content_pk"
                ids = np.arange(1, data.size + 1)

            # insert trash element
            data = np.insert(data.copy(), 0, 0, axis=len(data.shape) - 2)

            datasource.set(dataset_name, data)

        if np.any(ids):
            data = np.insert(ids.copy(), 0, 0, axis=len(data.shape) - 2)
            datasource.set("id", data)

        # Step 2: Postprocessing data

        # Connection nodes are nodes with content_pk != 0
        connection_nodes_mask = node_group["content_pk"][:] != 0
        connection_nodes_content_pks = node_group["content_pk"][:][
            connection_nodes_mask
        ]
        connection_nodes_content_id = node_group["id"][:][connection_nodes_mask]
        connection_nodes_content_coordinates = node_group["coordinates"][:][
            :, connection_nodes_mask
        ]

        connection_nodes_initial_waterlevel = node_group["initial_waterlevel"][:][
            connection_nodes_mask
        ]

        cn1_mapper = PKMapper(
            connection_nodes_content_pks, datasource["connection_node_start_pk"]
        )
        cn2_mapper = PKMapper(
            connection_nodes_content_pks, datasource["connection_node_end_pk"]
        )

        if "node1_id" not in list(datasource.keys()):
            node1_id = cn1_mapper.apply_on(connection_nodes_content_id, -9999)
            datasource.set("node1_id", node1_id)

        if "node2_id" not in list(datasource.keys()):
            node2_id = cn2_mapper.apply_on(connection_nodes_content_id, -9999)
            datasource.set("node2_id", node2_id)

        if "bottom_level" not in list(datasource.keys()):
            bottom_level = cn1_mapper.apply_on(connection_nodes_initial_waterlevel, 0)
            datasource.set("bottom_level", bottom_level)

        if "node_coordinates" not in list(datasource.keys()):
            node1_coordinates = cn1_mapper.apply_on(
                connection_nodes_content_coordinates, -9999
            )
            node2_coordinates = cn2_mapper.apply_on(
                connection_nodes_content_coordinates, -9999
            )

            datasource.set(
                "node_coordinates", np.vstack((node1_coordinates, node2_coordinates))
            )

        if "coordinates" not in list(datasource.keys()):
            # Set the coordinates based on the centroid of node_coordinates
            # if both set and else the one that is set.
            node_coordinates = datasource["node_coordinates"][:]
            node1_coords = node_coordinates[0:2, :]
            node2_coords = node_coordinates[2:4, :]
            node1_id = datasource["node1_id"][:]
            node2_id = datasource["node2_id"][:]
            node1_not_set = node1_id == -9999
            node2_not_set = node2_id == -9999

            # Replace empty values with coords from other node
            node2_coords[:, node2_not_set] = node1_coords[:, node2_not_set]
            node1_coords[:, node1_not_set] = node2_coords[:, node1_not_set]

            # Calculate centroids
            datasource.set("coordinates", (node2_coords + node1_coords) / 2.0)
