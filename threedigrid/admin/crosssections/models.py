"""
Models
++++++

The ``Crosssections`` models represent the cross-sections as used in the
threedicore with shape, width and height information.


"""

from threedigrid.orm.fields import ArrayField
from threedigrid.orm.models import Model


class CrossSections(Model):
    code = ArrayField(type=int)
    shape = ArrayField(type=int)
    content_pk = ArrayField(type=int)
    width_1d = ArrayField(type=float)
    offset = ArrayField(type=float)
    count = ArrayField(type=float)
    tables = ArrayField(type=float)
