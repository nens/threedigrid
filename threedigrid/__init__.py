# -*- coding: utf-8 -*-


# Always try to import netCDF4.Dataset
# before importing h5py to prevent netCDF4
# HDF errors.
try:
    from netCDF4 import Dataset
except ImportError:
    pass

# Threedigrid version number is automatic updated with zest.releaser
# the version number in setup.py is updated using the find_version()
__version__ = '0.2.6'
