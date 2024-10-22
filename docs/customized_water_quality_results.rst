.. _customized_wq_results3di:

customized_water_quality_results_3di.nc
=======================================

The customized water quality results file contains the same type of results as :ref:`wq_results3di`, but for a spatial selection of nodes, and for a selected list of variables. It is accessed through the ``CustomizedWaterQualityResultAdmin`` class.

Minimal example
---------------

.. code-block:: python

    from threedigrid.admin.gridresultadmin import CustomizedWaterQualityResultAdmin

    # Instantiate GridH5Admin and GridH5ResultAdmin objects
    gridadmin_filename = r"C:\3Di\My Model\gridadmin.h5"
    customized_wq_results_filename = r"C:\3Di\My Simulation\customized_water_quality_results_3di.nc"
    cwqra = CustomizedWaterQualityResultAdmin(gridadmin_filename, customized_water_quality_results_filename)

    # List the areas in this file
    cwqra.areas

    # See the name of area1
    cwqra.area1.name

    # List the available nodes
    cwqra.nodes.id  # in the whole file
    cwqra.area1.nodes.id  # in area1

    # Syntax that works for water_quality_results_3di.nc also works here
    # E.g., get the concentrations of all 2D open water nodes for substance1 during the first 4 hours of the simulation
    cwqra.substance1.subset('2d_open_water').timeseries(0, 4*60*60).concentration


Functionalities
---------------

The functionalites are the same as for :ref:`wq_results3di`, with the addition that you can query results for a specific area.

To list the available areas, use the `areas` property. To see the name of a specific area, use the `name` property of the area. See the examples above.
