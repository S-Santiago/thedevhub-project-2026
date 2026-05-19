from dataclasses import dataclass
from typing import Dict, Tuple
import random

from enums import Direction
from settings import (
    MATERIALS,
    DRILL_DEFAULT_CYCLE_SECONDS,
    DRILL_OUTPUT_BUFFER_CAPACITY,
)
from sound_manager import get_sound_manager
from audio_culling import get_audio_culling_manager


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
        # Desincronizar drills con un offset aleatorio en el ciclo (0 a cycle_seconds)
        # Esto evita que todos ejecuten en el mismo frame y causa picos de sonido/procesamiento
        self.progress_seconds = random.uniform(0.0, self.cycle_seconds)
        self.buffer_items = 0
        # Flag para audio culling: indica si este drill está audible en la cámara
        self.is_audible = True

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
            # Solo reproducir sonido si el drill está dentro del viewport de la cámara (Audio Culling)
            if self.is_audible:
                try:
                    sound_manager = get_sound_manager()
                    pitch = random.uniform(0.9, 1.1)  # Variar pitch para evitar monotonía
                    sound_manager.play_machine_sound("mineral", "extracted", pitch=pitch)
                except Exception:
                    # Si hay error al reproducir sonido, continuar sin fallar
                    pass


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

    def update_audibility(self) -> None:
        """
        Actualiza el estado de audibilidad de todos los drills según el Audio Culling Manager.
        
        Debe llamarse después de actualizar el frustum en AudioCullingManager.
        Operación O(n) pero muy rápida: solo comparaciones de enteros.
        """
        audio_culling = get_audio_culling_manager()
        for (x, y), drill in self._grid.items():
            drill.is_audible = audio_culling.is_audible(x, y)

    def __repr__(self) -> str:
        return f"DrillSystem({len(self._grid)} drills)"

    def iter_drills(self):
        """Iterador público sobre los taladros: devuelve ((x,y), drill)."""
        return iter(self._grid.items())

    def __len__(self):
        return len(self._grid)
