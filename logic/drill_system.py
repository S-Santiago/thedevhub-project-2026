from dataclasses import dataclass
from typing import Dict, Tuple

from enums import Direction
from settings import (
    MATERIALS,
    DRILL_DEFAULT_CYCLE_SECONDS,
    DRILL_OUTPUT_BUFFER_CAPACITY,
)


def _drill_cycle_seconds(mineral_kind: str) -> float:
    mineral_cfg = MATERIALS.get(mineral_kind, {})
    value = mineral_cfg.get("drill_cycle_seconds", DRILL_DEFAULT_CYCLE_SECONDS)
    return float(value) if value and value > 0 else DRILL_DEFAULT_CYCLE_SECONDS


@dataclass
class DrillMachine:
    x: int
    y: int
    direction: object
    mineral_kind: str
    cycle_seconds: float
    buffer_capacity: int = DRILL_OUTPUT_BUFFER_CAPACITY

    def __post_init__(self):
        if self.direction is None:
            self.direction = Direction.RIGHT
        self.progress_seconds = 0.0
        self.buffer_items = 0

    def update(self, delta_time: float, conveyor_system) -> None:
        if self.buffer_items < self.buffer_capacity:
            self.progress_seconds += delta_time

            while self.progress_seconds >= self.cycle_seconds and self.buffer_items < self.buffer_capacity:
                self.progress_seconds -= self.cycle_seconds
                self.buffer_items += 1

        self._try_output(conveyor_system)

    def _try_output(self, conveyor_system) -> None:
        if self.buffer_items <= 0:
            return

        if self.direction is None:
            self.direction = Direction.RIGHT

        dx, dy = self.direction.value
        target_x = self.x + dx
        target_y = self.y + dy

        if conveyor_system.place_material(target_x, target_y, self.mineral_kind):
            self.buffer_items -= 1


class DrillSystem:
    def __init__(self) -> None:
        self._grid: Dict[Tuple[int, int], DrillMachine] = {}

    def add_drill(self, drill: DrillMachine) -> None:
        self._grid[(drill.x, drill.y)] = drill

    def remove_drill(self, x: int, y: int) -> None:
        self._grid.pop((x, y), None)

    def get_drill(self, x: int, y: int):
        return self._grid.get((x, y))

    def create_drill(self, x: int, y: int, direction, mineral_kind: str) -> DrillMachine:
        if direction is None:
            direction = Direction.RIGHT
        return DrillMachine(
            x=x,
            y=y,
            direction=direction,
            mineral_kind=mineral_kind,
            cycle_seconds=_drill_cycle_seconds(mineral_kind),
        )
    def update(self, delta_time: float, conveyor_system) -> None:
        for drill in list(self._grid.values()):
            drill.update(delta_time, conveyor_system)

    def __repr__(self) -> str:
        return f"DrillSystem({len(self._grid)} drills)"

    def iter_drills(self):
        """Iterador público sobre los taladros: devuelve ((x,y), drill)."""
        return iter(self._grid.items())

    def __len__(self):
        return len(self._grid)
