History
=======

1.0.25 (2020-09-15)
-------------------

- Bugfix: crest_level is also inverted by Inpy. Use
  the raw value in the prepare step to include the
  correct (non inverted) value.


1.0.24 (2020-09-02)
-------------------

- Removed numba as dependency, since it did not really give any
  performance gain on Linux.


1.0.23 (2020-09-02)
-------------------

- Creating fresh release after upload failed.


1.0.22 (2020-09-02)
-------------------

- Added extra field 'discharge_coefficient' to channels and pipes. These
  fields default to 1.0.

- Bugfix: don't use the z-coordinate when making line_geometries during the prepare step


1.0.21 (2020-07-17)
-------------------

- Invert_level_start_point and end point where inverted
  by Inpy. After this change the values will be correct again,
  however present gridadmin files will still have the incorrect value.

- Added `Breaches` model under lines with specific breach fields
  mapped from the 'breaches' h5py datagroup.

- Added `MappedSubsetArrayField` allowing to map arrays from other
  h5py datagroups to a model on another datagroup subset. Breaches
  uses this to map the array's under 'breaches' to 'lines'


1.0.20.12 (2020-07-14)
----------------------

- Fixed problem with previous release


1.0.20.11 (2020-07-14)
----------------------

- Nodgrid generation bugfixes


1.0.20.10 (2020-07-07)
----------------------

- Added missing numba requirement in setup.py


1.0.20.9 (2020-07-07)
---------------------

- Fixed RPC breaches/pumps bug

- Added fast nod_grid generation on cells


1.0.20.8 (2020-05-22)
---------------------

- Add groundwater_cells to exporter for frontend.


1.0.20.7 (2020-05-18)
---------------------

- Added `content_pk` to the export_constants of all structures which have a
  `content_pk`.


1.0.20.6 (2020-04-15)
---------------------

- An empy array [] is returned now instead of None if there is no
  dataset.

- Line geojson items need to use line_geometry values

- Bugfix for `Model._get_subset_idx` not instantiating new subsets with their parent's
  mixins.


1.0.20.5 (2020-04-01)
---------------------

- Use 'ga.xxx.id.size' to check if certain submodels (like channels/weirs/manholes)
  are available for geojson exports.


1.0.20.4 (2020-03-31)
---------------------

- Allow older pyrpoj versions. (pre 2.2.0)

- Bugfix for timeseries start_time=0 selection and allow indexes=slice(x,x,x)
  in combination with sample() method.

- Added try-except surrounding all imports of the package `geojson`. This package is
  only available when threedigrid is installed with the extra [geo] extension.

- Add `ORIFICES_EXPORT_FIELDS` to export_constants.


1.0.20.3 (2020-03-18)
---------------------

- Add extra field `pixel_width` to cells

- Bugfix for GeometryIntersectionFilter: filter was only checking on
  intersecting bounding boxes


1.0.20.2 (2020-03-06)
---------------------

- The `sample` method needs to skip the last timestamp for SWMR
  to work correctly. (time dataset can have one item more
  than datasets with timeseries)

1.0.20.1 (2020-02-26)
---------------------

