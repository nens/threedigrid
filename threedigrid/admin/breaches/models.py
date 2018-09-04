# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
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

from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
from threedigrid.admin.breaches import exporters
from threedigrid.admin import constants
from threedigrid.orm.models import Model
from threedigrid.orm.fields import (
    ArrayField, PointArrayField)
from threedigrid.orm.base.fields import IndexArrayField


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
    content_pk = ArrayField()
    seq_ids = ArrayField()
    levbr = ArrayField()
    levl = IndexArrayField(to='Lines')
    levmat = ArrayField()
    kcu = ArrayField()

    coordinates = PointArrayField()

    OBJECT_TYPE = constants.TYPE_V2_BREACH

    def __init__(self, *args, **kwargs):
        super(Breaches, self).__init__(*args, **kwargs)

        self._exporters = [
            exporters.BreachesOgrExporter(self),
        ]
