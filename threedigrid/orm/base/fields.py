# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function


class ArrayField:
    """
    Generic field that can be used to describe values
    to be retrieved from a Datasource.
    """
    @staticmethod
    def get_value(datasource, name):
        """
        Returns: the data from the datasource
                 or None if 'name' is not in the datasource

        Optional transforms can be done here.
        """
        if name in datasource.keys():
            return datasource[name]

        return None


class IndexArrayField(ArrayField):
    def __init__(self, to=None):
        self.to = to
