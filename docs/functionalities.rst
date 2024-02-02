Functionalities
===============

.. todo::
	Include inheritance diagrams: https://www.sphinx-doc.org/en/master/usage/extensions/inheritance.html

.. _threedimodel_components:

Accessing 3Di model components
------------------------------

``threedigrid`` uses a limited number of main classes to access 3Di model components: ``Breaches``, ``CrossSections``, ``Levees``, ``Lines``, ``Nodes``, and ``Pumps``. The ``Lines`` and ``Nodes`` classes have several child classes (e.g. ``Manholes`` or ``Weirs``) that allow access to attributes specific to those 3Di model components.

``Breaches``, ``Nodes``, ``Lines``, and ``Pumps`` have time series connected to them through the ``GridH5ResultAdmin``, ``GridH5AggregateResultAdmin``, or ``GridH5WaterQualityResultAdmin``. 

.. _breaches:

Breaches
^^^^^^^^

Breaches are 1D-2D flowlines that were schematised using a *Potential breach* feature. They are Lines with a KCU value (line type) of 55.

Breaches have the following attributes:

+-------------------+--------------------------------------------------------+
| Variable Name     | Description                                            |
+===================+========================================================+
| code              | Code as set in the schematisation                      |
+-------------------+--------------------------------------------------------+
| content_pk        | ID of the source record in the schematisation          |
+-------------------+--------------------------------------------------------+
| coordinates       | Coordinates of the start and end nodes                 |
+-------------------+--------------------------------------------------------+
| display_name      | Display name as defined in the schematisation          |
+-------------------+--------------------------------------------------------+
| kcu               | Line type                                              |
+-------------------+--------------------------------------------------------+
| levbr             | Breach width                                           |
+-------------------+--------------------------------------------------------+
| levl              | Exchange level                                         |
+-------------------+--------------------------------------------------------+
| levmat            | Levee material                                         |
+-------------------+--------------------------------------------------------+
| line_geometries   | Geometry of the breach line (start node to end node)   |
+-------------------+--------------------------------------------------------+
| seq_ids           | *Deprecated*                                             |
+-------------------+--------------------------------------------------------+


CrossSections
^^^^^^^^^^^^^

``CrossSections`` describe all 1D cross-sections used in the 3Di model.

``CrossSections`` have the following attributes:

+------------+-------------------------------------------------------------+
| Variable   | Description                                                 |
| Name       |                                                             |
+============+=============================================================+
| code       | Code as set in the schematisation                           |
+------------+-------------------------------------------------------------+
| content_pk | ID of the source record in the schematisation               |
+------------+-------------------------------------------------------------+
| count      | Number of items in the tables array for this CrossSection   |
+------------+-------------------------------------------------------------+
| offset     | Index of the first item of the tables array where the data  |
|            | for this CrossSection is located                            |
+------------+-------------------------------------------------------------+
| shape      | Shape                                                       |
+------------+-------------------------------------------------------------+
| tables     | Array of all values for all Tabulated cross-sections        |
+------------+-------------------------------------------------------------+
| width_1d   | Width of cross-section (for circle and rectangle)           |
+------------+-------------------------------------------------------------+

Grid
^^^^

``Grid`` has the following attributes.

+----------+----------------------------------------------------------+
| Variable | Description                                              |
| Name     |                                                          |
+==========+==========================================================+
| ip       | Deprecated                                               |
+----------+----------------------------------------------------------+
| jp       | Deprecated                                               |
+----------+----------------------------------------------------------+
| nodk     | Refinement level, 1 being the smallest cell              |
+----------+----------------------------------------------------------+
| nodm     | Horizontal index of the cell within its refinement level |
+----------+----------------------------------------------------------+
| nodn     | Vertical index of the cell within its refinement level   |
+----------+----------------------------------------------------------+



Levees
^^^^^^

.. todo::
    
	Is this still used or Deprecated?
  
``Levees`` have the following attributes:
    
+-------------------+---------------------------+
| Variable Name     | Description               |
+===================+===========================+
| coords            | Geometry of the levee     |
+-------------------+---------------------------+
| crest_level       | Crest level               |
+-------------------+---------------------------+
| max_breach_depth  | Max breach depth          |
+-------------------+---------------------------+


