Introduction
============

What is ``threedigrid``
-----------------------

``threedigrid`` is a Python package that you can use to read the 3Di computational grid and simulation result files.

It allows you to efficiently read from the following files:

- Computational grid (:ref:`gridadmin`)

- 3Di Results (:ref:`results3di`)

- Aggregate 3Di Results (:ref:`aggregate_results3di`)

- Structure control actions logging (:ref:`structure_control_actions3di`)

- Water quality results (:ref:`wq_results3di`)

With threedigrid, you can query these files using pre-defined subsets, and spatial and non-spatial filters. You can also export model data to GIS formats like shapefile, geopackage, and geojson.

Installation
------------

If you want to make use of all capabilities threedigrid has to offer (e.g. spatial operations and command line tools), install like this:

.. code:: bash

    $ pip install threedigrid[geo,results]


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
    

Note on variable names
----------------------

For variables that are used in the 3Di computational core, threedigrid uses the same names as are used there. E.g., ``q`` for discharge, ``u1`` for velocity, ``dmax`` for bottom level, et cetera. It may be difficult to guess the meaning from these variable names, or vice versa, difficult to guess what the variable name for something is.

See the :ref:`gridadmin.h5<gridadmin_models>` section for an explanation of the names of attributes of 3Di model components.

In the :ref:`supported_files` section, the variables names used in each file interface are listed.