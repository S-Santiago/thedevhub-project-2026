from pathlib import Path
import sys

# Ensure workspace root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from build_system import MACHINE_CONVEYOR, MACHINE_DRILL
from enums import Direction
from map_manager import MapManager
from logic.conveyor import ConveyorSystem
from logic.drill_system import DrillSystem


def test_save_creates_save_structure_and_chunk_file(tmp_path):
    manager = MapManager(base_seed=123, chunk_size=4, margin=0, save_root=tmp_path)

    meta = manager.loadMapFromJSON()

    save_dir = tmp_path / "partida1"
    assert not save_dir.exists()
    assert meta["name"] == "partida1"

    assert manager.saveMapToJSON() is False
    assert not save_dir.exists()

    assert manager.get_tile(0, 0, ensure_chunk=True) is not None
    assert manager.saveMapToJSON() is False
    chunk_file = save_dir / "chunks" / "0_0" / "data.json"
    assert not chunk_file.exists()

    assert manager.place_machine(
        0,
        0,
        MACHINE_CONVEYOR,
        machine_data={"machine": MACHINE_CONVEYOR, "direction": "RIGHT", "in_direction": "UP"},
    )

    assert save_dir.exists()
    assert (save_dir / "meta.json").exists()
    assert chunk_file.exists()

    import json

    with chunk_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert payload["buildings"]
    assert payload["buildings"][0]["machine"] == MACHINE_CONVEYOR
    assert payload["buildings"][0]["direction"] == "RIGHT"


def test_save_and_load_restores_structures(tmp_path):
    manager = MapManager(base_seed=123, chunk_size=4, margin=0, save_root=tmp_path)
    manager.loadMapFromJSON()

    assert manager.get_tile(0, 0, ensure_chunk=True) is not None
    assert manager.place_machine(
        0,
        0,
        MACHINE_CONVEYOR,
        machine_data={"machine": MACHINE_CONVEYOR, "direction": "RIGHT", "in_direction": "UP"},
    )
    assert manager.place_machine(
        1,
        0,
        MACHINE_DRILL,
        machine_data={"machine": MACHINE_DRILL, "direction": "DOWN", "mineral": "COAL"},
    )

    manager.saveMapToJSON()

    import json

    with (tmp_path / "partida1" / "chunks" / "0_0" / "data.json").open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert payload["buildings"]
    assert "tiles" not in payload or payload["tiles"] == {}

    reloaded = MapManager(base_seed=999, chunk_size=4, margin=0, save_root=tmp_path)
    reloaded.loadMapFromJSON()

    tile = reloaded.get_tile(0, 0, ensure_chunk=False)
    assert tile is not None
    assert tile["machine"]["machine"] == MACHINE_CONVEYOR
    assert tile["machine"]["direction"] == "RIGHT"

    drill_tile = reloaded.get_tile(1, 0, ensure_chunk=False)
    assert drill_tile is not None
    assert drill_tile["machine"]["machine"] == MACHINE_DRILL
    assert drill_tile["machine"]["mineral"] == "COAL"

    conveyor_system = ConveyorSystem()
    drill_system = DrillSystem()
    reloaded.restore_structures(conveyor_system, drill_system)

    belt = conveyor_system.get_belt(0, 0)
    assert belt is not None
    assert belt.direction == Direction.RIGHT
    assert drill_system.get_drill(1, 0) is not None