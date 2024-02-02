gridadmin.h5: GridH5Admin
=========================

The gridadmin.h5 file contains the computational grid. This is all static data, i.e. the file contains no time series. It is the basis for interfacing with all of the other files.

Minimal example
---------------

.. todo::
    Write this


Functionalities
---------------

.. todo::
    Write this

.. _gridadmin_models:

Models
------

.. todo::
    Add (auto) documentation of relevant class properties and methods

The contents of the gridadmin file are accessed through a number of ``threedigrid`` Models (not to be confused with "3Di model"):

- :ref:`breaches`
- :ref:`crosssections`
- :ref:`grid`
- :ref:`levees`
- :ref:`lines`
- :ref:`nodes`

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
| seq_ids           | *Deprecated*                                           |
+-------------------+--------------------------------------------------------+

.. _crosssections:

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

.. _grid:

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

.. _levees:

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

.. _lines:

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
| content_pk                      | ID of the source feature in the schematisation                                                                    |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| content_type                    | Source table in the schematisation                                                                                |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| cross_pix_coords                | Location (index) of the lower left and upper right of the pixels at the cross-section in DEM (1-based)            |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| cross_weight                    | Relative distance between cross1 and cross2 (counting from cross1)                                                |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| cross1                          | ID of CrossSection 1. See also Lines.cross_weight                                                                 |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| cross2                          | ID of CrossSection 2. See also Lines.cross_weight                                                                 |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| discharge_coefficient_negative  | Positive discharge coefficient                                                                                    |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| discharge_coefficient_positive  | Negative discharge coefficient                                                                                    |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| dpumax                          | Exchange level as used by the computational core                                                                  |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| ds1d                            | Geometrical length of the line (used to calculate gradient)                                                       |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| ds1d_half                       | Distance from start of the line to the velocity point (relevant for embedded flowlines only)                      |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| flod                            | Obstacle height at cross-section (2D).                                                                            |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| flou                            | Obstacle height at cross-section (2D).                                                                            |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| invert_level_end_point          | Invert level at the end of the line                                                                               |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| invert_level_start_point        | Invert level at the start of the line                                                                             |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| kcu                             | Line type                                                                                                         |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| lik                             | Refinement level, 1 being the smallest cell. For internal use only.                                               |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| line                            | IDs of start and end nodes                                                                                        |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| line_coords                     | Coordinates of the start and end nodes                                                                            |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| line_geometries                 | (Relevant part of the) geometry of this element as set in the schematisation.                                     |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| sewerage                        | Is this part of a sewer system?                                                                                   |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| sewerage_type                   | Sewerage type                                                                                                     |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+
| zoom_category                   | Zoom category                                                                                                     |
+---------------------------------+-------------------------------------------------------------------------------------------------------------------+


``Channels`` have the following attributes, additional to the ones inherited from ``Lines``:

+--------------------------+-----------------------------------+
| Variable name            | Description                       |
+==========================+===================================+
| calculation_type         | Calculation type                  |
+--------------------------+-----------------------------------+
| code                     | Code as set in the schematisation |
+--------------------------+-----------------------------------+
| connection_node_end_pk   | Connection node end ID            |
+--------------------------+-----------------------------------+
| connection_node_start_pk | Connection node start ID          |
+--------------------------+-----------------------------------+
| discharge_coefficient    | Discharge coefficient             |
+--------------------------+-----------------------------------+
| dist_calc_points         | Calculation point distance        |
+--------------------------+-----------------------------------+

``Culverts`` have the following attributes, additional to the ones inherited from ``Lines``:

+--------------------------+-----------------------------------------------+
| Variable Name            | Description                                   |
+==========================+===============================================+
| calculation_type         | Calculation type                              |
+--------------------------+-----------------------------------------------+
| code                     | Code as set in the schematisation             |
+--------------------------+-----------------------------------------------+
| connection_node_end_pk   | Connection node end ID                        |
+--------------------------+-----------------------------------------------+
| connection_node_start_pk | Connection node start ID                      |
+--------------------------+-----------------------------------------------+
| cross_section_height     | Cross-section height                          |
+--------------------------+-----------------------------------------------+
| cross_section_shape      | Cross-section shape                           |
+--------------------------+-----------------------------------------------+
| cross_section_width      | Cross-section width                           |
+--------------------------+-----------------------------------------------+
| display_name             | Display name as defined in the schematisation |
+--------------------------+-----------------------------------------------+
| dist_calc_points         | Calculation point distance                    |
+--------------------------+-----------------------------------------------+
| friction_type            | Friction type                                 |
+--------------------------+-----------------------------------------------+
| friction_value           | Friction value                                |
+--------------------------+-----------------------------------------------+


``Orifices`` have the following attributes, additional to the ones inherited from ``Lines``:

