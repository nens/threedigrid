Functionalities
===============

.. todo::
    Include inheritance diagrams: https://www.sphinx-doc.org/en/master/usage/extensions/inheritance.html

.. _threedimodel_components:

Accessing 3Di model components
------------------------------

``threedigrid`` uses a limited number of main classes to access 3Di model components: 

- :ref:`breaches`
- :ref:`crosssections`
- :ref:`grid`
- :ref:`levees`
- :ref:`lines`
- :ref:`nodes`

The :ref:`lines` and :ref:`nodes` classes have several child classes (e.g. :ref:`manholes` or :ref:`weirs`) that allow access to attributes specific to those 3Di model components.

``Breaches``, ``Nodes``, ``Lines``, and ``Pumps`` have time series connected to them through the :ref:`GridH5ResultAdmin<results3di>`, :ref:`GridH5AggregateResultAdmin<aggregate_results3di>`, or :ref:`GridH5WaterQualityResultAdmin<wq_results3di>`.

Filters and subsets
-------------------

To make selections of data, you can use :ref:`spatial_filters`, :ref:`non_spatial_filters`, :ref:`subsets`, and :ref:`only`. You can chain these in any way you like. The example below returns all 1D nodes with a storage area >= 1.0 within a specific area.

.. code:: python

    ga.nodes.subset("1D_ALL").filter(storage_area__gte=1.0).filter(coordinates__intersects_geometry=my_polygon)

The filters and subsets are 'lazy', i.e. they are not executed until data is retrieved. To retrieve data you have to call ``data`` or ``timeseries()`` explicitly:

.. code-block:: python

    ga.nodes.filter(node_type__eq=5)  # will not return all data
    ga.nodes.filter(node_type__eq=5).data  # returns all data as an OrderedDict
    gr.nodes.timeseries(0, 3600).s1 # time series of the water levels of the first hour of the simulation


.. _spatial_filters:

Spatial filters
^^^^^^^^^^^^^^^

The following filters are available for making spatial selections:

- :ref:`contains_point`
- :ref:`in_bbox`
- :ref:`in_tile`
- :ref:`intersects_bbox`
- :ref:`intersects_geometry`
- :ref:`intersects_tile`

The spatial filters can be used on ``GeomArrayField`` subclasses:

.. todo::
    Check this!!!

- Breaches: `coordinates` or `line_geometries`
- Cells: `cell_coords`
- Levees: `coords`
- Lines: `line_coords` or `line_geometries`
- Nodes: `coordinates`


    
.. warning::
    Spatial filters only work on data in *projected* coordinate reference systems.

.. _contains_point:

contains_point
""""""""""""""

The ``contains_point`` filter can be used to, e.g., identify a grid cell in which a given point falls:

.. code-block:: python

    ga.cells.filter(cell_coords__contains_point=xy).id


    from shapely.geometry import Polygon
    polygon = Polygon([
        [109300.0, 518201.2], [108926.5, 518201.2], [108935.6, 517871.7], [109300.0, 518201.2]
    ])
    ga.nodes.filter(coordinates__intersects_geometry=polygon)


.. _in_bbox:
    
in_bbox
"""""""

Returns the features that are within a bounding box.

Example:

.. code-block:: python

    from shapely.geometry import Polygon
    polygon = Polygon([
        [109300.0, 518201.2], [108926.5, 518201.2], [108935.6, 517871.7], [109300.0, 518201.2]
    ])
    gr.lines.filter(
        line_coords__in_bbox=polygon.bounds
    )


.. _in_tile:
    
in_tile
"""""""

.. todo::
    How does this work? What defines the tiles?
    
Example:

.. code:: python

    ga.nodes.filter(coordinates__in_tile=[0, 0, 0])


.. _intersects_bbox:
    
intersects_bbox
"""""""""""""""

Returns the features that intersect a bounding box.

Example:

.. code-block:: python

    from shapely.geometry import Polygon
    polygon = Polygon([
        [109300.0, 518201.2], [108926.5, 518201.2], [108935.6, 517871.7], [109300.0, 518201.2]
    ])
    gr.lines.filter(
        line_coords__intersects_bbox=polygon.bounds
    )


.. _intersects_geometry:
    
intersects_geometry
"""""""""""""""""""

Returns the features that intersect the input geometry. It expects a shapely geometry:

.. code-block:: python

    from shapely.geometry import Polygon
    polygon = Polygon([
        [109300.0, 518201.2], [108926.5, 518201.2], [108935.6, 517871.7], [109300.0, 518201.2]
    ])
    ga.cells.filter(cell_coords__intersects_geometry=polygon)

To improve performance, it is recommended to always combine ``intersects_geometry`` with ``intersects_bbox``, like this:

.. code-block:: python

    gr.lines.filter(
        line_coords__intersects_bbox=polygon.bounds
    ).filter(
        line_coords__intersects_geometry=polygon
    )
    
.. _intersects_tile:

intersects_tile
"""""""""""""""