Lines
^^^^^

The ``Lines`` class is parent to a number of child classes:

- ``Pipes``
- ``Channels``
- ``Weirs``
- ``Culverts``
- ``Orifices``

``Lines`` and its child classes have the following attributes:

+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| Variable name                   | Description                                                                                                       |
+=================================+===================================================================================================================+
| content_pk                      | ID of the source feature in the schematisation                                                                     |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| content_type                    | Source table in the schematisation                                                                                 |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| cross_pix_coords                | Location (index) of the lower left corner and upper right of the pixels at the cross-section in pixels from DEM origin (1-based) |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| cross_weight                    | Relative distance between cross1 and cross2 (counting from cross1)                                                 |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| cross1                          | ID of CrossSection 1. See also Lines.cross_weight                                                                  |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| cross2                          | ID of CrossSection 2. See also Lines.cross_weight                                                                  |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| discharge_coefficient_negative  | Positive discharge coefficient                                                                                     |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| discharge_coefficient_positive  | Negative discharge coefficient                                                                                     |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| dpumax                          | Exchange level as used by the computational core                                                                    |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| ds1d                            | Geometrical length of the line (used to calculate gradient)                                                        |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| ds1d_half                       | Distance from start of the line to the velocity point (relevant for embedded flowlines only)                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| flod                            | Obstacle height at cross-section (2D).                                                                              |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| flou                            | Obstacle height at cross-section (2D).                                                                              |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| invert_level_end_point          | Invert level at the end of the line                                                                                 |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| invert_level_start_point        | Invert level at the start of the line                                                                               |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| kcu                             | Line type                                                                                                           |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| lik                             | Refinement level, 1 being the smallest cell. For internal use only.                                                 |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| line                            | IDs of start and end nodes                                                                                          |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| line_coords                     | Coordinates of the start and end nodes                                                                              |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| line_geometries                 | (Relevant part of the) geometry of this element as set in the schematisation.                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| sewerage                        | Is this part of a sewer system?                                                                                     |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| sewerage_type                   | Sewerage type                                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| zoom_category                   | Zoom category                                                                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+


``Channels`` have the following attributes, additional to the ones inherited from ``Lines``:

+--------------------------+-------------------------------+
| Variable name            | Description                   |
+==========================+===============================+
| calculation_type         | Calculation type              |
+--------------------------+-------------------------------+
| code                     | Code as set in the schematisation |
+--------------------------+-------------------------------+
| connection_node_end_pk   | Connection node end ID        |
+--------------------------+-------------------------------+
| connection_node_start_pk | Connection node start ID      |
+--------------------------+-------------------------------+
| discharge_coefficient    | Discharge coefficient         |
+--------------------------+-------------------------------+
| dist_calc_points         | Calculation point distance    |
+--------------------------+-------------------------------+

``Culverts`` have the following attributes, additional to the ones inherited from ``Lines``:

+--------------------------+-----------------------------------------+
| Variable Name            | Description                             |
+==========================+=========================================+
| calculation_type         | Calculation type                        |
+--------------------------+-----------------------------------------+
| code                     | Code as set in the schematisation       |
+--------------------------+-----------------------------------------+
| connection_node_end_pk   | Connection node end ID                  |
+--------------------------+-----------------------------------------+
| connection_node_start_pk | Connection node start ID                |
+--------------------------+-----------------------------------------+
| cross_section_height     | Cross-section height                    |
+--------------------------+-----------------------------------------+
| cross_section_shape      | Cross-section shape                     |
+--------------------------+-----------------------------------------+
| cross_section_width      | Cross-section width                     |
+--------------------------+-----------------------------------------+
| display_name             | Display name as defined in the schematisation |
+--------------------------+-----------------------------------------+
| dist_calc_points         | Calculation point distance              |
+--------------------------+-----------------------------------------+
| friction_type            | Friction type                           |
+--------------------------+-----------------------------------------+
| friction_value           | Friction value                          |
+--------------------------+-----------------------------------------+


``Orifices`` have the following attributes, additional to the ones inherited from ``Lines``:

