.. _aggregate_results3di:

aggregate_results_3di.nc
========================

The aggregate_results_3di.nc file is accessed through the ``GridH5AggregateResultAdmin`` class.

Note that it depends on the simulation's aggregation settings which variables are available in the aggregate_results_3di.nc file.

Minimal example
---------------


.. code-block:: python

    from threedigrid.admin.gridresultadmin import GridH5AggregateResultAdmin
    
    # Instantiate GridH5AggregateResultAdmin object
    gridadmin_filename = r"C:\3Di\My Model\gridadmin.h5"
    aggregate_results_filename = r"C:\3Di\My Simulation\aggregate_results_3di"
    gar = GridH5AggregateResultAdmin(gridadmin_filename, aggregate_results_filename)

    # It depends on the simulation's aggregation settings which variables are available
    # Get a list of all available fields for the lines:
    gar.lines._meta.get_fields()

    # Get a list of all available fields for the nodes:
    gar.nodes._meta.get_fields()

    # Get the maximum water level (s1_max) for all nodes
    # Note that the timestamps may be different for different variables
    last_timestamp = gar.nodes.get_timestamps('s1_max')[-1]
    nodes = gar.nodes.timeseries(start_time=0, end_time=last_timestamp).s1_max


Functionalities
---------------

The following methods and properties of the ``AggregateResultMixin`` class are available for nodes, lines, breaches, and pumps

.. automethod:: threedigrid.orm.base.timeseries_mixin.AggregateResultMixin.sample
.. automethod:: threedigrid.orm.base.timeseries_mixin.AggregateResultMixin.timeseries
.. automethod:: threedigrid.orm.base.timeseries_mixin.AggregateResultMixin.get_timestamps
.. automethod:: threedigrid.orm.base.timeseries_mixin.AggregateResultMixin.get_time_unit
.. autoproperty:: threedigrid.orm.base.timeseries_mixin.AggregateResultMixin.timestamps
.. autoproperty:: threedigrid.orm.base.timeseries_mixin.AggregateResultMixin.dt_timestamps


Attribute names
---------------

Attribute names in the GridH5AggregateResultAdmin are a combination of the variable name and the aggregation method suffix. For example, the maximum water level (s1) is accessed by the name ``s1_max``.


Nodes
^^^^^

+---------------------------+-----------------------------------------+---------------------------------------------+
| Attribute                 | Possible suffixes                       | Description                                 |
+===========================+=========================================+=============================================+
| infiltration_rate_simple  | min, max, avg, cum, cum_positive,       | Infiltration rate                           |
|                           | cum_negative                            |                                             |
+---------------------------+-----------------------------------------+---------------------------------------------+
| intercepted_volume        | min, max, avg, sum, cum, current        | Intercepted volume                          |
+---------------------------+-----------------------------------------+---------------------------------------------+
| leak                      | min, max, avg, cum, cum_positive,       | Leakage                                     |
|                           | cum_negative                            |                                             |
+---------------------------+-----------------------------------------+---------------------------------------------+
| q_lat                     | min, max, avg, cum, cum_positive,       | Lateral discharge                           |
|                           | cum_negative                            |                                             |
+---------------------------+-----------------------------------------+---------------------------------------------+
| q_sss                     | min, max, avg, cum, cum_positive,       | Surface sources and sinks discharge         |
|                           | cum_negative                            |                                             |
+---------------------------+-----------------------------------------+---------------------------------------------+
| rain                      | min, max, avg, cum, cum_positive,       | Rain intensity                              |
|                           | cum_negative                            |                                             |
+---------------------------+-----------------------------------------+---------------------------------------------+
| s1                        | min, max, avg                           | Water level                                 |
+---------------------------+-----------------------------------------+---------------------------------------------+
| su                        | min, max, avg                           | Wet surface area                            |
+---------------------------+-----------------------------------------+---------------------------------------------+
| ucx                       | min, max, avg                           | Velocity at cell center in x direction      |
+---------------------------+-----------------------------------------+---------------------------------------------+
| ucy                       | min, max, avg                           | Velocity at cell center in y direction      |
+---------------------------+-----------------------------------------+---------------------------------------------+
| vol                       | min, max, avg, sum, cum, current        | Volume                                      |
+---------------------------+-----------------------------------------+---------------------------------------------+


Lines
^^^^^

+---------------------------+-----------------------------------------+---------------------------------------------+
| Attribute                 | Possible suffixes                       | Description                                 |
+===========================+=========================================+=============================================+
| au                        | min, max, avg                           | Wet cross-sectional area                    |
+---------------------------+-----------------------------------------+---------------------------------------------+
| q                         | min, max, avg, cum, cum_positive,       | Discharge                                   |
|                           | cum_negative                            |                                             |
+---------------------------+-----------------------------------------+---------------------------------------------+
| qp                        | min, max, avg                           | Interflow discharge                         |
+---------------------------+-----------------------------------------+---------------------------------------------+
| u1                        | min, max, avg                           | Flow velocity                               |
+---------------------------+-----------------------------------------+---------------------------------------------+
| up1                       | min, max, avg, cum, cum_positive,       | Interflow velocity                          |
|                           | cum_negative                            |                                             |
+---------------------------+-----------------------------------------+---------------------------------------------+
