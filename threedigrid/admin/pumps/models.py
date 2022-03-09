# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

from threedigrid.orm.fields import ArrayField, LineArrayField, PointArrayField
from threedigrid.orm.models import Model


class Pumps(Model):
    display_name = ArrayField()
    content_pk = ArrayField()
    type = ArrayField()
    node1_id = ArrayField()
    node2_id = ArrayField()
    bottom_level = ArrayField()
    start_level = ArrayField()
    lower_stop_level = ArrayField()
    capacity = ArrayField()
    coordinates = PointArrayField()
    # coordinates is the centroid of
    # node_coordinates if both set, else
    # the one that is set.
    node_coordinates = LineArrayField()
    # [ [node1_x], [node1_y], [node2_x], [node2_y]]
    # Note: -9999 if nodeX_id is -9999 (not set)
    zoom_category = ArrayField()
