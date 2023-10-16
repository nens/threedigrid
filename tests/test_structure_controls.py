import os
from typing import List

import pytest
from numpy.testing import assert_array_equal

from threedigrid.admin.gridresultadmin import GridH5StructureControl
from threedigrid.admin.structure_controls.exporters import (
    structure_control_actions_to_csv,
)
from threedigrid.admin.structure_controls.models import StructureControl

test_file_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "test_files/structure_controls"
)
result_file = os.path.join(test_file_dir, "structure_control_actions_3di.nc")
grid_file = os.path.join(test_file_dir, "gridadmin.h5")


@pytest.fixture()
def gsc():
    gsc = GridH5StructureControl(grid_file, result_file)
    yield gsc
    gsc.close()


def test_group_by_id(gsc: GridH5StructureControl):
    struct_cntrl: StructureControl = gsc.table_control.group_by_id(
        "tablepumpcapacity_3_0_3153600000"
    )

    assert struct_cntrl.id == "tablepumpcapacity_3_0_3153600000"
    assert struct_cntrl.source_table == "v2_pumpstation"
    assert struct_cntrl.source_table_id == 2
    assert_array_equal(struct_cntrl.time, [0, 202, 602, 1202, 2002])
    assert struct_cntrl.action_type == "set_pump_capacity"
    assert_array_equal(struct_cntrl.action_value_1, [0.0, 0.1, 0.0, 0.2, 0.0])
    assert_array_equal(struct_cntrl.action_value_2, [0.0, 0.0, 0.0, 0.0, 0.0])
    assert_array_equal(struct_cntrl.is_active, [1, 1, 1, 1, 1])


def test_group_by_id_0(gsc: GridH5StructureControl):
    struct_cntrl: StructureControl = gsc.table_control.group_by_id("x")
    assert struct_cntrl is None


def test_group_by_action_type(gsc: GridH5StructureControl):
    struct_cntrls: List[StructureControl] = gsc.table_control.group_by_action_type(
        "set_pump_capacity"
    )
    assert len(struct_cntrls) == 2
    assert isinstance(struct_cntrls[0], StructureControl)
    assert struct_cntrls[0].id == "tablepumpcapacity_2_0_3153600000"
    assert struct_cntrls[1].id == "tablepumpcapacity_3_0_3153600000"


def test_group_by_is_active(gsc: GridH5StructureControl):
    struct_cntrls: List[StructureControl] = gsc.table_control.group_by_is_active(0)
    assert len(struct_cntrls) == 1
    assert struct_cntrls[0].id == "tablecrestlevel_1_0_3153600000"


def test_group_by_time(gsc: GridH5StructureControl):
    struct_cntrls: List[StructureControl] = gsc.table_control.group_by_time(241, 599)
    assert len(struct_cntrls) == 2
    assert struct_cntrls[0].id == "tablecrestlevel_1_0_3153600000"
    assert struct_cntrls[1].id == "tablepumpcapacity_2_0_3153600000"


def test_group_by_time_incorrect(gsc: GridH5StructureControl):
    struct_cntrls: List[StructureControl] = gsc.table_control.group_by_time(10, 0)
    assert len(struct_cntrls) == 0


def test_group_by_action_value(gsc: GridH5StructureControl):
    struct_cntrls: List[StructureControl] = gsc.table_control.group_by_action_value_1(
        0, 0.1
    )
    assert len(struct_cntrls) == 3
    assert struct_cntrls[0].id == "tablecrestlevel_1_0_3153600000"
    assert struct_cntrls[1].id == "tablepumpcapacity_2_0_3153600000"
    assert struct_cntrls[2].id == "tablepumpcapacity_3_0_3153600000"


def test_group_by_action_value_2(gsc: GridH5StructureControl):
    struct_cntrls: List[StructureControl] = gsc.table_control.group_by_action_value_2(
        0, 0
    )
    assert len(struct_cntrls) == 3
    assert struct_cntrls[0].id == "tablecrestlevel_1_0_3153600000"
    assert struct_cntrls[1].id == "tablepumpcapacity_2_0_3153600000"
    assert struct_cntrls[2].id == "tablepumpcapacity_3_0_3153600000"


def test_group_by_action_value_negative(gsc: GridH5StructureControl):
    struct_cntrls: List[StructureControl] = gsc.table_control.group_by_action_value_1(
        -1, -0.1
    )
    assert len(struct_cntrls) == 1
    assert struct_cntrls[0].id == "tablecrestlevel_1_0_3153600000"


def test_export_method(gsc):
    csv_path = os.path.join(test_file_dir, "test_struct_control_actions.csv")
    structure_control_actions_to_csv(gsc, csv_path)
    assert os.path.exists(csv_path)
