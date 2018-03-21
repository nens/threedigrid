API documentation
=================

Introduction
------------

One of the main challenges of the 3Di backend is the efficient combination of different
data sources, as well as different abstraction levels. The grid administration itself
is not sufficient for showing meaningful information for the end user in a GUI because
the data he or she has modeled has been re-designed and re-shaped for purposes of numerical
calculations only. Therefore one of the main tasks for the grid admin object was to be able
to translate to user defined data and visa versa. Ideally the fortran produced admin file
would be read and append by the python code. Luckily, hdf5 is able to do exactly this

    > HDF5 is a data model, library, and file format for storing and managing data.
    It supports an unlimited variety of datatypes, and is designed for flexible and
    efficient I/O and for high volume and complex data. HDF5 is portable and is
    extensible, allowing applications to evolve in their use of HDF5. The HDF5
    Technology suite includes tools and applications for managing, manipulating,
    viewing, and analyzing data in the HDF5 format.


The benefits of this approach are divers (to name the most important):
    - the HDF5 Fortran Library is well documented and tested
    - both parts of the application can contribute to the same file.
    - the file itself is annotated, thus self describing,
    - the file can be viewed with basic command line tools like h5dump*,
    - the data is persistent and portable, and can be compressed;
    - when data is read from the file it acts like standard numpy arrays (in most situations, see drawbacks)

Most python scientific libraries support hdf5: The pandas I/O API has a top level reader/writer for hfd5 files.
Dask reads in hdf5 datasets as easily as::

    f = h5py.File('myfile.hdf5')
    dset = f['/data/path']

    import dask.array as da
    x = da.from_array(dset, chunks=(1000, 1000))

Also pytables has a hdf5 driver. This makes it extremely versatile format that allows for adaptation of other
techniques whenever needed. The 3Di API is build on vanilla hdf5.

The API itself is inspired by the django query language that allows for filtering model objects.
The model is the source of information about an entity. It contains the data of that entity and
describes its behaviour. In django each model essentially is a mapping to a database table. In
the grid admin a model maps to a hdf5 group. The group itself has been populated with data from
different sources but once the data is there is has the same function as a django model.

Models
------

The threedicore consists of three main data types: grid cells, flow lines and calculation nodes.
Not so surprisingly, these data structures are described in form of models which basically is a
container for structured, annotated data. The basic definition of a model looks like this::

    class Lines(Model):
        kcu = ArrayField()
        lik = ArrayField()
        line = IndexArrayField(to='Nodes')
        line_geometries = MultiLineArrayField()

The most important functionality exposed by a model instance, obviously, is:
filtering, geo transformations, data serialisation and data export.


Filtering
---------

There are different types of filters but a filter, generally speaking, acts on field. That means you can
filter by value. If you have a line model instance you can filter the data by the kcu field::

    ga.lines.filter(kcu__in=[100,102])

or by the lik value::

    ga.lines.filter(lik__eq=4)

The filtering is lazy, that is, to retrieve data you have to call data explicitly::

    ga.lines.filter(lik__eq=4).data  # will return an ordered dict


**Spatial filters**

The grid admin is also able to perform some basic spatial operations. Those are

    - in_tile
    - in_bbox
    - contains_point
    - intersects_tile
    - intersects_bbox

*Warning: The geospatial filters only works on data in non-spherical projections.*

The ``contains_point`` filter for instance, can be used to identify a grid cell in which
a given point falls::

    ga.cells.filter(cell_coords__contains_point=xy).id

Spatial filtering works only on GeomArrayField subclasses.


Subsets
-------
Subsets are a easy way to retrieve categorized sub parts of the data.

As mentioned earlier, the three main data types of the threedicore are grid cells, flow lines
and calculation nodes. Calculation nodes normally are located in the center of a grid cell.
Calculation nodes are connected with each other by flow lines. These data are organized in
form of arrays, contiguous, ordered fields of the same data type. Different parts of the array can be
categorized. In other words: they form subsets. The API allows the user to define its own subsets,
but there are also some predefined subsets available

So see if a model has any predefined subset you can call the ``known_subset`` property::

    In [6]: ga.lines.known_subset
    Out[6]:
    [u'ACTIVE_BREACH',
     u'2D_OPEN_WATER',
     u'1D',
     u'SHORT_CRESTED_STRUCTURES',
     u'2D_GROUNDWATER',
     u'LONG_CRESTED_STRUCTURES',
     u'1D2D',
     u'2D_VERTICAL_INFILTRATION',
     u'1D_ALL',
     u'2D_ALL',
     u'2D_OPEN_WATER_OBSTACLES',
     u'GROUNDWATER_ALL']

To retrieve data of a subset use the ``subset()`` method like so::

    ga.lines.subset('1D_ALL').data  # remember, all filtering is lazy

Fields
------


**ArrayField**

The most basic/generic field is an ArrayField. It can be used to describe values that are to be retrieved from a (hdf5) Datasource.

**IndexArrayField(ArrayField)**

Used to annotate a foreign key relationship to another field (can not be used for look ups, though)

**GeomArrayField(ArrayField)**

Base geometry field, allows spatial filters.

**PointArrayField(GeomArrayField)**

Used for representing point geometries. Implements the reproject method.

Also see :ref:`fields-label`


Serializers
-----------

The API includes Geojson serializers to convert model data to
geojson. Serializers can be used on models that have filtering/subset and reprojection,
for example generating the geojson of all 2D open water channels in WGS84::

    from threedigrid.admin.lines.serializers import ChannelsGeoJsonSerializer

    channels_wgs84 = ga.lines.channels.subset('1D_ALL').reproject_to('4326')

    channels_wgs84_geojson = ChannelsGeoJsonSerializer(channels_wgs84).data


Exporters
---------

Like serializers, exporters allow to export model data to files. For example exporting
all 2D open water lines in WGS84 into a shape file::

    from threedigrid.admin.lines.exporters import LinesOgrExporter

    line_2d_open_water_wgs84 = ga.lines.subset('2D_OPEN_WATER').reproject_to('4326')

    exporter = LinesOgrExporter(line_2d_open_water_wgs84)
    exporter.save('/tmp/line.shp', line_2d_open_water_wgs84.data, '4326')


Note: most models have shortcut methods for exporting their data for shape files and geopackages, like::

    # Shape file
    ga.lines.subset('2D_OPEN_WATER').reproject_to('4326').to_shape('/tmp/line.shp')

    # Geopackage file
    ga.lines.subset('2D_OPEN_WATER').reproject_to('4326').to_gpkg('/tmp/line.gpkg')
