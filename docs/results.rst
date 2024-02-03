.. _results3di:

results_3di.nc
==============

The results_3di.nc file is accessed through the ``GridH5ResultAdmin`` class.

Minimal example
---------------

.. code-block:: python

    from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
    from threedigrid.admin.gridadmin import GridH5Admin
    
    # Instantiate GridH5Admin and GridH5ResultAdmin objects
    gridadmin_filename = r"C:\3Di\My Model\gridadmin.h5"
    results_filename = r"C:\3Di\My Simulation\results_3di.nc"
    ga = GridH5Admin(gridadmin_filename)
    gr = GridH5ResultAdmin(gridadmin_filename, results_filename)

    # Get water level (s1) time series for node 23
    last_timestamp = gr.nodes.timestamps[-1]
    water_levels_23 = gr.nodes.filter(id__eq=23).timeseries(start_time=0, end_time=last_timestamp).s1
    
    # Get the discharge (q) time series for all 1D nodes for the first hour of the simulation
    discharge_1d = gr.lines.subset('1D').timeseries(start_time=0,end_time=3600).q
    

Functionalities
---------------

The following methods and properties of the ``ResultMixin`` class are available for nodes, lines, breaches, and pumps

.. automethod:: threedigrid.orm.base.timeseries_mixin.ResultMixin.sample
.. automethod:: threedigrid.orm.base.timeseries_mixin.ResultMixin.timeseries
.. autoproperty:: threedigrid.orm.base.timeseries_mixin.ResultMixin.timestamps
.. autoproperty:: threedigrid.orm.base.timeseries_mixin.ResultMixin.dt_timestamps




Meta data
^^^^^^^^^

Descriptions of variables in the results_3di.nc file can be retrieved using the ``_meta`` property. For example:

.. code-block:: python

    gr.nodes._meta.s1
    >>> s1(units=u'm', long_name=u'waterlevel', standard_name=u'water_surface_height_above_reference_datum')


``s1`` is a ``namedtuple``, so you can retrieve the units attribute by using the ``.`` notation:

.. code:: python
    
	gr.nodes._meta.s1.units
	
or using the ``_as_dict`` method 

.. code:: python

    gr.nodes._meta.s1._asdict()['units']
 

Attribute names
---------------

Nodes
^^^^^

+---------------------------+----------------------------------------+
| Variable Name             | Description                            |
+===========================+========================================+
| infiltration_rate_simple  | Infiltration rate                      |
+---------------------------+----------------------------------------+
| intercepted_volume        | Intercepted volume                     |
+---------------------------+----------------------------------------+
| leak                      | Leakage                                |
+---------------------------+----------------------------------------+
| q_lat                     | Lateral discharge                      |
+---------------------------+----------------------------------------+
| q_sss                     | Surface sources and sinks discharge    |
+---------------------------+----------------------------------------+
| rain                      | Rain intensity                         |
+---------------------------+----------------------------------------+
| s1                        | Water level                            |
+---------------------------+----------------------------------------+
| su                        | Wet surface area                       |
+---------------------------+----------------------------------------+
| ucx                       | Velocity at cell center in x direction |
+---------------------------+----------------------------------------+
| ucy                       | Velocity at cell center in y direction |
+---------------------------+----------------------------------------+
| vol                       | Volume                                 |
+---------------------------+----------------------------------------+


Lines
^^^^^

+----------------+-------------------------------+
| Variable Name  | Description                   |
+================+===============================+
| au             | Wet cross-sectional area      |
+----------------+-------------------------------+
| breach_depth   | Breach depth                  |
+----------------+-------------------------------+
| breach_width   | Breach width                  |
+----------------+-------------------------------+
| q              | Discharge                     |
+----------------+-------------------------------+
| qp             | Interflow discharge           |
+----------------+-------------------------------+
| u1             | Flow velocity                 |
+----------------+-------------------------------+
| up1            | Interflow velocity            |
+----------------+-------------------------------+
	
