# -*- coding: utf-8 -*-

import pkg_resources
# Always try to import netCDF4.Dataset
# before importing h5py to prevent netCDF4
# HDF errors.
try:
    from netCDF4 import Dataset
except ImportError:
    pass

# from admin.gridadmin import GridH5Admin

try:
    __version__ = pkg_resources.get_distribution("threedigrid").version
except pkg_resources.DistributionNotFound:
    # for development environments
    __version__ = pkg_resources.find_distributions(
        '.', only=True).next().version