.. todo::
    How does this work? What defines the tiles?
    
Example:

.. code:: python

    ga.nodes.filter(coordinates__intersects_tile=[0, 0, 0])

.. _non_spatial_filters:

Non-spatial filters
^^^^^^^^^^^^^^^^^^^

Non-geometry fields can also be filtered on. For example, to select the nodes with type "2D Boundary" (i.e. node_type = 5), you can use this filter:

.. code:: python

    ga.nodes.filter(node_type__eq=5)

or both "2D Boundary" and "2D Open water" nodes:

.. code:: python

    ga.nodes.filter(node_type__in=[5, 6])

The following non-spatial filters are available:

- eq: Equals
- ne: Not equals
- gt: Greater than
- gte: Greater than equals
- lt: Less than
- lte: Less than equals
- in: In collection

You combine them with the field name by adding a double underscore ``__`` in between, e.g. ``crest_level`` must be greater than 4.33: ``crest_level__gt=4.33``.

.. _subsets:

Subsets
^^^^^^^

Subsets are an easy way to retrieve categorized sub parts of the data.

``Nodes`` and ``Lines`` have predefined subsets. To those, can call the ``known_subset`` property:

.. code-block:: python

    ga.lines.known_subset
    
    >>> [u'ACTIVE_BREACH',
    >>>  u'2D_OPEN_WATER',
    >>>  u'1D',
    >>>  u'SHORT_CRESTED_STRUCTURES',
    >>>  u'2D_GROUNDWATER',
    >>>  u'LONG_CRESTED_STRUCTURES',
    >>>  u'1D2D',
    >>>  u'2D_VERTICAL_INFILTRATION',
    >>>  u'1D_ALL',
    >>>  u'2D_ALL',
    >>>  u'2D_OPEN_WATER_OBSTACLES',
    >>>  u'GROUNDWATER_ALL']

To retrieve data of a subset use the ``subset()`` method like this:

.. code:: python

    ga.lines.subset('1D_ALL').data  # remember, all filtering is lazy

The definitions of the known subsets can be found here:

- Nodes: threedigrid/admin/nodes/subsets.py
- Lines: threedigrid/admin/lines/subsets.py

You can also define your own subsets.

.. todo::
    Describe how you can define your own subsets

.. _only:

Selecting attributes using ``only``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you only need a few attributes, you can use ``only()``.

Example:

.. code:: python

    ga.nodes.only('id', 'coordinates').data

Exporters
---------

Exporters allow you to export model data to files. For example exporting
all 2D open water lines to a Shapefile with EPSG code 4326 (WGS84):

.. code-block:: python

    from threedigrid.admin.lines.exporters import LinesOgrExporter

    line_2d_open_water_wgs84 = ga.lines.subset('2D_OPEN_WATER').reproject_to('4326')

    exporter = LinesOgrExporter(line_2d_open_water_wgs84)
    exporter.save('/tmp/line.shp', line_2d_open_water_wgs84.data, '4326')

Supported extenstions are:

- .shp (Shapefile)
- .gpkg (GeoPackage)
- .json (GeoJSON)
- .geojson (GeoJSON)

Most models have shortcut methods for exporting their data for shapefiles and geopackages, like:

.. code-block:: python

    # Shapefile
    ga.lines.subset('2D_OPEN_WATER').reproject_to('4326').to_shape('/tmp/line.shp')

    # Geopackage
    ga.lines.subset('2D_OPEN_WATER').reproject_to('4326').to_gpkg('/tmp/line.gpkg')

.. include:: ../threedigrid/management/README.rst

Remote procedure calls
----------------------

.. note:: 
    This is an advanced feature used inside the 3Di stack, probably you do not need this.

Currently only the client-side is included. The server-side might be added in a later stage.

Installation:

.. code:: bash

    $ pip install threedigrid[rpc]


Basic usage:

.. code:: python

    ga = GridH5ResultAdmin('rpc://REDIS_HOST/SIMULATION_ID', 'rpc://REDIS_HOST/SIMULATION_ID')
    # Replace REDIS_HOST and SIMULATION_ID with actual values.
    future_result = ga.nodes.filter(lik__eq=4).data
    data = await future_result.resolve()

Subscription usage:

.. code:: python

    subscription = await future_result.subscribe()

    async for item in subscription.enumerate():
        # do something with item
