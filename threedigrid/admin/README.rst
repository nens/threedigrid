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

**Non spatial filters**

This is an overview of the different basic filters that are available:

    - eq ("Equals")
    - ne: ("Not equals")
    - gt: ("Greater than")
    - gte: ("Greater than equals")
    - lt: ("Less than")
    - lte': ("Less than equals")
    - in: ("In collection")

**Spatial filters**

The grid admin is also able to perform some basic spatial operations. Those are

    - in_tile
    - in_bbox
    - contains_point
    - intersects_tile
    - intersects_bbox
    - intersects_geometry

*Warning: The geospatial filters only works on data in non-spherical projections.*

The ``contains_point`` filter for instance, can be used to identify a grid cell in which
a given point falls::

    ga.cells.filter(cell_coords__contains_point=xy).id

The ``intersects_geometry`` expects a shapely geometry for which the intersection will be determined::

    from shapely.geometry import Polygon
    polygon = Polygon([
        [109300.0, 518201.2], [108926.5, 518201.2], [108935.6, 517871.7], [109300.0, 518201.2]
    ])
    ga.cells.filter(cell_coords__intersects_geometry=geometry)

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

**TimeSeriesArrayField(ArrayField)**

Field to store time series arrays,

**TimeSeriesCompositeArrayField(TimeSeriesArrayField)**

A time series field can be composed of two or more fields in the source file.
The threedicore result netCDF file for instance has split their node and line
data into subsets for the 1D and 2D parts of the threedi model. A composite
field can be used to combine those source fields into a single model field
by specifying a composition dict. Example::

        LINE_COMPOSITE_FIELDS = {
            'au': ['Mesh1D_au', 'Mesh2D_au'],
            'u1': ['Mesh1D_u1', 'Mesh2D_u1'],
            'q': ['Mesh1D_q', 'Mesh2D_q']
        }

``au``, ``u1`` and ``q`` will thus be added to the lines model fields.


Also see :ref:`fields-label`


Exporters
---------

Exporters allow to export model data to files. For example exporting
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


Results
-------

The threedigrid admin can also be used to query results of the threedicore.
Results are written to a netCDF file that contains data like water depth,
flow velocity and such. This data is linked to the same entities we're already
familiar with like calculation nodes and flow links.

To query these results you can use ``GridH5ResultAdmin``, an object very
similar to the ``GridH5Admin``. It takes both the gridadmin file and the
results netcdf as input parameters::

    >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
    >>> nc = "/code/tests/test_files/subgrid_map.nc"
    >>> f = "/code/tests/test_files/gridadmin.h5"
    >>> gr = GridH5ResultAdmin(f, nc)

It has properties we already know like ``has_breaches`` or ``has_1d``. It
also holds the same fields from the ``GridH5Admin``. Those fields have been
extended by a set of result fields, like s1 for nodes for example::

    In [8]: gr.nodes._meta.get_fields(only_names=True)
    Out[8]:
    [u'zoom_category',
     u'content_pk',
     u'vol',
     u'seq_id',
     u's1',
     u'rain',
     u'id',
     u'node_type',
     u'su',
     u'q_lat',
     u'coordinates',
     u'cell_coords']


A query that includes TimeSeriesArrayField fields or fields derived from this
type by default will yield a time series chunk of 10. The default can be
altered by calling::

    >>> gr.set_timeseries_chunk_size(50)

To see the current setting::

    >>> gr.timeseries_chunk_size


The most common use case however, will be defining custom queries using the
timeseries* filter itself. There are two ways the time series filter can be
applied, either using the ``start_time`` and ``end_time`` keywords or a custom
index.

Example usage for start_time and end_time filter::

    >>> from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
    >>> nc = "/code/tests/test_files/subgrid_map.nc"
    >>> f = "/code/tests/test_files/gridadmin.h5"
    >>> gr = GridH5ResultAdmin(f, nc)
    >>> qs = gr.nodes.timeseries(start_time=0, end_time=40)  # lazy


The filtering is lazy, to retrieve the query results call ``qs.data`` or if you
are interested in a specific field like ``s1`` for instance, call ``qs.s1``.
You can see how many timesteps are captured by calling qs.s1.shape::

    >>> qs.s1.shape
    >>> (2, 15604)

