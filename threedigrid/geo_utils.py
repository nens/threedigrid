# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

import logging
from functools import lru_cache

import numpy as np

try:
    import pyproj
except ImportError:
    pyproj = None

try:
    from osgeo import osr
except ImportError:
    osr = None

try:
    import mercantile
except ImportError:
    mercantile = None

try:
    import shapely
    from shapely.strtree import STRtree
    from shapely.wkt import loads
except ImportError:
    shapely = None

from threedigrid.numpy_utils import select_lines_by_bbox

logger = logging.getLogger(__name__)

MERCANTILE_EPSG_CODE = "4326"

BBOX_LEFT = 0
BBOX_TOP = 1
BBOX_RIGHT = 2
BBOX_BOTTOM = 3


def raise_import_exception(name):
    raise ImportError(
        "Could not import {}, you need to install threedigrid "
        "with the extra [geo], e.g "
        "pip install threedigrid[geo]==<version>".format(name)
    )


@lru_cache(10)
def get_transformer(source_epsg, target_epsg):
    if pyproj is None:
        raise_import_exception("pyproj")

    return pyproj.Transformer.from_crs(
        pyproj.CRS.from_epsg(int(source_epsg)),
        pyproj.CRS.from_epsg(int(target_epsg)),
        always_xy=True,
    )


def transform_xys(x_array, y_array, source_epsg, target_epsg):
    """
    Transform x_array, y_array from source_epsg_code to
    target_epsg code
    """
    transformer = get_transformer(source_epsg, target_epsg)
    assert isinstance(x_array, np.ndarray)
    assert isinstance(y_array, np.ndarray)

    if x_array.size == 0 and y_array.size == 0:
        return np.array([[], []])

    reprojected = transformer.transform(x_array, y_array)
    return np.array(reprojected)


def get_spatial_reference(epsg_code):
    """
    :param epsg_code: Spatial Reference System Identifier (SRID)
        as implemented by the European Petroleum Survey Group (EPSG).

    :return: an osr spatial reference instance

    :raise RuntimeError: if the import from epsg_code failed

    """
    if osr is None:
        raise_import_exception("osr")

    sr = osr.SpatialReference()
    try:
        sr.ImportFromEPSG(int(epsg_code))
        return sr
    except RuntimeError:
        logger.exception(
            "[-] Importing projection from epsg code %s failed." % epsg_code
        )
        raise


def transform_bbox(bbox, source_epsg_code, target_epsg_code, all_coords=False):
    """
    Transform bbox from source_epsg_code to target_epsg_code,
    if necessary

    :returns np.array of shape 4 which represent the two coordinates:
        left, bottom and right, top.
        When `all_coords` is set to `True`, a np.array of shape 8 is given
        which represents coords of the bbox in the following order:
        left top, right top, right bottom, left bottom
    """
    if source_epsg_code != target_epsg_code:
        # XXX: Not entirely sure whether transformations between two projected
        # coordinate systems always do retain the rectangular shape of a bbox.
        # Transformations between an unprojected system (e.g. WGS84) and a
        # projected system (e.g. RDNEW) will experience distortion: the
        # resulting shape cannot be accurately represented by top left
        # and bottom right.
        source_srs = get_spatial_reference(source_epsg_code)
        target_srs = get_spatial_reference(target_epsg_code)
        if source_srs.IsProjected() != target_srs.IsProjected():
            msg = "Transforming a bbox from %s to %s is inaccurate."
            logger.warning(msg, source_epsg_code, target_epsg_code)
        # Transform to [[left, right],[top, bottom]]
        input_x = [bbox[BBOX_LEFT], bbox[BBOX_RIGHT]]
        input_y = [bbox[BBOX_TOP], bbox[BBOX_BOTTOM]]
        if all_coords:
            input_x += [bbox[BBOX_RIGHT], bbox[BBOX_LEFT]]
            input_y += [bbox[BBOX_TOP], bbox[BBOX_BOTTOM]]
        bbox_trans = np.array(
            transform_xys(
                np.array(input_x), np.array(input_y), source_epsg_code, target_epsg_code
            )
        )

        if all_coords:
            bbox = np.array(
                [
                    bbox_trans[0][0],
                    bbox_trans[1][0],  # left_top
                    bbox_trans[0][2],
                    bbox_trans[1][2],  # right_top
                    bbox_trans[0][1],
                    bbox_trans[1][1],  # right_bottom
                    bbox_trans[0][3],
                    bbox_trans[1][3],  # left_bottom
                ]
            )
        else:
            # Transform back to [left,bottom,right,top]
            bbox = np.array(
                [
                    min(bbox_trans[0]),
                    min(bbox_trans[1]),  # left_bottom
                    max(bbox_trans[0]),
                    max(bbox_trans[1]),  # right_top
                ]
            )
    return bbox


