# -*- coding: utf-8 -*-

# Always try to import netCDF4.Dataset
# before importing h5py
try:
    from netCDF4 import Dataset
except ImportError:
    pass


from admin.gridadmin import GridH5Admin
