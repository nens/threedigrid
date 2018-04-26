History
=======

0.2 (2018-04-26)
----------------

- Added additional exporters for

    - 2D_GROUNDWATER
    - 2D_OPEN_WATER
    - 2D_VERTICAL_INFILTRATION

- Added method ``get_model_instance_by_field_name``  to the
  ``GridH5ResultAdmin`` class. This makes it possible to do reverse lookups
  in situations where you have a field name but do not know which model it
  belongs to. N.B the field must be unique otherwise an ``IndexError`` will
  be raised.

- Added property ``dt_timestamps`` to the timeseries_mixin module.

- The version number is added to the ``__init__`` file dynamically using the
  ``pkg_resources`` API.

- Timestamps of all timeseries fields are shown for aggregation results.

- Timestamps in the aggregation results are filtered when retrieving subsets of timeseries.

- Introducing the ModelMeta class. Its main purpose at this moment is to compute all 
  possible combinations of composite_fields and aggregation variables.

- Fixed return statement of method slice (in class Model) which now takes 
  ``**new_class_kwargs``. 
  
- Empty or missing datasets are now displayed as ``np.array(None)`` instead of 
  raising an error.

0.1.6 (2018-04-18)
------------------

- New release using twine 1.11.


0.1.5 (2018-04-18)
------------------

- Added support for composite fields which can be used to fetch data from
  multiple source variables as a single field. Like this
  result_3di netcdfs can be queried the same way as gridadmin files.

0.1.4 (2018-04-08)
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