def get_bbox_for_tile(tile_xyz=(0, 0, 0), target_epsg_code="4326"):
    """
    Get the bbox for a tile defined by x,y,z in epsg=target_epsg_code

    :param tile_xyz: tuple with tile x,y,z
    :param target_epsg_code: the epsg_code to reproject the bbox to.

    :return: The bbox of the tile
             (reprojected to target_epsg_code if necessary)
             Numpy array: [left, top, right, bottom]
             y-axis is inverted: bottom >= top

    Examples:
    >>> get_bbox_for_tile((10, 10, 15))
    array([-179.89013672,   85.04069252, -179.87915039,   85.04164217])

    >>> get_bbox_for_tile((10, 10, 15), '28992')
    array([  212572.58551456,  5468921.2451706 ,   212705.73721283,
            5469031.60724307])
    """
    if mercantile is None:
        raise_import_exception("mercantile")
    bbox = np.array(
        mercantile.bounds(
            mercantile.Tile(x=int(tile_xyz[0]), y=int(tile_xyz[1]), z=int(tile_xyz[2]))
        )
    )

    if MERCANTILE_EPSG_CODE != target_epsg_code:
        bbox = transform_bbox(bbox, MERCANTILE_EPSG_CODE, target_epsg_code)

    return bbox


def select_points_by_bbox(points, bbox):
    """
    Return a boolean mask array for the points that are in bbox

    :param points: np.array [[x1, x2, x3...], [y1, y2, y3...]]
    :param bbox: np.array [left, top, right, bottom], bottom >= top
    :return: a boolean mask array with 'True' for the
             points that are in the bbox

    Example:
    >>> select_points_by_bbox(
    ...     points=np.array([[1, 10, 1, 10], [10, 10, 50, 50]]),
    ...     bbox=np.array([10, 10, 50, 50]))
    array([False,  True, False,  True], dtype=bool)

    >>> select_points_by_bbox(
    ...     points=np.array([[-11, 10, 10, -10], [10, 10, -11, -10]]),
    ...     bbox=np.array([-10, -10, 10, 10]))
    array([False,  True, False,  True], dtype=bool)

    >>> select_points_by_bbox(
    ...     points=np.array([[-11, 10, 10, -10], [10, 10, 0, -10]]),
    ...     bbox=np.array([-10, 0, 10, 10]))
    array([False,  True,  True, False], dtype=bool)

    >>> select_points_by_bbox(
    ...     points=np.array([[-1, 0, 0, 10], [0, 0, -11, -10]]),
    ...     bbox=np.array([0, -10, 10, 0]))
    array([False,  True, False,  True], dtype=bool)

    >>> select_points_by_bbox(
    ...     points=np.array([[100, -100], [110, -110]]),
    ...     bbox=np.array([0, -10, 10, 0]))
    array([False, False], dtype=bool)
    """
    lleft = np.array([bbox[BBOX_LEFT], bbox[BBOX_TOP]])  # lower-left
    uright = np.array([bbox[BBOX_RIGHT], bbox[BBOX_BOTTOM]])  # upper-right
    xy_points = points.T
    pre_sel_low = xy_points >= lleft
    pre_sel_up = xy_points <= uright
    return np.all((pre_sel_low & pre_sel_up), axis=1)


def select_points_by_tile(tile_xyz=(0, 0, 0), target_epsg_code="4326", points=None):
    """
    Select points by a tile

    :param tile_xyz: tuple with tile x,y,z
    :param target_epsg_code: the epsg_code to reproject the bbox to
            before selecting.
    :param points: (np.array) array [[x1, x2, x3...], [y1, y2, y3...]]
    :return: A boolean mask for the points within the tile_xyz bbox.

    Example:
    >>> select_points_by_tile((10, 10, 15),
    ...     '4326',
    ...     np.array([[-179.89013670, -179.89013670],
    ...               [  85.04069252,   85.04269252]]))
    array([ True, False], dtype=bool)
    """

    assert isinstance(points, np.ndarray)

    return select_points_by_bbox(points, get_bbox_for_tile(tile_xyz, target_epsg_code))


def select_lines_by_tile(
    tile_xyz=(0, 0, 0), target_epsg_code="4326", lines=None, include_intersections=False
):
    """
    Select lines by a tile

    :param tile_xyz: tuple with tile x,y,z
    :param target_epsg_code: the epsg_code to reproject the bbox to
            before selecting.
    :param lines: (np.array) array:
                    x1_array=lines[0], y1_array=lines[1],
                    x2_array=lines[2], y2_array=lines[3]
           line[i] = (x1[i], y1[i]) - (x2[i], y2[i])

    :return: The bbox of the tile
             (reprojected to target_epsg_code if necessary)
    """

    assert isinstance(lines, np.ndarray)

    return select_lines_by_bbox(
        lines, get_bbox_for_tile(tile_xyz, target_epsg_code), include_intersections
    )


def select_geoms_by_geometry(geoms, geometry):
    """Build an STRtree from geoms and returns indices into 'geoms'
    where geometry intersects.

    :param geoms: list of geometries you want to search from
    :param geometry: intersection geometry
    :return: ndarray of indices into 'geoms'
    """
    if shapely is None:
        raise_import_exception("shapely")

    if type(geometry) in (bytes, str):
        if isinstance(geometry, bytes):
            geometry = geometry.decode("utf-8")
        # assume wkt, try to load
        geometry = loads(geometry)

    tree = STRtree(geoms)
    # STRtree checks intersection based on bbox of the geometry only:
    # https://github.com/Toblerity/Shapely/issues/558

    if shapely.__version__.startswith("1."):
        result = []

        for i, g in enumerate(geoms):
            g.index = i

        for intersected_geom in tree.query(geometry):
            if geometry.intersects(intersected_geom):
                result.append(intersected_geom.index)
        return np.array(result, dtype=int)
    else:
        return tree.query(geometry, predicate="intersects")
