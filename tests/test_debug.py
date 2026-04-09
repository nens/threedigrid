import os

import numpy as np
import pytest

from threedigrid.admin.gridresultadmin import GridH5DebugResultAdmin

test_file_dir = os.path.join(os.path.dirname(__file__), "test_files", "debug")
grid_admin_path = os.path.join(test_file_dir, "gridadmin.h5")
debug_result_path = os.path.join(test_file_dir, "debug_results_3di.nc")


@pytest.fixture
def gb():
    gb = GridH5DebugResultAdmin(grid_admin_path, debug_result_path)
    yield gb
    gb.close()


def test_value_retrieval(gb):
    assert gb.lines.timeseries(indexes=slice(None)).cfl.shape == (3601, 1809)


def test_get_model_instance_by_field_name(gb):
    model = gb.get_model_instance_by_field_name("cfl")
    assert np.array_equal(
        gb.lines.timeseries(indexes=slice(None)).cfl,
        model.timeseries(indexes=slice(None)).cfl,
    )
    with pytest.raises(IndexError):
        gb.get_model_instance_by_field_name("nonexisting")
