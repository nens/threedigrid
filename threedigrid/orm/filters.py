# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function


from __future__ import absolute_import
from threedigrid.orm.base.filters import BaseFilter
from threedigrid.orm.base.filters import FILTER_MAP as BASE_FILTER_MAP


class GeomFilter(BaseFilter):
    def to_dict(self):
        return {
            'filter': {
                "{0}__{1}".format(
                    self.key, self.func_name): self.values
            }
        }


class BboxFilter(GeomFilter):
    """
    Bbox (geom) filter
    """
    include_intersections = False
    func_name = 'in_bbox'

    def __init__(self, key, field, values, filter_as=False):
        self.field = field
        self.key = key
        self.bbox = values
        self.values = values
        self._filter_as = filter_as
        assert hasattr(self.field, 'get_mask_by_bbox')

    def get_field_name(self):
        return self.key

    def filter(self, nparray_dict):
        return self.field.get_mask_by_bbox(
            self.bbox, nparray_dict[self.key][:],
            self.include_intersections)

    def filter_dict(self, nparray_dict, model_instance):
        """
        Filter the values in nparray_dict dictionairy by
        the filter defined in self.filter()

        :param nparray_dict:  dictionairy of np_array's.
        :param target_epsg_code: epsg_code of instance (ignored for bbox)
        """
        # Get the filter
        base_filter = self.filter(nparray_dict)
        self._do_filter(base_filter, nparray_dict)


class PointFilter(GeomFilter):
    func_name = 'contains_point'

    def __init__(self, key, field, values, filter_as=False):
        self.field = field
        self.key = key
        self.x, self.y = values
        self.values = values
        self._filter_as = filter_as
        assert hasattr(self.field, 'get_mask_by_point')

    def get_field_name(self):
        return self.key

    def filter(self, nparray_dict):
        return self.field.get_mask_by_point(
            (self.x, self.y), nparray_dict[self.key][:]
        )

    def filter_dict(self, nparray_dict, model_instance):
        """
        Filter the values in nparray_dict dictionairy by
        the filter defined in self.filter()

        :param nparray_dict:  dictionairy of np_array's.
        :param target_epsg_code: epsg_code of instance
        """
        # Get the filter
        base_filter = self.filter(nparray_dict)
        self._do_filter(base_filter, nparray_dict)


class TileFilter(GeomFilter):
    """
    Tile (geom) filter
    """
    include_intersections = False
    func_name = 'in_tile'

    def __init__(self, key, field, values, filter_as=False):
        self.field = field
        self.key = key
        self.x, self.y, self.z = values
        self.values = values
        self._filter_as = filter_as
        assert hasattr(self.field, 'get_mask_by_tile')

    def get_field_name(self):
        return self.key

    def filter(self, nparray_dict, target_epsg_code):
        return self.field.get_mask_by_tile(
            (int(self.x), int(self.y), int(self.z)),
            target_epsg_code, nparray_dict[self.key][:],
            self.include_intersections)

    def filter_dict(self, nparray_dict, model_instance):
        """
        Filter the values in nparray_dict dictionairy by
        the filter defined in self.filter()

        :param nparray_dict:  dictionairy of np_array's.
        :param target_epsg_code: epsg_code of instance
        """
        # Get the filter
        base_filter = self.filter(nparray_dict, model_instance.epsg_code)
        self._do_filter(base_filter, nparray_dict)


class BboxIntersectsFilter(BboxFilter):
    include_intersections = True
    func_name = 'intersects_bbox'


class TileIntersectsFilter(TileFilter):
    include_intersections = True
    func_name = 'intersects_tile'


class GeometryIntersectionFilter(GeomFilter):
    func_name = 'intersects_geometry'

    def __init__(self, key, field, values, filter_as=False):
        self.field = field
        self.key = key
        self.geometry = values
        self.values = values
        # geom is Shapely.geometry
        self._filter_as = filter_as
        assert hasattr(self.field, 'get_mask_by_geometry')

    def get_field_name(self):
        return self.key

    def filter(self, nparray_dict):
        return self.field.get_mask_by_geometry(
            self.geometry, nparray_dict[self.key][:],
        )

    def filter_dict(self, nparray_dict, model_instance):
        """
        Filter the values in nparray_dict dictionairy by
        the filter defined in self.filter()

        :param nparray_dict: dictionairy of np_array's.
        :param model_instance: epsg_code of instance (ignored)
        """
        # Get the filter
        base_filter = self.filter(nparray_dict)
        self._do_filter(base_filter, nparray_dict)


FILTER_MAP = dict(BASE_FILTER_MAP, ** {
    'in_tile': TileFilter,
    'in_bbox': BboxFilter,
    'contains_point': PointFilter,
    'intersects_tile': TileIntersectsFilter,
    'intersects_bbox': BboxIntersectsFilter,
    'intersects_geometry': GeometryIntersectionFilter}
)
