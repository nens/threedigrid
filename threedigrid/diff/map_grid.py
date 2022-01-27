import logging
from pathlib import Path

import numpy as np
import pygeos

from threedigrid.admin.gridadmin import GridH5Admin

logger = logging.getLogger(__name__)


def has_doubles(arr):
    """Return True if an array has doubles"""
    return np.any(np.bincount(arr) > 1)


def _map_nodes(old_ga, new_ga, max_distance, **filters):
    old_data = old_ga.nodes.filter(id__ne=0, **filters).only("id", "coordinates").data
    if len(old_data["id"]) == 0:
        return
    # patch "coordinates" if it is missing
    if len(old_data["coordinates"]) == 0:
        old_data["coordinates"] = np.array(
            [
                old_ga.h5py_file["nodes"]["x_coordinate"][old_data["id"]],
                old_ga.h5py_file["nodes"]["y_coordinate"][old_data["id"]],
            ]
        )
    new_data = new_ga.nodes.filter(id__ne=0, **filters).only("id", "coordinates").data
    if len(new_data["id"]) == 0:
        return
    tree = pygeos.STRtree(pygeos.points(new_data["coordinates"].T))
    old_idx, new_idx = tree.nearest_all(
        pygeos.points(old_data["coordinates"].T),
        max_distance=max_distance,
    )
    if has_doubles(old_idx) or has_doubles(new_idx) > 0:
        raise NotImplementedError("Unable to uniquely map old to new node ids.")

    return old_data["id"][old_idx], new_data["id"][new_idx]


def _map_lines(old_ga, new_ga, node_mapping, **filters):
    old_data = old_ga.lines.filter(id__ne=0, **filters).only("id", "line").data
    new_data = new_ga.lines.filter(id__ne=0, **filters).only("id", "line").data
    old_line = np.take(node_mapping, old_data["line"])
    new_line = new_data["line"]
    tree = pygeos.STRtree(pygeos.points(new_line.T))
    old_idx, new_idx = tree.query_bulk(pygeos.points(old_line.T))
    if has_doubles(old_idx) or has_doubles(new_idx) > 0:
        raise NotImplementedError("Unable to uniquely map old to new line ids.")
    return old_data["id"][old_idx], new_data["id"][new_idx]


def create_grid_mapping(old_path: Path, new_path: Path, max_distance: float = 0.01):
    """Create a mapping for nodes and lines between two gridadmin files

    Args:
        old_path: The path to a gridadmin file
        new_path: The path to a gridadmin file
        max_distance: The maximum distance between old and new nodes. The nearest will
          always be taken. If there are two options, a warning will be emitted and the
          first is taken.

    Returns:
        tuple of:
        - ndarray with shape (n_nodes_old, ) mapping old to new node ids
        - ndarray with shape (n_lines_old, ) mapping old to new line ids
    """
    if isinstance(old_path, str):
        old_path = Path(old_path)
    if isinstance(new_path, str):
        new_path = Path(new_path)

    if not old_path.exists():
        raise FileNotFoundError(
            "Unable to find old gridadmin to make the node/line mappings."
        )
    if not new_path.exists():
        raise FileNotFoundError(
            "Unable to find new gridadmin to make the node/line mappings."
        )

    old_ga = GridH5Admin(old_path)
    new_ga = GridH5Admin(new_path)

    # Create the node mapping by iterating over unique node_types
    node_mapping = np.full(old_ga.nodes.count, fill_value=-9999)
    all_node_type = np.unique(old_ga.nodes.only("node_type").data["node_type"][1:])
    for node_type in all_node_type:
        if node_type == 3:
            node_type = [3, 4]
        else:
            node_type = [node_type]
        _mapping = _map_nodes(old_ga, new_ga, max_distance, node_type__in=node_type)
        if _mapping is not None:
            node_mapping[_mapping[0]] = _mapping[1]

    logger.info(
        f"Matched {np.count_nonzero(node_mapping != -9999)} of {old_ga.nodes.count} nodes."
    )

    # Create the line mapping by iterating over unique kcu
    line_mapping = np.full(old_ga.lines.count, fill_value=-9999)
    all_kcu = np.unique(old_ga.lines.only("kcu").data["kcu"][1:])
    # lump 1D2D lines (5x) together because of changes there
    is_1d2d = (all_kcu >= 50) & (all_kcu < 60)
    all_kcu_groups = [[x] for x in all_kcu[~is_1d2d]]
    if np.any(is_1d2d):
        all_kcu_groups.append(range(50, 60))
    for kcu_group in all_kcu_groups:
        _mapping = _map_lines(old_ga, new_ga, node_mapping, kcu__in=kcu_group)
        if _mapping is not None:
            line_mapping[_mapping[0]] = _mapping[1]

    logger.info(
        f"Matched {np.count_nonzero(line_mapping != -9999)} of {old_ga.lines.count} lines."
    )

    old_ga.close()
    new_ga.close()
    return node_mapping, line_mapping


def map_ids(lhs_ids, rhs_ids, mapping):
    new_lhs_ids = mapping[lhs_ids]

    # We really need all ids, else the arrays will shift and the diff will compare
    # different nodes.
    missing = sorted(set(rhs_ids) - set(new_lhs_ids))
    n_missing = len(missing)
    if n_missing > 0:
        not_assigned = new_lhs_ids == -9999
        n_not_assigned = np.count_nonzero(not_assigned)
        if n_not_assigned < n_missing:
            not_assigned |= np.isin(
                new_lhs_ids, np.sort(new_lhs_ids)[(n_not_assigned - n_missing) :]
            )
        elif n_not_assigned > n_missing:
            missing += [999999] * (n_not_assigned - n_missing)
        new_lhs_ids[not_assigned] = missing
    return new_lhs_ids