+--------------------------+-----------------------------------------+
| Variable Name            | Description                             |
+==========================+=========================================+
| connection_node_end_pk   | Connection node end ID                  |
+--------------------------+-----------------------------------------+
| connection_node_start_pk | Connection node start ID                |
+--------------------------+-----------------------------------------+
| crest_level              | Crest level                             |
+--------------------------+-----------------------------------------+
| crest_type               | Crest type                              |
+--------------------------+-----------------------------------------+
| display_name             | Display name as defined in the schematisation |
+--------------------------+-----------------------------------------+
| friction_type            | Friction type                           |
+--------------------------+-----------------------------------------+
| friction_value           | Friction value                          |
+--------------------------+-----------------------------------------+
| sewerage                 | Code as set in the schematisation       |
+--------------------------+-----------------------------------------+


``Pipes`` have the following attributes, additional to the ones inherited from ``Lines``:

+--------------------------+-------------------------------------------+
| Variable Name            | Description                               |
+==========================+===========================================+
| calculation_type         | Calculation type                          |
+--------------------------+-------------------------------------------+
| connection_node_end_pk   | Connection node end ID                    |
+--------------------------+-------------------------------------------+
| connection_node_start_pk | Connection node start ID                  |
+--------------------------+-------------------------------------------+
| cross_section_height     | Cross-section height                      |
+--------------------------+-------------------------------------------+
| cross_section_shape      | Cross-section shape                       |
+--------------------------+-------------------------------------------+
| cross_section_width      | Cross-section width                       |
+--------------------------+-------------------------------------------+
| discharge_coefficient    | Discharge coefficient                     |
+--------------------------+-------------------------------------------+
| display_name             | Display name as defined in the schematisation |
+--------------------------+-------------------------------------------+
| friction_type            | Friction type                             |
+--------------------------+-------------------------------------------+
| friction_value           | Friction value                            |
+--------------------------+-------------------------------------------+
| material                 | Pipe material                             |
+--------------------------+-------------------------------------------+
| sewerage_type            | Sewerage type                             |
+--------------------------+-------------------------------------------+


``Weirs`` have the following attributes, additional to the ones inherited from ``Lines``:

+--------------------------+------------------------------------------------+
| Variable Name            | Description                                    |
+==========================+================================================+
| code                     | Code as set in the schematisation              |
+--------------------------+------------------------------------------------+
| connection_node_end_pk   | Connection node end ID                         |
+--------------------------+------------------------------------------------+
| connection_node_start_pk | Connection node start ID                       |
+--------------------------+------------------------------------------------+
| crest_level              | Crest level                                    |
+--------------------------+------------------------------------------------+
| crest_type               | Crest type                                     |
+--------------------------+------------------------------------------------+
| cross_section_height     | Cross-section height                           |
+--------------------------+------------------------------------------------+
| cross_section_shape      | Cross-section shape                            |
+--------------------------+------------------------------------------------+
| cross_section_width      | Cross-section width                            |
+--------------------------+------------------------------------------------+
| display_name             | Display name as defined in the schematisation  |
+--------------------------+------------------------------------------------+
| friction_type            | Friction type                                  |
+--------------------------+------------------------------------------------+
| friction_value           | Friction value                                 |
+--------------------------+------------------------------------------------+
| sewerage                 | Is this weir part of a sewer system?           |
+--------------------------+------------------------------------------------+


Nodes
^^^^^

The ``Nodes`` class is parent to a number of child classes:

- ``Cells``
- ``ConnectionNodes``
- ``Manholes`` (child class of ``ConnectionNodes``)

``Nodes`` have the following attributes, additional to the ones inherited from ``Lines``:

+------------------------+----------------------------------------------------------------------------------------------------------------+
| Variable Name          | Description                                                                                                    |
+========================+================================================================================================================+
| calculation_type       | Calculation type                                                                                               |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| cell_coords            | Cell coordinates                                                                                               |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| content_pk             | Connection node ID                                                                                             |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| coordinates            | Node coordinates                                                                                               |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| dimp                   | Impervious surface level (interflow)                                                                           |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| dmax                   | Bottom level. May differ from Manhole.bottom_level e.g. if all pipes connected to this node have a higher invert level. For 2D: elevation of lowest pixel in the cell. |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| drain_level            | Drain level as defined in the schematisation. May be different from the actual exchange level (see Lines.dpumax). Only relevant if models is purely 1D. In all other cases, use Lines.dpumax). |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| initial_waterlevel     | Initial water level as defined in the schematisation.                                                           |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| is_manhole             | Is this node a manhole                                                                                          |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| node_type              | Node type                                                                                                      |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| seq_id                 | Deprecated                                                                                                     |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| storage_area           | Storage area as defined in the schematisation. May be different from the actual/total storage area (see Nodes.sumax) |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| sumax                  | Maximum surface area (wet surface area when entire cell/node is wet)                                           |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| zoom_category          | Zoom category                                                                                                  |
+------------------------+----------------------------------------------------------------------------------------------------------------+


