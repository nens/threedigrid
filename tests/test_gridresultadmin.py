from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import unittest
import tempfile
import shutil

import numpy as np
import ogr

from threedigrid.admin.gridadmin import GridH5Admin
from threedigrid.admin.nodes.exporters import CellsOgrExporter
from threedigrid.admin.nodes.exporters import NodesOgrExporter
from threedigrid.admin.lines.exporters import LinesOgrExporter
from threedigrid.admin.breaches.exporters import BreachesOgrExporter
from threedigrid.admin.constants import SUBSET_1D_ALL
from threedigrid.admin.constants import SUBSET_2D_OPEN_WATER
from threedigrid.admin.constants import NO_DATA_VALUE

test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
grid_admin_h5_file = os.path.join(test_file_dir, "subgrid_map.nc")

# >> > from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
# >> > nc = "/code/tests/test_files/subgrid_map.nc"
# >> > f = "/code/tests/test_files/gridadmin.h5"
# >> > gr = GridH5ResultAdmin(f, nc)
# >> > qs_s1 = gr.nodes.timeseries(indexes=[1, 2, 3]).s1
# >> > qs_s1.shape
# >> > (3, 25156)
#
