# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import pytest

from threedigrid.admin.gridresultadmin import GridH5ResultAdmin
from threedigrid.orm.base.options import ModelMeta
import six

test_file_dir = os.path.join(
    os.getcwd(), "tests/test_files")

# the testfile is a copy of the v2_bergermeer gridadmin file
result_file = os.path.join(test_file_dir, "results_3di.nc")
grid_file = os.path.join(test_file_dir, "gridadmin.h5")


@pytest.fixture()
def gr():
    gr = GridH5ResultAdmin(grid_file, result_file)
    yield gr
    gr.close()


def test_combine_vars():
    a = {'a', 'b'}
    b = {'c', 'd'}
    result = ModelMeta.combine_vars(a, b, '_')
    assert set(result) == {'a_c', 'a_d', 'b_c', 'b_d'}


def test_combine_vars_empty_set():
    a = {'a', 'b'}
    b = {}
    result = ModelMeta.combine_vars(a, b, '_')
    assert result == []


def test_combine_vars_invalid_combinator():
    a = {'a', 'b'}
    b = {'c'}
    with pytest.raises(TypeError):
        ModelMeta.combine_vars(a, b, 5)


BASE_COMPOSITE_FIELDS = {
    'au': ['Mesh2D_au', 'Mesh1D_au'],
    'u1': ['Mesh2D_u1', 'Mesh1D_u1'],
    'q': ['Mesh2D_q', 'Mesh1D_q'],
    '_mesh_id': ['Mesh2DLine_id', 'Mesh1DLine_id'],  # private
}


@pytest.fixture()
def mm_composite():
    class TestMetaComposition(object):

        class Meta(six.with_metaclass(ModelMeta)):
            composite_fields = {
                'au': ['Mesh2D_au', 'Mesh1D_au'],
            }

    tmc = TestMetaComposition()
    yield tmc


@pytest.fixture()
def mm_base_composite():
    class TestMetaBase(object):

        class Meta(six.with_metaclass(ModelMeta)):
            base_composition = {
                'q': ['Mesh2D_q', 'Mesh1D_q'],
            }

            composition_vars = {
                'q': ['cum', 'cum_positive', 'cum_negative'],
            }

    tmc = TestMetaBase()
    yield tmc


def test_meta_error():
    # must define a composite_fields dict
    with pytest.raises(AttributeError):
        class TestMetaComposition(object):
            class Meta(six.with_metaclass(ModelMeta)):
                pass

        TestMetaComposition()


def test_meta_composite(mm_composite):
    assert mm_composite.Meta.composite_fields == {
        'au': ['Mesh2D_au', 'Mesh1D_au']}


def test_meta_base_composition(mm_base_composite):
    assert {'q_cum', 'q_cum_positive', 'q_cum_negative'} == set(
        mm_base_composite.Meta.composite_fields.keys())
    import itertools
    assert set(list(itertools.chain(
        *list(mm_base_composite.Meta.composite_fields.values())))) == {
        'Mesh2D_q_cum', 'Mesh1D_q_cum', 'Mesh2D_q_cum_positive',
        'Mesh1D_q_cum_positive', 'Mesh2D_q_cum_negative',
        'Mesh1D_q_cum_negative'
    }