+--------------------------+-----------------------------------------------+
| Variable Name            | Description                                   |
+==========================+===============================================+
| connection_node_end_pk   | Connection node end ID                        |
+--------------------------+-----------------------------------------------+
| connection_node_start_pk | Connection node start ID                      |
+--------------------------+-----------------------------------------------+
| crest_level              | Crest level                                   |
+--------------------------+-----------------------------------------------+
| crest_type               | Crest type                                    |
+--------------------------+-----------------------------------------------+
| display_name             | Display name as defined in the schematisation |
+--------------------------+-----------------------------------------------+
| friction_type            | Friction type                                 |
+--------------------------+-----------------------------------------------+
| friction_value           | Friction value                                |
+--------------------------+-----------------------------------------------+
| sewerage                 | Code as set in the schematisation             |
+--------------------------+-----------------------------------------------+


``Pipes`` have the following attributes, additional to the ones inherited from ``Lines``:

+--------------------------+-----------------------------------------------+
| Variable Name            | Description                                   |
+==========================+===============================================+
| calculation_type         | Calculation type                              |
+--------------------------+-----------------------------------------------+
| connection_node_end_pk   | Connection node end ID                        |
+--------------------------+-----------------------------------------------+
| connection_node_start_pk | Connection node start ID                      |
+--------------------------+-----------------------------------------------+
| cross_section_height     | Cross-section height                          |
+--------------------------+-----------------------------------------------+
| cross_section_shape      | Cross-section shape                           |
+--------------------------+-----------------------------------------------+
| cross_section_width      | Cross-section width                           |
+--------------------------+-----------------------------------------------+
| discharge_coefficient    | Discharge coefficient                         |
+--------------------------+-----------------------------------------------+
| display_name             | Display name as defined in the schematisation |
+--------------------------+-----------------------------------------------+
| friction_type            | Friction type                                 |
+--------------------------+-----------------------------------------------+
| friction_value           | Friction value                                |
+--------------------------+-----------------------------------------------+
| material                 | Pipe material                                 |
+--------------------------+-----------------------------------------------+
| sewerage_type            | Sewerage type                                 |
+--------------------------+-----------------------------------------------+


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

.. _nodes:

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
| dmax                   | Bottom level. May differ from Manhole.bottom_level e.g. if all pipes connected to this node have a higher      |
|                        | invert level. For 2D: elevation of lowest pixel in the cell.                                                   |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| drain_level            | Drain level as defined in the schematisation. May be different from the actual exchange level                  |
|                        | (see Lines.dpumax). Only relevant if models is purely 1D. In all other cases, use Lines.dpumax).               |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| initial_waterlevel     | Initial water level as defined in the schematisation.                                                          |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| is_manhole             | Is this node a manhole                                                                                         |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| node_type              | Node type                                                                                                      |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| seq_id                 | *Deprecated*                                                                                                   |
+------------------------+----------------------------------------------------------------------------------------------------------------+
| storage_area           | Storage area as defined in the schematisation.                                                                 |
|                        | May be different from the actual/total storage area (see Nodes.sumax)                                          |
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

+-------------------+--------------------------------------------------------------------------------------------+
| Variable Name     | Description                                                                                |
+===================+============================================================================================+
| bottom_level      | Bottom level of the start node                                                             |
+-------------------+--------------------------------------------------------------------------------------------+
| capacity          | Pump capacity                                                                              |
+-------------------+--------------------------------------------------------------------------------------------+
| content_pk        | ID of the source record in the schematisation                                              |
+-------------------+--------------------------------------------------------------------------------------------+
| coordinates       | Coordinates is the centroid of node_coordinates if both are set, else the one that is set. |
+-------------------+--------------------------------------------------------------------------------------------+
| display_name      | Display name as defined in the schematisation                                              |
+-------------------+--------------------------------------------------------------------------------------------+
| lower_stop_level  | Pump lower stop level                                                                      |
+-------------------+--------------------------------------------------------------------------------------------+
| node_coordinates  | ``[[node1_x], [node1_y], [node2_x], [node2_y]]`` ``-9999`` if nodeX_id is -9999            |
+-------------------+--------------------------------------------------------------------------------------------+
| node1_id          | Start node id                                                                              |
+-------------------+--------------------------------------------------------------------------------------------+
| node2_id          | End node id                                                                                |
+-------------------+--------------------------------------------------------------------------------------------+
| start_level       | Pump start level                                                                           |
+-------------------+--------------------------------------------------------------------------------------------+
| type              | Pump type                                                                                  |
+-------------------+--------------------------------------------------------------------------------------------+
| zoom_category     | Zoom category                                                                              |
+-------------------+--------------------------------------------------------------------------------------------+

