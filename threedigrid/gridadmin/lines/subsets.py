# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

KCU__IN_SUBSETS = {
    '1D': [0, 1, 2, 3, 4, 5],
    '1D2D': [51, 52, 53, 54, 55, 56, 57, 58],
    '2D_OPEN_WATER': [100, 101, 200, 300, 400, 500],
    'LONG_CRESTED_STRUCTURES': [3],
    'SHORT_CRESTED_STRUCTURES': [4],
    '2D_OPEN_WATER_OBSTACLES': [101],
    '2D_VERTICAL_INFILTRATION': [150],
    '2D_GROUNDWATER': [-150],
    'ACTIVE_BREACH': [56],
}

KCU__IN_SUBSETS['1D_ALL'] = KCU__IN_SUBSETS['1D'] + KCU__IN_SUBSETS['1D2D']
KCU__IN_SUBSETS['GROUNDWATER_ALL'] = (
    KCU__IN_SUBSETS['2D_GROUNDWATER'] + KCU__IN_SUBSETS[
        '2D_VERTICAL_INFILTRATION']
)
KCU__IN_SUBSETS['2D_ALL'] = (
    KCU__IN_SUBSETS['GROUNDWATER_ALL'] +
    KCU__IN_SUBSETS['2D_OPEN_WATER_OBSTACLES'] +
    KCU__IN_SUBSETS['2D_OPEN_WATER']
)
