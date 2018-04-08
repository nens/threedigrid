History
=======

0.1.4 (unreleased)
------------------

- Changed ResultMixin to dynamically add attributes based on the netcdf
  variables.

- Added basic result proccesing for line/node data.

- The filter mask is computed only for array's affected and
  before applying it to all array's

- The 'only' filter works much faster because the filter mask
  is only applied on fields that are affected.

- The filter mask is cached on the line/node instance after getting
  the first value. You can thus do something like:

      queryset = gridadmin.lines.filter(kcu=2)
      ids = queryset.id
      line_coords = queryset.line_coords

  and the filter mask will only be computed once.

- Add click console scripts ``3digrid_explore`` and ``3digrid_export`` for
  quick overviews and data exports.

- Make ogr/gdal imports optional to avoid breaking parts of the documentation.

- Added documentation and setup for ``sphinx`` documentation pipeline.

- Use linear referencing for embedded channels to keep the original geometry
  intact when preparing line geometries for visualisation.

- Define extra's to make the standard threedigrid distribution as
  lightweight as possible.

- Convert strings in ``attrs`` to ``numpy.string_`` to fix crashes under
  Windows.

0.1.3 (2018-03-16)
------------------

- Remove property ``has_groundwater`` from ``GridH5Admin``.
  Should always be provided by the threedicore itself. Gives a warning for
  backwards compatibility.


0.1.2 (2018-03-12)
------------------

- Get model extent now always returns a bbox (minX, minY, maxX, maxY)

0.1.1 (2018-03-06)
------------------

- All imports are absolute.

- Added install info using pip.


0.1.0 (2018-03-05)
------------------

* First release with fullrelease.
