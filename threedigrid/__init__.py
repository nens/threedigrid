# -*- coding: utf-8 -*-

from __future__ import absolute_import

# Always try to import netCDF4.Dataset before importing
# h5py to prevent netCDF4 HDF errors.
try:
    from netCDF4 import Dataset  # noqa
except ImportError:
    pass

# Threedigrid version number is automatic updated with zest.releaser
# the version number in setup.py is updated using the find_version()
__version__ = '1.1.dev0'
