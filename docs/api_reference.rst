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

result attributes for the given fields


``composite_fields``

values of *_COMPOSITE_FIELDS are the variables names as known in
the result netCDF file. They are split into 1D and 2D subsets.
As threedigrid has its own subsection ecosystem they are merged
into a single field (e.g. the keys of *_COMPOSITE_FIELDS).

N.B. # fields starting with '_' are private and will not be added to
fields property


``lookup_fields``

A pair of fields of search_array and index_array. The search_array can be
used to lookup the indices from index_array.



ORM
---

.. _fields-label:

Fields
++++++

.. automodule:: threedigrid.orm.base.fields
   :members:


Model _meta API
---------------

.. automodule:: threedigrid.orm.base.options
   :members: get_field, get_fields, add_field, add_fields
