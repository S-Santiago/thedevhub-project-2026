from enums import Direction
from logic.conveyor import ConveyorBelt

MACHINE_CONVEYOR = "CONVEYOR"
MACHINE_DRILL = "DRILL"
AVAILABLE_MACHINES = (MACHINE_CONVEYOR, MACHINE_DRILL)

_DIRECTION_ORDER = (
    Direction.RIGHT,
    Direction.DOWN,
    Direction.LEFT,
    Direction.UP,
)


def rotate_machine_direction(direction):
    """Return the next clockwise direction for machine placement."""
    if direction not in _DIRECTION_ORDER:
        return Direction.RIGHT

    index = _DIRECTION_ORDER.index(direction)
    return _DIRECTION_ORDER[(index + 1) % len(_DIRECTION_ORDER)]


def rotate_conveyor_direction(direction):
    """Backward-compatible alias."""
    return rotate_machine_direction(direction)


def screen_to_tile(mouse_pos, offset_x, offset_y, tile_size):
    """Translate screen pixels to tile coordinates."""
    mouse_x, mouse_y = mouse_pos
    world_x = mouse_x - offset_x
    world_y = mouse_y - offset_y
    return int(world_x // tile_size), int(world_y // tile_size)


def _place_conveyor(map_manager, conveyor_system, tile_x, tile_y, selected_direction):
    if conveyor_system is None:
        return False

    if conveyor_system.get_belt(tile_x, tile_y) is not None:
        return False

    if not map_manager.place_machine(tile_x, tile_y, MACHINE_CONVEYOR):
        return False

    conveyor_system.add_belt(ConveyorBelt(tile_x, tile_y, selected_direction))
    return True


def _place_drill(map_manager, drill_system, tile_x, tile_y, selected_direction):
    if drill_system is None:
        return False

    if drill_system.get_drill(tile_x, tile_y) is not None:
        return False

    tile = map_manager.get_tile(tile_x, tile_y, ensure_chunk=True)
    if tile is None:
        return False

    mineral_kind = tile.get("mineral")
    if not mineral_kind:
        return False

    if not map_manager.place_machine(tile_x, tile_y, MACHINE_DRILL):
        return False

    drill = drill_system.create_drill(tile_x, tile_y, selected_direction, mineral_kind)
    drill_system.add_drill(drill)
    return True


def place_selected_machine(
    map_manager,
    conveyor_system,
    tile_x,
    tile_y,
    selected_machine,
    selected_direction,
    drill_system=None,
):
    """Place selected machine if the target tile and systems allow it."""
    if selected_machine == MACHINE_CONVEYOR:
        return _place_conveyor(
            map_manager,
            conveyor_system,
            tile_x,
            tile_y,
            selected_direction,
        )

    if selected_machine == MACHINE_DRILL:
        return _place_drill(
            map_manager,
            drill_system,
            tile_x,
            tile_y,
            selected_direction,
        )

    return False
