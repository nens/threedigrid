Threedigrid: The 3Di grid admin framework
=========================================

The Python package for the threedigrid administration.


.. image:: https://travis-ci.org/nens/threedigrid.svg?branch=master
        :target: https://travis-ci.org/larsclaussen/threedigrid


.. image:: https://readthedocs.org/projects/threedigrid/badge/?version=latest
        :target: https://threedigrid.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status



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


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
