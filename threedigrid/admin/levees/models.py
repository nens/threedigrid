# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Models
++++++

The ``Levees`` model.
"""
from __future__ import unicode_literals
from __future__ import print_function

try:
    from osgeo import ogr
except ImportError:
    ogr = None

from threedigrid.numpy_utils import reshape_flat_array
from threedigrid.geo_utils import raise_import_exception
from threedigrid.orm.models import Model
from threedigrid.orm.fields import MultiLineArrayField
from threedigrid.orm.fields import ArrayField

from threedigrid.admin.levees import exporters


class Levees(Model):

    crest_level = ArrayField()
    max_breach_depth = ArrayField()
    coords = MultiLineArrayField()

    def __init__(self, *args,  **kwargs):
        super(Levees, self).__init__(*args, **kwargs)

        self._geoms = []
        self.current_epsg = None
        self._exporters = [
            exporters.LeveeOgrExporter(self),
        ]

    @property
    def geoms(self):
        if not self._geoms:
            self.load_geoms()
        return self._geoms

    def load_geoms(self):
        """
        load levee geometries originating
        from model DB
        """

        # works on premise of ogr install
        if ogr is None:
            raise_import_exception('ogr')

        if self._geoms:
            return
        for line_coords in self.coords:
            line = ogr.Geometry(ogr.wkbLineString)
            linepoints = reshape_flat_array(line_coords).T
            for x in linepoints:
                line.AddPoint(x[0], x[1])
            self._geoms.append(line)
