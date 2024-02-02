structure_control_actions_3di.nc: GridH5StructureControl
========================================================

Minimal example
---------------
.. code-block:: python

	from threedigrid.admin.gridresultadmin import GridH5StructureControl
	from threedigrid.admin.structure_controls.exporters import structure_control_actions_to_csv

	gst = GridH5StructureControl("gridadmin.h5", "structure_control_actions_3di.nc")
	gst.table_control
	structure_control_actions_to_csv(gst, "test.csv")
	
Functionalities
---------------

.. todo::
    Write this

Attribute names
---------------

+----------------+---------------------------------------------------------------------------------------------+
| Attribute      | Description                                                                                   |
+================+=============================================================================================+
| action_type    | Action type                                                                                   |
+----------------+---------------------------------------------------------------------------------------------+
| action_value_1 | Action value 1, e.g. crest_level is action_type = set_crest_level                            |
+----------------+---------------------------------------------------------------------------------------------+
| action_value_2 | Action value 2 (relevant if action_type = set_discharge_coefficients                          |
+----------------+---------------------------------------------------------------------------------------------+
| id             | ID of the structure control action                                                            |
+----------------+---------------------------------------------------------------------------------------------+
| is_active      | Is the structure control active                                                               |
+----------------+---------------------------------------------------------------------------------------------+
| source_table   | Source table in the schematisation for the structure on which the structure control acts     |
+----------------+---------------------------------------------------------------------------------------------+
| source_table_id| ID of the feature in the schematisation                                                       |
+----------------+---------------------------------------------------------------------------------------------+
| time           | Time in seconds since start of simulation at which structure control action takes place      |
+----------------+---------------------------------------------------------------------------------------------+
