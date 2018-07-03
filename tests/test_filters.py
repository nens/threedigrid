from __future__ import absolute_import
import unittest

import numpy as np

from threedigrid.orm.base.filters import BaseFilter
from threedigrid.orm.base.filters import BaseCompareFilter
from threedigrid.orm.base.filters import EqualsFilter
from threedigrid.orm.base.filters import get_filter
from threedigrid.orm.base.filters import InFilter
from threedigrid.orm.filters import PointFilter
from threedigrid.orm.filters import FILTER_MAP

from threedigrid.orm.base.fields import ArrayField
from threedigrid.orm.fields import PolygonArrayField


class BasicFilterTests(unittest.TestCase):

    def setUp(self):
        self.field = ArrayField()

    def test_base_filter(self):
        b = BaseFilter()
        with self.assertRaises(NotImplementedError):
            b.filter('foo')

    def test_repr(self):
        f = BaseCompareFilter('in', self.field, [1, 2, 3])
        self.assertTrue(repr(f))

    def test_get_filter_eq(self):
        """Test that we get a default EqualsFilter without keys."""
        f = get_filter(['content_type'], self.field, 3)
        self.assertIsInstance(f, EqualsFilter)

        # also works when 'eq' is explicitly given
        f = get_filter(['content_type', 'eq'], self.field, 3)
        self.assertIsInstance(f, EqualsFilter)

    def test_eq_filter(self):
        f = EqualsFilter('content_type', self.field, np.array([1, 2]))
        filtered = f.filter({'content_type': np.array([1, 2])})
        self.assertTrue(filtered.all())

        filtered = f.filter({'content_type': np.array([1, 3])})
        self.assertFalse(filtered.all())

    def test_get_filter_in(self):
        f = get_filter(['content_pk', 'in'], self.field, [2])
        self.assertIsInstance(f, InFilter)

    def test_get_filter_error(self):
        """get_filter fails with malformed splitted keys."""
        with self.assertRaises(ValueError):
            get_filter(['content_pk', 'in', 'foo'], self.field, [2])

        with self.assertRaises(ValueError):
            get_filter([], self.field, [2])

    def test_get_nonexisting_filter(self):
        with self.assertRaises(ValueError):
            get_filter(['content_type', 'not_a_filter'], self.field, 3)


class PointFilterTests(unittest.TestCase):

    def setUp(self):
        self.field = PolygonArrayField()

    def test_get_point_filter(self):
        f = get_filter(
            ['cell_coords', 'contains_point'],
            self.field, [1, 5], filter_map=FILTER_MAP
        )
        self.assertIsInstance(f, PointFilter)

    def test_point_filter(self):
        f = PointFilter('coord_cells', self.field, np.array([1, 5]))
        filtered = f.filter(
            {'coord_cells': np.array([[0, 2], [0, 2], [6, 6], [10, 11]])}
        )
        self.assertTrue(filtered[0])
        self.assertFalse(filtered[1])
