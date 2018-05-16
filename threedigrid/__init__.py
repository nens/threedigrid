# -*- coding: utf-8 -*-

# Always try to import netCDF4.Dataset
# before importing h5py to prevent netCDF4
# HDF errors.
try:
    from netCDF4 import Dataset
except ImportError:
    pass

__version__ = '0.2.6.dev0'
