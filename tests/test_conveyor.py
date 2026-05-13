from pathlib import Path
import sys
from enum import Enum

# Ensure workspace root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logic.conveyor import ConveyorBelt, ConveyorSystem


class DummyDir(Enum):
    RIGHT = (1, 0)
    LEFT = (-1, 0)
    UP = (0, -1)
    DOWN = (0, 1)


def test_conveyor_transfer():
    system = ConveyorSystem()

    a = ConveyorBelt(0, 0, DummyDir.RIGHT)
    b = ConveyorBelt(1, 0, DummyDir.RIGHT)

    system.add_belt(a)
    system.add_belt(b)

    placed = system.place_material(0, 0, "IRON")
    assert placed
    assert not a.is_empty

    # Advance enough time to trigger transfer (speed=1.0 by default)
    system.update(1.1)

    assert a.is_empty
    assert not b.is_empty
    assert b.item is not None
    assert b.item.kind == "IRON"
