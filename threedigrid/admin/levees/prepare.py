# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

from __future__ import absolute_import
import numpy as np
import h5py


DT_VARIABLE = h5py.special_dtype(vlen=np.dtype('float64'))


class PrepareLevees(object):
    @staticmethod
    def prepare_datasource(h5py_file, threedi_datasource):
        v2_levee_instances = threedi_datasource.levees
        group_name = 'levees'
        if group_name not in h5py_file:
            gr = h5py_file.create_group(group_name)
        else:
            gr = h5py_file['levees']

        dset_coords = gr.create_dataset(
            'coords', (len(v2_levee_instances),), dtype=DT_VARIABLE
        )
        dset_clevel = gr.create_dataset(
            'crest_level', (len(v2_levee_instances),), dtype='f8'
        )
        dset_mbreach_depth = gr.create_dataset(
            'max_breach_depth', (len(v2_levee_instances),), dtype='f8'
        )
        dset_id = gr.create_dataset(
            'id', (len(v2_levee_instances),), dtype='i4'
        )
        for i, levee in enumerate(v2_levee_instances):
            # "F" means to flatten in column-major (Fortran- style) order
            dset_coords[i] = np.array(
                levee.the_geom.coords).flatten('F')
            dset_clevel[i] = levee.crest_level
            dset_mbreach_depth[i] = levee.max_breach_depth or -9999
            dset_id[i] = levee.pk
