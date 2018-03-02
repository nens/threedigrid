===========
threedigrid
===========


.. image:: https://img.shields.io/pypi/v/threedigrid.svg
        :target: https://pypi.python.org/pypi/threedigrid

.. image:: https://img.shields.io/travis/larsclaussen/threedigrid.svg
        :target: https://travis-ci.org/larsclaussen/threedigrid

.. image:: https://readthedocs.org/projects/threedigrid/badge/?version=latest
        :target: https://threedigrid.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Grid Admin Python package.


* Free software: BSD license
* Documentation: https://threedigrid.readthedocs.io.


Installation
------------

To be able to use the full range of features you need to install the python gdal bindings.
There are several ways to accomplish this, see the following thread for an overview:

 https://gis.stackexchange.com/questions/9553/installing-gdal-and-ogr-for-python


Docker
------

To run threedigrid in a docker::

   $ cd <project_root>
   $ docker build .
   $ docker run -it <image id> ipython

To run the tests in the docker same steps as above, then::
    $ docker run -it <image id> pytest tests

Features
--------
 - access to the threedicore administration by a single instance of the ``GridH5Admin`` object
 - query the model data by pre-defined subsets and django style filters
 - export model data to gis formats like shapefile, geopackage
 - serialize model data as geojson

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
