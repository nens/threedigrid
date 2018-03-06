===========
threedigrid
===========



.. image:: https://travis-ci.org/nens/threedigrid.svg?branch=master
        :target: https://travis-ci.org/larsclaussen/threedigrid


.. image:: https://readthedocs.org/projects/threedigrid/badge/?version=latest
        :target: https://threedigrid.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status



Python package for the threedigrid administration.


* Free software: BSD license
* Documentation: https://threedigrid.readthedocs.io.


Features
========
 - access to the threedicore administration by a single instance of the ``GridH5Admin`` object
 - query the model data by pre-defined subsets and django style filters
 - export model data to gis formats like shapefile, geopackage
 - serialize model data as geojson


Installation
============

Using pip::

    $ pip install threedigrid

To be able to use the full range of features you need to install the python gdal bindings.
There are several ways to accomplish this, see the following thread for an overview:

 https://gis.stackexchange.com/questions/9553/installing-gdal-and-ogr-for-python


Quick start
===========

Get a grid admin instance::

    from threedigrid import GridH5Admin

    f = 'gridadmin.h5'
    ga = GridH5Admin(f)


The grid admin directly holds some model specific attributes like whether the model has a 1D or 2D
or groundwater section::

    In [4]: ga.has_groundwater
    Out[4]: False

    In [5]: ga.has_1d
    Out[5]: True


Filtering
---------

There are different types of filters but a filter, generally speaking, acts on field. That means you can
filter by value. If you have a line model instance you can filter the data by the kcu field::

    ga.lines.filter(kcu__in=[100,102])

or by the lik value::

    ga.lines.filter(lik__eq=4)

The filtering is lazy, that is, to retrieve data you have to call data explicitly::

    ga.lines.filter(lik__eq=4).data  # will return an ordered dict



Tests
=====

Tests can be run best in a docker container::

   $ cd <project_root>
   $ docker build -t threedigrid:test .
   $ docker run --rm threedigrid:test pytest --cov=threedigrid --flake8



Credits
=======

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
