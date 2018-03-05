# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function


class NotConsistentException(Exception):
    """Is raises when data is not consistent"""
    pass


class DriverNotSupportedError(BaseException):
    """Will be raised when trying export with an
    unknown/unsupported ogr driver"""
    pass


class OperationNotSupportedError(BaseException):
    """Will be raised when an user operation
    could result in ambiguous results """
    pass
