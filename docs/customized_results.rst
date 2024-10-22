.. _customized_results3di:

customized_results_3di.nc
=========================

The customized_results_3di.nc file contains a snapshot results for a spatial selection of nodes, flowlines, and pumps, for a selected list of variables. It is accessed through the ``CustomizedResultAdmin`` class.

Minimal example
---------------

.. code-block:: python

    from threedigrid.admin.gridresultadmin import CustomizedResultAdmin
    from threedigrid.admin.gridadmin import GridH5Admin

    # Instantiate GridH5Admin and GridH5ResultAdmin objects
    gridadmin_filename = r"C:\3Di\My Model\gridadmin.h5"
    customized_results_filename = r"C:\3Di\My Simulation\customized_results_3di.nc"
    cra = CustomizedResultAdmin(gridadmin_filename, customized_results_filename)

    # List the areas in this file
    cra.areas

    # See the name of area1
    cra.area1.name

    # List the available nodes
    cra.nodes.id  # in the whole file
    cra.area1.nodes.id  # in area1

    # Syntax that works for results_3di.nc also works here
    # E.g. get water level (s1) time series for node 23
    last_timestamp = cra.nodes.timestamps[-1]
    water_levels_23 = cra.nodes.filter(id__eq=23).timeseries(start_time=0, end_time=last_timestamp).s1


Functionalities
---------------

The functionalites are the same as for :ref:`results3di`, with the addition that you can query results for a specific area.

To list the available areas, use the `areas` property. To see the name of a specific area, use the `name` property of the area. See the examples above.