``Cells`` have the following attributes, additional to the ones inherited from ``Nodes``:

+-------------------+------------------------------------------------------------------------------------------------------------------+
| Variable Name     | Description                                                                                                      |
+===================+==================================================================================================================+
| has_dem_averaged  | Has DEM averaging been used in this cell?                                                                        |
+-------------------+------------------------------------------------------------------------------------------------------------------+
| pixel_coords      | Location (index) of the lower left corner and upper right in pixels from DEM origin (1-based)                    |
+-------------------+------------------------------------------------------------------------------------------------------------------+
| pixel_width       | Pixel size                                                                                                       |
+-------------------+------------------------------------------------------------------------------------------------------------------+
| z_coordinate      | Elevation of lowest pixel in the cell. Equal to Node.dmax                                                        |
+-------------------+------------------------------------------------------------------------------------------------------------------+


``ConnectionNodes`` have the same attributes as ``Nodes``.

``Manholes`` have the following attributes, additional to the ones inherited from ``Nodes``:

+-------------------+----------------------------------------------------------------------------------+
| Variable Name     | Description                                                                      |
+===================+==================================================================================+
| bottom_level      | Bottom level as defined in the schematisation. For the bottom level used in the  |
|                   | calculation, see Nodes.dmax                                                      |
+-------------------+----------------------------------------------------------------------------------+
| display_name      | Display name as defined in the schematisation                                    |
+-------------------+----------------------------------------------------------------------------------+
| manhole_indicator | Manhole indicator as defined in the schematisation                               |
+-------------------+----------------------------------------------------------------------------------+
| shape             | Manhole shape as defined in the schematisation                                   |
+-------------------+----------------------------------------------------------------------------------+
| surface_level     | Surface level as defined in the schematisation                                   |
+-------------------+----------------------------------------------------------------------------------+
| width             | Manhole width as defined in the schematisation                                   |
+-------------------+----------------------------------------------------------------------------------+

.. note::
    The ``Nodes`` child class ``EmbeddedNodes`` is intended for internal use only.

Pumps
^^^^^

+-------------------+-----------------------------------------------------------------------------------------+
| Variable Name     | Description                                                                             |
+===================+=========================================================================================+
| bottom_level      | Bottom level of the start node                                                          |
+-------------------+-----------------------------------------------------------------------------------------+
| capacity          | Pump capacity                                                                           |
+-------------------+-----------------------------------------------------------------------------------------+
| content_pk        | ID of the source record in the schematisation                                           |
+-------------------+-----------------------------------------------------------------------------------------+
| coordinates       | Coordinates is the centroid of node_coordinates if both are set, else the one that is set. |
+-------------------+-----------------------------------------------------------------------------------------+
| display_name      | Display name as defined in the schematisation                                           |
+-------------------+-----------------------------------------------------------------------------------------+
| lower_stop_level  | Pump lower stop level                                                                   |
+-------------------+-----------------------------------------------------------------------------------------+
| node_coordinates  | ``[[node1_x], [node1_y], [node2_x], [node2_y]]`` ``-9999`` if nodeX_id is -9999         |
+-------------------+-----------------------------------------------------------------------------------------+
| node1_id          | Start node id                                                                           |
+-------------------+-----------------------------------------------------------------------------------------+
| node2_id          | End node id                                                                             |
+-------------------+-----------------------------------------------------------------------------------------+
| start_level       | Pump start level                                                                        |
+-------------------+-----------------------------------------------------------------------------------------+
| type              | Pump type                                                                               |
+-------------------+-----------------------------------------------------------------------------------------+
| zoom_category     | Zoom category                                                                           |
+-------------------+-----------------------------------------------------------------------------------------+



