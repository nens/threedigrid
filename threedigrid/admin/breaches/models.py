# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from threedigrid.admin.breaches import exporters
from threedigrid.admin import constants
from threedigrid.orm.models import Model
from threedigrid.orm.fields import (
    ArrayField, PointArrayField)
from threedigrid.orm.base.fields import IndexArrayField


class Breaches(Model):
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
