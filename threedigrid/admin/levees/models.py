# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
Models
++++++

The ``Levees`` model.
"""

try:
    from osgeo import ogr
except ImportError:
    ogr = None

from threedigrid.admin.levees import exporters
from threedigrid.geo_utils import raise_import_exception
from threedigrid.numpy_utils import reshape_flat_array
from threedigrid.orm.fields import ArrayField, MultiLineArrayField
from threedigrid.orm.models import Model


class Levees(Model):
    crest_level = ArrayField(type=float)
    max_breach_depth = ArrayField(type=float)
    coords = MultiLineArrayField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            raise_import_exception("ogr")

        if self._geoms:
            return
        for line_coords in self.coords:
            line = ogr.Geometry(ogr.wkbLineString)
            linepoints = reshape_flat_array(line_coords).T
            for x in linepoints:
                line.AddPoint(x[0], x[1])
            self._geoms.append(line)
