from threedigrid.admin.fragments import exporters
from threedigrid.orm.fields import ArrayField, PolygonArrayField
from threedigrid.orm.models import Model


class Fragments(Model):

    node_id = ArrayField(type=int)
    coords = PolygonArrayField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._exporters = [
            exporters.FragmentsOgrExporter(self),
        ]
