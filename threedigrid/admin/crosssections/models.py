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

    def get_tabulated_cross_section_width_and_height(self, cross_section_pk):
        """
        Returns the width and height of a cross-section.

        Args:
            cross_section_pk: (int) the cross-section primary key

        Returns:
            (tuple) the width and height of the cross-section
        """
        offset = self.offset[cross_section_pk]
        count = self.count[cross_section_pk]
        return (
            self.tables[1, offset : offset + count],
            self.tables[0, offset : offset + count],
        )
