"""
Models
++++++

The ``Crosssections`` models represent the cross-sections as used in the
threedicore with shape, width and height information.


"""

from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import

from threedigrid.orm.models import Model
from threedigrid.orm.fields import ArrayField


class CrossSections(Model):
    code = ArrayField()
    shape = ArrayField()
    content_pk = ArrayField()
    width_1d = ArrayField()
    offset = ArrayField()
    count = ArrayField()
    tables = ArrayField()
