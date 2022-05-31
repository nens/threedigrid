# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from threedigrid.orm.fields import ArrayField, LineArrayField, PointArrayField
from threedigrid.orm.models import Model


class Pumps(Model):
    display_name = ArrayField(type=str)
    content_pk = ArrayField(type=int)
    type = ArrayField(type=int)
    node1_id = ArrayField(type=int)
    node2_id = ArrayField(type=int)
    bottom_level = ArrayField(type=float)
    start_level = ArrayField(type=float)
    lower_stop_level = ArrayField(type=float)
    capacity = ArrayField(type=float)
    coordinates = PointArrayField()
    # coordinates is the centroid of
    # node_coordinates if both set, else
    # the one that is set.
    node_coordinates = LineArrayField()
    # [ [node1_x], [node1_y], [node2_x], [node2_y]]
    # Note: -9999 if nodeX_id is -9999 (not set)
    zoom_category = ArrayField(type=int)

    GPKG_DEFAULT_FIELD_MAP = {
        "id": "id",
        "display_name": "display_name",
        "node1_id": "calculation_node_id_start",
        "node2_id": "calculation_node_id_end",
        "content_pk": "source_table_id",
        "type": "type",
        "bottom_level": "bottom_level",
        "start_level": "start_level",
        "lower_stop_level": "lower_stop_level",
        # "start_level": "upper_stop_level",
        "capacity": "capacity",
        "coordinates": "the_geom",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
