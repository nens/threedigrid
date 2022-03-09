# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.

import json

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """
    convert specific numpy types to native python types
    """

    def default(self, obj):
        """
        overwrites the default method. Numpy integers and floats will be
        converted to native python types, numpy.ndarrays to python lists
        :param obj: object to encode
        :return: encoded object
        """
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, bytes):
            return obj.decode("utf-8")
        else:
            return super().default(obj)
