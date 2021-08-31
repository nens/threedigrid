# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

NODE_TYPE__EQ_SUBSETS = {
    '2D_OPEN_WATER': 1,
    '2D_GROUNDWATER': 2,
    '1D_NO_STORAGE': 3,
    '1D_STORAGE': 4,
    '2D_BOUNDARIES': 5,
    '2D_GROUNDWATER_BOUNDARIES': 6,
    '1D_BOUNDARIES': 7,
}

NODE_TYPE__IN_SUBSETS = dict()
NODE_TYPE__IN_SUBSETS['1D'] = [
    NODE_TYPE__EQ_SUBSETS['1D_NO_STORAGE'],
    NODE_TYPE__EQ_SUBSETS['1D_STORAGE'],
]

NODE_TYPE__IN_SUBSETS['1D_ALL'] = [
    NODE_TYPE__EQ_SUBSETS['1D_NO_STORAGE'],
    NODE_TYPE__EQ_SUBSETS['1D_STORAGE'],
    NODE_TYPE__EQ_SUBSETS['1D_BOUNDARIES']
]

NODE_TYPE__IN_SUBSETS['GROUNDWATER_ALL'] = [
        NODE_TYPE__EQ_SUBSETS['2D_GROUNDWATER'],
        NODE_TYPE__EQ_SUBSETS['2D_GROUNDWATER_BOUNDARIES']
]

NODE_TYPE__IN_SUBSETS['2D_ALL'] = [
    NODE_TYPE__EQ_SUBSETS['2D_GROUNDWATER'],
    NODE_TYPE__EQ_SUBSETS['2D_GROUNDWATER_BOUNDARIES'],
    NODE_TYPE__EQ_SUBSETS['2D_BOUNDARIES'],
    NODE_TYPE__EQ_SUBSETS['2D_OPEN_WATER']
]