- Bugfix: reprojection with no coordinates (empty array's)


1.0.20 (2020-02-19)
-------------------

- Added `GeometryIntersectionFilter`.

- Added general GeoJsonSerializer which allows you to specify the field names
  you want to serialize and extract to geojson. The GeoJsonSerializer allows
  you to specify nested fields.

- Added a set of standard export fields for each model.

- Automatically pick the correct serializer based on file extention

    - .json/.geojson --> to_geojson
    - .gpgk --> to_geopackage
    - .shp --> to_shape

1.0.19.1 (2020-02-04)
---------------------

- Minor bugfix, need to check if h5py filepath is a str or bytes string
  during initialization


1.0.19 (2020-01-31)
-------------------

- First release with RPC integration.


1.0.19rc3 (2020-01-14)
----------------------

- Bumped version of asyncio-rpc


1.0.19rc2 (2020-01-14)
----------------------

- Fixed incorrect version number


1.0.19rc1 (2020-01-14)
----------------------

- Added RPC datasource which enables to use the majority of
  threedigrid in a RPC setting. Uses asyncio-rpc for
  sending/handling RPC calls.

- RPC datasource allows both one time executing (`resolve()`) and pub/sub
  (`subscribe()`) functionialty.

- Refactored to allow using RPC datasource

1.0.18 (2019-11-28)
-------------------

- Only use pyproj Transformer if it is present
  else revert to old transform method


1.0.17 (2019-11-28)
-------------------

- Added `content_pk` to the pumps model.

- Bumped package versions

- Reduced reprojection overhead of line_geometries.


1.0.16 (2019-07-08)
-------------------

- Removed max capacity from Orifice model/serializer.


1.0.15 (2019-07-05)
-------------------

- Fixed group update for default null values.


1.0.14 (2019-06-19)
-------------------

- Do not use ``0`` has a default when converting database objects to numpy
  arrays in the prepare phase.


1.0.13 (2019-05-01)
-------------------

- Fixed `_field_model_dict` being a class variable.


1.0.12 (2019-04-18)
-------------------

- Added sumax to nodes


1.0.11 (2019-02-01)
-------------------

- Bug fix in `h5py_file` method mapping.


1.0.10 (2019-01-31)
-------------------

- Added sources and sinks (q_sss) to threedigrid.


1.0.9 (2019-01-31)
------------------

- Manholes preparation fixed mapping in ``connection_node_pk``.

- Added `to_structured_array` method for retrieving (filtered) results
  as Numpy structured array instead of an OrderedDict


1.0.8 (2019-01-03)
------------------

- Set fixed type to the fields `code`, `display_name` and `shape`. These fields
  now have a fixed lenght of 32, 64 and 4 characters respectively.


1.0.7 (2018-11-21)
------------------

- Bug fix: dict.values() and dict.keys() in python 3 are causing some
  unintended behaviour.


1.0.6 (2018-11-14)
------------------

- New release due to failing uploads.


1.0.5 (2018-11-14)
------------------

- Add aggregation option 'current' to volume and intercepted_volume.

- Using a non-tuple sequence for multidimensional indexing is deprecated; use
  `arr[tuple(seq)]` instead of `arr[seq]`.

- Properties should be strings so we can use string methods on them.

- Do not prepare levees if there aren't any.

- Split requirements file to allow for finer grained builds (for instance to
  generate the documentation).

- Add 'intercepted_volume' to NodesAggregateResultsMixin.

- Split requirements file to allow for finer grained builds (for instance to
  generate the documentation).


1.0.4 (2018-10-17)
------------------

- Added BooleanArrayField for boolean values and use it for `is_manhole` filter.
  NO_DATA_VALUE is interpreted as False.


1.0.3 (2018-09-17)
------------------

- Do not throw exception on cftime ``ImportError``


1.0.2 (2018-09-17)
------------------

- Add boolean filter for manholes.


1.0.1 (2018-09-11)
------------------

- Patch for converting numpy strings/bytes to float for both python2/3.

- Dropped NetCDF library and replaced opening NetCDF files with h5py

- Bumped h5py to 2.8.0


1.0 (2018-09-04)
----------------

- Made threedigrid >= Python 3.5 compatible.


0.2.8 (2018-07-23)
------------------

- Bug fix for issue #44: use the method ``get_filtered_field_value()`` instead
  of ``get_field_value()`` for the count property.

- Properly closes netcdf-file in ``GridH5ResultAdmin``.


0.2.7 (2018-05-24)
------------------

- Add export functions for 2D to the ``export_all()`` collection.


0.2.6 (2018-05-17)
------------------

- Do not use ``pkg_resources`` to determine the current version but use
  zest_releaser to update the version string in threedigrid/init.py


0.2.5 (2018-05-16)
------------------

- Use the custom ``NumpyEncoder`` to convert specific numpy types to native
  python types when calling ``(geo-)json.dumps()``.


0.2.4 (2018-05-15)
------------------

- Introducing subset fields that can be used to query results that are collected
  only for subsets of the model, like the 2D section.


0.2.3 (2018-05-14)
------------------

- Fix lookup_index functionality for composite fields.

- Make model name property optional. That is, 'unknown' will be returned if the
  name cannot be derived.

- Changed Depth/width fields on breach-timeseries to breach_depth and breach_width.

0.2.2 (2018-04-30)
------------------

- ``_get_composite_meta()`` does not raise an AssertionError anymore if
  composite field attributes differ. Instead a warning is issued.


0.2.1 (2018-04-26)
------------------

- Bug fix: ``threedicore_result_version`` must be a property.


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
