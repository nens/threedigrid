"""
Models
++++++

The ``Crosssections`` models represent the cross-sections as used in the
threedicore with shape, width and height information.


"""
from enum import IntEnum, unique

from threedigrid.orm.fields import ArrayField
from threedigrid.orm.models import Model


@unique
class CrossSectionShape(IntEnum):
    CLOSED_RECTANGLE = 0
    RECTANGLE = 1
    CIRCLE = 2
    EGG = 3
    TABULATED_RECTANGLE = 5
    TABULATED_TRAPEZIUM = 6
    TABULATED_YZ = 7
    INVERTED_EGG = 8


class CrossSections(Model):
    code = ArrayField(type=int)
    shape = ArrayField(type=int)
    content_pk = ArrayField(type=int)
    width_1d = ArrayField(type=float)
    offset = ArrayField(type=float)
    count = ArrayField(type=float)
    tables = ArrayField(type=float)
    offset_yz = ArrayField(type=float)
    count_yz = ArrayField(type=float)
    tables_yz = ArrayField(type=float)

    def get_tabulated_cross_section_height_and_width(self, cross_section_pk):
        """
        Returns the heights and widths of a cross-section.

        Args:
            cross_section_pk: (int) the cross-section primary key

        Returns:
            (tuple([heights], [widths])) the heights and widths of the cross-section
        """

        if self.shape[cross_section_pk] == CrossSectionShape.TABULATED_YZ:
            offset = self.offset_yz[cross_section_pk]
            count = self.count_yz[cross_section_pk]
            table = self.tables_yz
        else:
            offset = self.offset[cross_section_pk]
            count = self.count[cross_section_pk]
            table = self.tables

        return (
            table[1, offset : offset + count],
            table[0, offset : offset + count],
        )
