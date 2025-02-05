from threedigrid.admin.fragments import exporters
from threedigrid.orm.fields import ArrayField, PolygonArrayField
from threedigrid.orm.models import Model


class Fragments(Model):

    node_id = ArrayField(type=int)
    coords = PolygonArrayField()

    GPKG_DEFAULT_FIELD_MAP = {
        "id": "id",
        "node_id": "node_id",
        "coords": "the_geom",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._exporters = [
            exporters.FragmentsOgrExporter(self),
        ]
