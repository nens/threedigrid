
.. _structure_control_actions3di:

structure_control_actions_3di.nc
================================

If there are any structure control actions during the simulation, these are logged to the structure_control_actions_3di.nc file. This file can be accessed through the ``GridH5StructureControl`` class.

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

The main class ``GridH5StructureControl`` is documented below. 

This class' ``table_control``, ``memory_control``, or ``timed_control`` properties return instances of ``_GridH5NestedStructureControl``, also documented below.

.. autoclass:: threedigrid.admin.gridresultadmin.GridH5StructureControl
    :members:
	
.. autoclass:: threedigrid.admin.gridresultadmin._GridH5NestedStructureControl
	:members:

Exporters
^^^^^^^^^

.. automodule:: threedigrid.admin.structure_controls.exporters
    :members: structure_control_actions_to_csv



Attribute names
---------------

+----------------+---------------------------------------------------------------------------------------------+
| Attribute      | Description                                                                                 |
+================+=============================================================================================+
| action_type    | Action type                                                                                 |
+----------------+---------------------------------------------------------------------------------------------+
| action_value_1 | Action value 1, e.g. crest_level if action_type = set_crest_level                           |
+----------------+---------------------------------------------------------------------------------------------+
| action_value_2 | Action value 2 (relevant if action_type = set_discharge_coefficients)                       |
+----------------+---------------------------------------------------------------------------------------------+
| id             | ID of the structure control action                                                          |
+----------------+---------------------------------------------------------------------------------------------+
| is_active      | Is the structure control active                                                             |
+----------------+---------------------------------------------------------------------------------------------+
| source_table   | Source table in the schematisation for the structure on which the structure control acts    |
+----------------+---------------------------------------------------------------------------------------------+
| source_table_id| ID of the feature in the schematisation                                                     |
+----------------+---------------------------------------------------------------------------------------------+
| time           | Time in seconds since start of simulation at which structure control action takes place     |
+----------------+---------------------------------------------------------------------------------------------+
