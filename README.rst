Threedigrid: The 3Di grid admin framework
=========================================

The Python package for the threedigrid administration.


.. image:: https://github.com/nens/threedigrid/workflows/Linux/badge.svg
	:alt: Github Actions status
	:target: https://github.com/nens/threedigrid/actions/workflows/test.yml?query=branch%3Amaster


.. image:: https://readthedocs.org/projects/threedigrid/badge/?version=latest
        :target: https://threedigrid.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. PyPI

.. image:: https://img.shields.io/pypi/v/threedigrid.svg
	:alt: PyPI
	:target: https://pypi.org/project/threedigrid/

.. Anaconda

.. image:: https://img.shields.io/conda/vn/conda-forge/threedigrid
  :alt: Anaconda
  :target: https://anaconda.org/conda-forge/threedigrid


* Free software: BSD license
* Documentation: https://threedigrid.readthedocs.io.

Overview
========

Features
--------
- access to the threedicore administration by a single instance of the ``GridH5Admin`` object
- query the model data by pre-defined subsets and django style filters
- export model data to gis formats like shapefile, geopackage
- serialize model data as geojson


Quick start
-----------

The standard threedigrid distribution is pretty lightweight, installing as little dependencies
as possible. If you want to make use of all capabilities threedigrid has to ofter (e.g. spatial
operations and command line tools) install like this::

    $ pip install threedigrid[geo,results]


Console scripts
+++++++++++++++

Using the 3digrid_explore shortcut, simply run::

    $ 3digrid_explore --grid-file=<path to grid file> --ipy

This will invoke an ipython session with a ``GridH5Admin`` instance already loaded.

To get a quick overview of the threedimodels meta data omit the ``--ipy`` option or
explicitly run::

    $ 3digrid_explore --grid-file=<the to grid file> --no-ipy

This will give you output like this::

    Overview of model specifics:

    model slug:              v2_bergermeer-v2_bergermeer_bres_maalstop-58-b1f8179f1f3c2333adb08c9e6933fa7b9a8cd163
    threedicore version:     0-20180315-3578e9b-1
    threedi version:         1.63.dev0
    has 1d:                  True
    has 2d:                  True
    has groundwater:         True
    has levees:              True
    has breaches:            True
    has pumpstations:        True


(I)Python shell
+++++++++++++++
Get a grid admin instance::

    from threedigrid.admin.gridadmin import GridH5Admin

    f = 'gridadmin.h5'
    ga = GridH5Admin(f)


The grid admin directly holds some model specific attributes like whether the model has a 1D or 2D
or groundwater section::

    In [4]: ga.has_groundwater
    Out[4]: False

    In [5]: ga.has_1d
    Out[5]: True



There are different types of filters but a filter, generally speaking, acts on field. That means you can
filter by value. If you have a line model instance you can filter the data by the kcu field::

    ga.lines.filter(kcu__in=[100,102])

or by the lik value::

    ga.lines.filter(lik__eq=4)

The filtering is lazy, that is, to retrieve data you have to call data explicitly::

    ga.lines.filter(lik__eq=4).data  # will return an ordered dict


The structure control actions netcdf can also be analyzed and exported using threedigrid::

    from threedigrid.admin.gridresultadmin import GridH5StructureControl
    from threedigrid.admin.structure_controls.exporters import structure_control_actions_to_csv

    gst = GridH5StructureControl("gridadmin.h5", "structure_control_actions_3di.nc")
    gst.table_control
    structure_control_actions_to_csv(gst, "test.csv")

Remote procedure calls
----------------------

Currently only the client-side is included. The server-side might be added in a later stage.
Note: this is an advanced feature used inside the 3Di stack, probably you don't need this.
Note2: you need Python 3.7 or higher for this to work.


Installation::

    $ pip install threedigrid[rpc]


Basic usage::

    ga = GridH5ResultAdmin('rpc://REDIS_HOST/SIMULATION_ID', 'rpc://REDIS_HOST/SIMULATION_ID')
    # Replace REDIS_HOST and SIMULATION_ID with actual values.
    future_result = ga.nodes.filter(lik__eq=4).data
    data = await future_result.resolve()

Subscription usage::

    subscription = await future_result.subscribe()

    async for item in subscription.enumerate():
          # do something with item


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
