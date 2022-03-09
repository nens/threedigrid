# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.


class NotConsistentException(Exception):
    """Is raises when data is not consistent"""

    pass


class DriverNotSupportedError(BaseException):
    """Will be raised when trying export with an
    unknown/unsupported ogr driver"""

    pass


class OperationNotSupportedError(BaseException):
    """Will be raised when an user operation
    could result in ambiguous results"""

    pass
