from enum import Enum
from typing import List


class StructureControlTypes(Enum):
    table_control = "table_control"
    memory_control = "memory_control"
    timed_control = "timed_control"


class StructureControl:
    def __init__(
        self,
        id: str,
        source_table: str,
        source_table_id: int,
        time: List[float],
        action_type: str,
        action_value_1: List[float],
        action_value_2: List[float],
        is_active: List[int],
    ) -> None:
        self.id = id
        self.source_table = source_table
        self.source_table_id = source_table_id
        self.time = time
        self.action_type = action_type
        self.action_value_1 = action_value_1
        self.action_value_2 = action_value_2
        self.is_active = is_active
