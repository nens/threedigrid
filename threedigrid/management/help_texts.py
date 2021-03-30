# -*- coding: utf-8 -*-
"""help text functions for threedigrid management commands"""
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from collections import OrderedDict

from threedigrid.admin.gridadmin import GridH5Admin
import six


def model_overview(grid_file):
    """

    :param grid_file: path to hdf5 grid file
    :returns formatted string like so::

        threedicore version:     0-20180219-587b996-1
        has 1d:                  True
        has 2d:                  True
        has groundwater:         False
        has levees:              True
    """

    grid = GridH5Admin(grid_file)
    _attrs = OrderedDict([
        ('model_slug', ''),
        ('threedicore_version', ''),
        ('threedi_version', ''),
        ('has_1d', ''),
        ('has_2d', ''),
        ('has_groundwater', ''),
        ('has_levees', ''),
        ('has_breaches', ''),
        ('has_pumpstations', ''),
    ])

    for k in six.iterkeys(_attrs):
        if not hasattr(grid, k):
            continue
        attr = getattr(grid, k)
        if attr is None:
            continue
        _attrs[k] = '{:24} {}'.format(k.replace('_', ' ') + ':', attr)

    return '\n'.join((v for v in _attrs.values() if v != '')) + '\n'
