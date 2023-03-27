# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
Models
++++++

Breaches are better described as possible breach locations
as they represent the intersection between threedicore
1d-2d flow lines and levee geometries from the models spatialite
database. That is, once the kcu (the type classifier, see :ref:`kcu-label`)
of the 1d-2d flow line has the value 56 there actually will be an active
link between the 1d and the 2d calculation nodes.

To query the ``Breaches`` model::

    >>> from threedigrid.admin.breaches.models import Breaches
    >>> from threedigrid.admin.gridadmin import GridH5Admin

    >>> f = 'gridadmin.h5'
    >>> ga = GridH5Admin(f)
    >>> # get all active breaches
    >>> ga.breaches.filter(kcu__eq=56).data

"""

import logging

from threedigrid.admin import constants
from threedigrid.admin.breaches import exporters
from threedigrid.admin.utils import PKMapper
from threedigrid.orm.base.fields import IndexArrayField
from threedigrid.orm.fields import ArrayField, MultiLineArrayField, PointArrayField
from threedigrid.orm.models import Model

logger = logging.getLogger(__name__)


class LineGeometries(MultiLineArrayField):
    """
    Used for setting `line_geometries` (field in 'lines' h5 group) on the
    Breaches model.
    """

    def __init__(self):
        super().__init__(None)

    def get_value(self, datasource, name, **kwargs):
        if name in list(datasource.keys()):
            return datasource[name]

        if datasource._gridadmin is not None:
            # Return mapped line_coords, based on levl
            levl = datasource["levl"][:]
            data = datasource._gridadmin.lines.filter(id__in=levl).only(
                "id", "line_geometries"
            )
            return PKMapper(data.id, levl).apply_on(data.line_geometries)

        return ArrayField.get_value(datasource, name)


class Breaches(Model):
    """
    fields originating from threedicore:

        - levbr (breach width)
        - levmat (material code)
        - levl (exchange level)
        - kcu (type field 55 or 56)

    added fields from spatialite database:

        - content_pk (primary key database)
        - seq_ids (sequence ids generated during input file generation)

    fields from `lines` h5 group:

        - line_geometries
    """

    content_pk = ArrayField(type=int)
    seq_ids = ArrayField(type=int)
    levbr = ArrayField(type=float)
    levl = IndexArrayField(to="Lines")
    levmat = ArrayField(type=int)
    kcu = ArrayField(type=int)
    line_geometries = LineGeometries()
    coordinates = PointArrayField()
    code = ArrayField(type=str)
    display_name = ArrayField(type=str)

    OBJECT_TYPE = constants.TYPE_V2_BREACH

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._exporters = [
            exporters.BreachesOgrExporter(self),
        ]
