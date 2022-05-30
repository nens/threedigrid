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
from threedigrid.orm.base.fields import IndexArrayField
from threedigrid.orm.fields import ArrayField, PointArrayField
from threedigrid.orm.models import Model

logger = logging.getLogger(__name__)


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

    """

    content_pk = ArrayField(type=int)
    seq_ids = ArrayField(type=int)
    levbr = ArrayField(type=float)
    levl = IndexArrayField(to="Lines")
    levmat = ArrayField(type=int)
    kcu = ArrayField(type=int)

    coordinates = PointArrayField()

    OBJECT_TYPE = constants.TYPE_V2_BREACH

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._exporters = [
            exporters.BreachesOgrExporter(self),
        ]
