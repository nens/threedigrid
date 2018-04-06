.. highlight:: shell

============
Installation
============

Stable release
--------------

The standard threedigrid distribution is pretty lightweight, installing as little dependencies
as possible. If you want to make use of all capabilities threedigrid has to ofter (e.g. spatial
operations and command line tools) install like this::

    $ pip install threedigrid[geo]

If you want to use the ogr exporters you'll also need to install the python gdal bindings.
There are several ways to accomplish this, see the following thread for an overview:

 https://gis.stackexchange.com/questions/9553/installing-gdal-and-ogr-for-python

This is the preferred method to install threedigrid, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for threedigrid can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/nens/threedigrid

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/nens/threedigrid/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/nens/threedigrid
.. _tarball: https://github.com/nens/threedigrid/tarball/master
