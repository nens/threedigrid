.. toctree::
   :maxdepth: 2
   :caption: Contents:

API Reference
=============

Admin
-----

.. automodule:: threedigrid.admin
   :members:

Breaches
++++++++

.. automodule:: threedigrid.admin.breaches
   :members:

.. automodule:: threedigrid.admin.breaches.models
   :members:

.. automodule:: threedigrid.admin.breaches.exporters
   :members:

Lines
+++++

.. automodule:: threedigrid.admin.lines
   :members:

.. automodule:: threedigrid.admin.lines.models
   :members:

.. automodule:: threedigrid.admin.lines.exporters
   :members:


Nodes
+++++

.. automodule:: threedigrid.admin.nodes
   :members:

.. automodule:: threedigrid.admin.nodes.models
   :members:


Model Meta options
------------------

A model can have a Meta class that accepts several options as input.
Meta options are used at this point mainly in the models that use the
``ResultMixin``.


``field_attrs``

Attributes for the given fields. 'units' for instance could yield 'm' [meters].
The attribute will be avaible throught the models ``_meta`` property. For example::

    >>> gr.nodes._meta.s1
    >>> s1(units=u'm', long_name=u'waterlevel', standard_name=u'water_surface_height_above_reference_datum')

``s1`` is a namedtuple so you can retrieve the units attribute by the the ``.`` notation ``gr.nodes._meta.s1.units``
or using the ``_as_dict`` method ``gr.nodes._meta.s1._asdict()['units']``


``composite_fields``

If a single model field is composed of multiple sources, you can use the
``composite_fields`` option to join those sources into a single model field.
The threedicore result netCDF file, for instance, is split into 1D and 2D subsets::

    >>> gr.nodes._datasource.keys()
    >>> ['Mesh2D_s1', 'Mesh1D_s1',...]

To map those source fields simply define a ``composite_fields`` dictionary::

    >>> composite_fields = {'s1': ['Mesh2D_s1', 'Mesh1D_s1'],}

This will add the field s1 to your ``nodes`` model.

.. note:: fields starting with '_' are private and will not be added to
    fields property


``lookup_fields``

A pair of fields of search_array and index_array. The search_array can be
used to lookup the indices from index_array.


.. autoclass:: threedigrid.orm.base.options.ModelMeta
   :members:


Example
+++++++

The ``NodesAggregateResultsMixin`` makes use of a ``base_composition``
and ``composition_vars`` setup.

The base_composition is equal to the fields in the result netcdf file. Those
are::


    BASE_COMPOSITE_FIELDS = {
        's1': ['Mesh2D_s1', 'Mesh1D_s1'],
        'vol': ['Mesh2D_vol', 'Mesh1D_vol'],
        'su': ['Mesh2D_su', 'Mesh1D_su'],
        'rain': ['Mesh2D_rain', 'Mesh1D_rain'],
        'q_lat': ['Mesh2D_q_lat', 'Mesh1D_q_lat'],
        '_mesh_id': ['Mesh2DNode_id', 'Mesh1DNode_id'],  # private
    }

The ``composition_vars``

.. code-block:: python

    composition_vars = {
        's1': ['min', 'max', 'avg'],
        'vol': ['max', 'cum'],
        'su': ['min'],
        'rain': ['avg'],
        'q_lat': ['cum'],
    }

define all possible combinations with those field names. ``s1`` and ``vol``
alone result in 10 field names.

    >>> Mesh2D_s1_min
    >>> Mesh1D_s1_min
    >>> Mesh2D_s1_max
    >>> Mesh1D_s1_max
    >>> Mesh2D_s1_avg
    >>> Mesh1D_s1_avg
    >>> Mesh2D_vol_max
    >>> Mesh1D_vol_max
    >>> Mesh2D_vol_cum
    >>> Mesh1D_vol_cum


Using the ``__metaclass__ = ModelMeta`` hook will compute all those
combinations automatically.

.. note:: The field names that are being added to the model instance will
    be a combination of the ``base_composition`` keys and the ``composition_vars``
    keys like ``s1_min``, ``s1_max`` etc


.. code-block:: python

    class NodesAggregateResultsMixin(ResultMixin):

        class Meta:
            __metaclass__ = ModelMeta

            base_composition = BASE_COMPOSITE_FIELDS

            # attributes for the given fields
            field_attrs = ['units', 'long_name']

            # extra vars that will be combined with the
            # composite fields, e.g.
            # s1 --> s1_min [Mesh2D_s1_min + Mesh1D_s1_min]
            #    --> s1_max  [Mesh2D_s1_max + Mesh1D_s1_max]
            composition_vars = {
                's1': ['min', 'max', 'avg'],
                'vol': ['max', 'cum'],
                'su': ['min'],
                'rain': ['avg'],
                'q_lat': ['cum'],
            }

            lookup_fields = ('id', '_mesh_id')


ORM
---

.. _fields-label:

Fields
++++++

.. automodule:: threedigrid.orm.base.fields
   :members:


Model _meta API
---------------

.. autoclass:: threedigrid.orm.base.options.Options
   :members: get_field, get_fields, add_field, add_fields
