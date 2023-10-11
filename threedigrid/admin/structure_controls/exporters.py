from threedigrid.admin.gridresultadmin import (
    GridH5StructureControl,
    _GridH5NestedStructureControl,
)
from threedigrid.admin.structure_controls.models import STRUCTURE_CONTROL_TYPES

import csv


def structure_control_actions_to_csv(
    structure_control: GridH5StructureControl, out_path: str
):
    with open(out_path, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=",")
        csv_writer.writerow(
            [
                "control_type",
                "id",
                "source_table",
                "source_table_id",
                "time",
                "action_type",
                "action_value_1",
                "action_value_2",
                "is_active",
            ]
        )
        for control_type in STRUCTURE_CONTROL_TYPES:
            control_type_data: _GridH5NestedStructureControl = getattr(
                structure_control, control_type
            )
            for (
                id,
                grid_id,
                time,
                action_type,
                action_value_1,
                action_value_2,
                is_active,
            ) in zip(
                control_type_data.id,
                control_type_data.grid_id,
                control_type_data.time,
                control_type_data.action_type,
                control_type_data.action_value_1,
                control_type_data.action_value_2,
                control_type_data.is_active,
            ):
                source_table, source_table_id = structure_control.get_source_table(
                    action_type, grid_id
                )
                csv_writer.writerow(
                    [
                        control_type,
                        id,
                        source_table,
                        source_table_id,
                        time,
                        action_type,
                        action_value_1,
                        action_value_2,
                        is_active,
                    ]
                )
