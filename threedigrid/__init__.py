# -*- coding: utf-8 -*-

# Always try to import netCDF4.Dataset
# before importing h5py to prevent netCDF4 
# HDF errors.
try:
    from netCDF4 import Dataset
except ImportError:
    pass

from admin.gridadmin import GridH5Admin

__version__ = '0.1.4.dev0'