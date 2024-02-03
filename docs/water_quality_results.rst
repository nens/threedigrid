.. _wq_results3di:

water_quality_results_3di.nc
============================

If a simulation includes substance concentrations, the results (concentrations at nodes at each output time step) are written to a water_quality_results_3di.nc file. This file can be accessed through the ``GridH5WaterQualityResultAdmin`` class.

Each substance that is used in the simulation (1 .. *n*), can be accessed as a ``Nodes`` object by calling ``gwq.substance1`` .. ``gwq.substancen``  

Minimal example
---------------
.. code-block:: python
    
    from threedigrid.admin.gridresultadmin import GridH5WaterQualityResultAdmin    
    
    # Instantiate GridH5WaterQualityResultAdmin object
    gridadmin_filename = r"C:\3Di\My Model\gridadmin.h5"
    water_quality_results_filename = r"C:\3Di\My Simulation\water_quality_results_3di.nc"
    gwq = GridH5WaterQualityResultAdmin(gridadmin_filename, water_quality_results_filename)

    # Get the concentrations of all 2D open water nodes for substance1 during the first 4 hours of the simulation
    gwq.substance1.subset('2d_open_water').timeseries(0, 4*60*60).concentration


Attribute names
---------------

The attribute names inherited from the :ref:`nodes` class and an attribute ``concentration`` is added.

