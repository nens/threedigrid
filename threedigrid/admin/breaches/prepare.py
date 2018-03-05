# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function

import ogr
import numpy as np
from threedigrid.admin import constants


def as_numpy_array(array):
    if hasattr(array, 'value'):
        return array.value
    return array


class PrepareBreaches(object):
    @staticmethod
    def get_coordinates(levees, line_coords, levl):
        breaches_x = np.zeros(levl.shape, dtype='f8')
        breaches_y = np.zeros(levl.shape, dtype='f8')

        for i, line_id in enumerate(levl):
            if i == 0:
                continue
            line = ogr.Geometry(ogr.wkbLineString)

            line.AddPoint(
                line_coords[0][line_id],
                line_coords[1][line_id])
            line.AddPoint(
                line_coords[2][line_id],
                line_coords[3][line_id])

            for levee_geom in levees.geoms:
                if not levee_geom.Intersect(line):
                    continue
                intersection = levee_geom.Intersection(line)
                breaches_x[i] = intersection.GetX()
                breaches_y[i] = intersection.GetY()
                break

        return np.array([breaches_x, breaches_y])

    @classmethod
    def prepare_datasource(cls, datasource, kcu, id_mapper,
                           levees, line_coords):
        # TODO: Check values below
        if 'id' not in datasource.keys():
            datasource.set(
                'id', np.arange(0, datasource['levl'].size))

        if 'seq_ids' not in datasource.keys():
            datasource.set(
                'seq_ids', np.arange(0, datasource['levl'].size))
        if 'content_pk' not in datasource.keys():
            content_pk = np.zeros(datasource['levl'].shape, dtype='i4')
            type_code = constants.TYPE_CODE_MAP['v2_breach']
            id_mapping = id_mapper.id_mapping
            src = id_mapper.obj_slices[type_code]
            sort_by = as_numpy_array(datasource['seq_ids'])
            sort_idx = np.argsort(sort_by)
            idx = sort_idx[np.searchsorted(
                sort_by,
                id_mapping[src]['seq_id'],
                sorter=sort_idx)]

            content_pk[idx] = id_mapping[src]['pk']
            datasource.set('content_pk', content_pk)

        levl = as_numpy_array(datasource['levl'])

        if 'kcu' not in datasource.keys():
            datasource.set('kcu', as_numpy_array(kcu)[levl])

        if 'coordinates' not in datasource.keys() and levees:
            datasource.set(
                'coordinates',
                cls.get_coordinates(levees, as_numpy_array(line_coords), levl))
