"""
Models
++++++

The ``Crosssections`` models represent the cross-sections as used in the
threedicore with shape, width and height information.


"""


from threedigrid.orm.fields import ArrayField
from threedigrid.orm.models import Model


class CrossSections(Model):
    code = ArrayField()
    shape = ArrayField()
    content_pk = ArrayField()
    width_1d = ArrayField()
    offset = ArrayField()
    count = ArrayField()
    tables = ArrayField()
