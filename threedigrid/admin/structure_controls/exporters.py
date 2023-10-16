import csv

from threedigrid.admin.gridresultadmin import (
    _GridH5NestedStructureControl,
    GridH5StructureControl,
)
from threedigrid.admin.structure_controls.models import StructureControlTypes


def structure_control_actions_to_csv(
    structure_control: GridH5StructureControl, out_path: str
):
    """Set place table, timed, and memory controls after each other in one file."""
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
        for control_type in StructureControlTypes.__members__.values():
            control_type_data: _GridH5NestedStructureControl = getattr(
                structure_control, control_type.name
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
                        control_type.value,
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