Please note, querying large portions of the time dimension can consume lot's of
memory so use with caution. See the :ref:`benchmarks-label` for more details.

The result fields can only be filtered by chunks of time at this point and
not by the logical operators like 'eq', 'gt' etc. To extract this kind of
information you can make use of numpy and its tools. To get the maximum
water depth of the first 4 time steps and their corresponding node ids::

    >>> # get a timeserie
    >>> t = gr.nodes.timeseries(indexes=[2,3,4,5])
    >>> # limit the fields to whatever you are interested in
    >>> s1_id = t.only('s1', 'id').data
    >>> zip(s1_id['id'][np.argmax(s1_id['s1'], axis=1)], np.max(s1_id['s1'], axis=1))
    >>>  [(13115, -0.40000000596046448),
         (0, 5.0013032438928677),
         (0, 5.0016998451768755),
         (0, 5.0020966845033916)]


.. _benchmarks-label:

Benchmarks
++++++++++


Run on::

     *-memory
          description: System memory
          size: 15GiB
     *-cpu
          product: Intel(R) Core(TM) i7-7700HQ CPU @ 2.80GHz
          vendor: Intel Corp.
          size: 1109MHz
          capacity: 3800MHz
          width: 64 bits


Getting all fields::


    In [18]: %timeit %memit gr.nodes.timeseries(start_time=0, end_time=100).data
    peak memory: 113.65 MiB, increment: 5.54 MiB
    peak memory: 113.87 MiB, increment: 0.01 MiB
    peak memory: 113.87 MiB, increment: 0.00 MiB
    peak memory: 113.87 MiB, increment: 0.00 MiB
    1 loop, best of 3: 198 ms per loop

    In [19]: %timeit %memit gr.nodes.timeseries(start_time=0, end_time=1000).data
    peak memory: 150.76 MiB, increment: 36.89 MiB
    peak memory: 150.76 MiB, increment: 0.00 MiB
    peak memory: 150.76 MiB, increment: 0.00 MiB
    peak memory: 150.76 MiB, increment: 0.00 MiB
    1 loop, best of 3: 215 ms per loop

    In [20]: %timeit %memit gr.nodes.timeseries(start_time=0, end_time=10000).data
    peak memory: 343.04 MiB, increment: 192.29 MiB
    peak memory: 306.43 MiB, increment: 159.59 MiB
    peak memory: 314.81 MiB, increment: 167.97 MiB
    peak memory: 308.24 MiB, increment: 161.40 MiB
    1 loop, best of 3: 511 ms per loop

    In [21]: %timeit %memit gr.nodes.timeseries(start_time=0, end_time=100000).data
    peak memory: 2520.57 MiB, increment: 2373.73 MiB
    peak memory: 2524.54 MiB, increment: 2352.19 MiB
    peak memory: 2512.11 MiB, increment: 2341.73 MiB
    peak memory: 2522.84 MiB, increment: 2361.71 MiB
    1 loop, best of 3: 6.15 s per loop



Getting a single field::

    In [23]: %timeit %memit gr.nodes.timeseries(start_time=0, end_time=1000).s1
    peak memory: 155.47 MiB, increment: 9.55 MiB
    peak memory: 155.47 MiB, increment: 0.00 MiB
    peak memory: 155.47 MiB, increment: 0.00 MiB
    peak memory: 155.47 MiB, increment: 0.00 MiB
    1 loop, best of 3: 201 ms per loop

    In [24]: %timeit %memit gr.nodes.timeseries(start_time=0, end_time=10000).s1
    peak memory: 220.41 MiB, increment: 64.88 MiB
    peak memory: 215.97 MiB, increment: 71.15 MiB
    peak memory: 223.68 MiB, increment: 78.86 MiB
    peak memory: 217.91 MiB, increment: 73.09 MiB
    1 loop, best of 3: 330 ms per loop

    In [25]: %timeit %memit gr.nodes.timeseries(start_time=0, end_time=100000).s1
    peak memory: 918.97 MiB, increment: 774.10 MiB
    peak memory: 908.92 MiB, increment: 756.00 MiB
    peak memory: 917.43 MiB, increment: 764.51 MiB
    peak memory: 922.58 MiB, increment: 769.66 MiB
    1 loop, best of 3: 1.31 s per loop