Filters and subsets
-------------------

To make selections of data, you can use :ref:`spatial_filters`, :ref:`non_spatial_filters`, and :ref:`subsets`. You can chain these in any way you like. The example below returns all 1D nodes with a storage area >= 1.0 within a specific area.

	ga.nodes.subset("1D_ALL").filter(storage_area__gte=1.0).filter(coordinates__intersects_geometry=my_polygon)

The filters and subsets are 'lazy', i.e. they are not executed until data is retrieved. To retrieve data you have to call ``data`` or ``timeseries()`` explicitly::

    ga.nodes.filter(node_type__eq=5)  # will not return all data
    ga.nodes.filter(node_type__eq=5).data  # returns all data as an OrderedDict
	gr.nodes.s1.timeseries(0, 3600) # time series of the water levels of the first hour of the simulation


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

The ``contains_point`` filter can be used to, e.g., identify a grid cell in which a given point falls::

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

Example:: 

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
	
Example::

	ga.nodes.filter(coordinates__in_tile=[0, 0, 0])


.. _intersects_bbox:
	
intersects_bbox
"""""""""""""""

Returns the features that intersect a bounding box.

Example:: 

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

Returns the features that intersect the input geometry. It expects a shapely geometry::

    from shapely.geometry import Polygon
    polygon = Polygon([
        [109300.0, 518201.2], [108926.5, 518201.2], [108935.6, 517871.7], [109300.0, 518201.2]
    ])
    ga.cells.filter(cell_coords__intersects_geometry=polygon)

To improve performance, it is recommended to always combine ``intersects_geometry`` with ``intersects_bbox``, like this::

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
	
Example::

	ga.nodes.filter(coordinates__intersects_tile=[0, 0, 0])

Non-spatial filters
^^^^^^^^^^^^^^^^^^^

Non-geometry fields can also be filtered on. For example, to select the nodes with type "2D Boundary" (i.e. node_type = 5), you can use this filter::

    ga.nodes.filter(node_type__eq=5)

or both "2D Boundary" and "2D Open water" nodes::

    ga.nodes.filter(node_type__in=[5, 6])

The following non-spatial filters are available:

    - eq ("Equals")
    - ne: ("Not equals")
    - gt: ("Greater than")
    - gte: ("Greater than equals")
    - lt: ("Less than")
    - lte': ("Less than equals")
    - in: ("In collection")

You combine them with the field name by adding a double underscore ``__`` in between, e.g. ``crest_level`` must be greater than 4.33: ``crest_level__gt=4.33``.

Subsets
-------

Subsets are an easy way to retrieve categorized sub parts of the data.

``Nodes`` and ``Lines`` have predefined subsets. To those, can call the ``known_subset`` property::

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

To retrieve data of a subset use the ``subset()`` method like this::

    ga.lines.subset('1D_ALL').data  # remember, all filtering is lazy

The definitions of the known subsets can be found here:

- Nodes: threedigrid/admin/nodes/subsets.py
- Lines: threedigrid/admin/lines/subsets.py

You can also define your own subsets.

.. todo::
    Describe how you can define your own subsets

Exporters
---------	

Exporters allow you to export model data to files. For example exporting
all 2D open water lines to a Shapefile with EPSG code 4326 (WGS84)::

    from threedigrid.admin.lines.exporters import LinesOgrExporter

    line_2d_open_water_wgs84 = ga.lines.subset('2D_OPEN_WATER').reproject_to('4326')

    exporter = LinesOgrExporter(line_2d_open_water_wgs84)
    exporter.save('/tmp/line.shp', line_2d_open_water_wgs84.data, '4326')

Supported extenstions are:

- .shp (Shapefile)
- .gpkg (GeoPackage)
- .json (GeoJSON)
- .geojson (GeoJSON)

Most models have shortcut methods for exporting their data for shapefiles and geopackages, like::

    # Shapefile
    ga.lines.subset('2D_OPEN_WATER').reproject_to('4326').to_shape('/tmp/line.shp')

    # Geopackage
    ga.lines.subset('2D_OPEN_WATER').reproject_to('4326').to_gpkg('/tmp/line.gpkg')

