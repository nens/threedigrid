Console scripts
---------------

3digrid_explore
^^^^^^^^^^^^^^^

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



3digrid_export
^^^^^^^^^^^^^^

To quickly export data of a model (or a models subset) you can use the 3digrid_export
shortcut. To get an overview of the options run::

    $ 3digrid_export --help

    Usage: 3digrid_export [OPTIONS]

    Options:
      --grid-file PATH                Path to the admin file
      --file-type [shape|gpkg]
      --output-file PATH              Path to the output file
      --model [nodes|lines|breaches|levees]
      --subset TEXT                   Filter by a subset like 1D_all (applies only
                                      for models nodes and lines
      --help                          Show this message and exit.

So to export the all 1D nodes::

    $ 3digrid_export --grid-file=<path to grid file> --file-type=shape --output-file=<name>.shp --model=nodes --subset=1d_all