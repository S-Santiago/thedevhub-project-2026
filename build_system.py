from enums import Direction
from logic.conveyor import ConveyorBelt, ConveyorCurve
from logic.inventory import MACHINE_INVENTORY

MACHINE_CONVEYOR = "CONVEYOR"
MACHINE_DRILL = "DRILL"
AVAILABLE_MACHINES = (MACHINE_CONVEYOR, MACHINE_DRILL, MACHINE_INVENTORY)

_DIRECTION_ORDER = (
    Direction.RIGHT,
    Direction.DOWN,
    Direction.LEFT,
    Direction.UP,
)


def rotate_machine_direction(direction):
    """Devuelve la siguiente dirección en sentido horario para colocar máquinas.

    direction: valor del enum `Direction`.
    """
    if direction not in _DIRECTION_ORDER:
        return Direction.RIGHT

    index = _DIRECTION_ORDER.index(direction)
    return _DIRECTION_ORDER[(index + 1) % len(_DIRECTION_ORDER)]


def rotate_machine_direction_ccw(direction):
    """Devuelve la siguiente dirección en sentido antihorario para colocar máquinas.

    direction: valor del enum `Direction`.
    """
    if direction not in _DIRECTION_ORDER:
        return Direction.RIGHT

    index = _DIRECTION_ORDER.index(direction)
    return _DIRECTION_ORDER[(index - 1) % len(_DIRECTION_ORDER)]


def rotate_conveyor_direction(direction):
    """Alias compatible: rota la dirección de la cinta en sentido horario."""
    return rotate_machine_direction(direction)


def screen_to_tile(mouse_pos, offset_x, offset_y, tile_size):
    """Convierte coordenadas de pantalla (píxeles) a coordenadas de tile.

    Devuelve una tupla `(tx, ty)` con la celda correspondiente.
    """
    mouse_x, mouse_y = mouse_pos
    world_x = mouse_x - offset_x
    world_y = mouse_y - offset_y
    return int(world_x // tile_size), int(world_y // tile_size)


def _place_conveyor(map_manager, conveyor_system, tile_x, tile_y, selected_direction, selected_in_direction=None):
    if conveyor_system is None:
        return False

    if conveyor_system.get_belt(tile_x, tile_y) is not None:
        return False

    if not map_manager.place_machine(tile_x, tile_y, MACHINE_CONVEYOR):
        return False

    # Determinar entrada (incoming): si se especifica `selected_in_direction` usarla,
    # en caso contrario detectar una cinta vecina que apunte a esta casilla.
    incoming = selected_in_direction
    if incoming is None:
        try:
            for d in Direction:
                dx, dy = d.value
                neighbor = conveyor_system.get_belt(tile_x - dx, tile_y - dy)
                if neighbor is not None and neighbor.direction == d:
                    incoming = d
                    break
        except Exception:
            incoming = None

    # Persistir metadatos de dirección en map_manager.machine_overrides para mantener la rotación
    try:
        map_manager.machine_overrides[(tile_x, tile_y)] = {"machine": MACHINE_CONVEYOR, "direction": getattr(selected_direction, "name", str(selected_direction)), "in_direction": getattr(incoming, "name", None) if incoming else None}
    except Exception:
        pass

    # Si incoming y salida difieren, crear una curva explícita
    try:
        if incoming is not None and incoming != selected_direction:
            conveyor_system.add_belt(ConveyorCurve(tile_x, tile_y, selected_direction, incoming))
        else:
            conveyor_system.add_belt(ConveyorBelt(tile_x, tile_y, selected_direction, incoming_direction=incoming))
    except Exception:
        # Fallback sencillo
        conveyor_system.add_belt(ConveyorBelt(tile_x, tile_y, selected_direction, incoming_direction=incoming))
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


def _place_inventory(map_manager, inventory_system, tile_x, tile_y):
    """Coloca un inventario (cofre) en la celda y registra la máquina en el InventorySystem."""
    if inventory_system is None:
        return False

    if inventory_system.get_inventory(tile_x, tile_y) is not None:
        return False

    tile = map_manager.get_tile(tile_x, tile_y, ensure_chunk=True)
    if tile is None:
        return False

    if not map_manager.place_machine(tile_x, tile_y, MACHINE_INVENTORY):
        return False

    # Persistir metadatos: asignar asset del cofre existente en los assets de CONVEYOR (Cofre.png)
    try:
        map_manager.machine_overrides[(tile_x, tile_y)] = {"machine": MACHINE_INVENTORY, "asset_key": "CONVEYOR_COFRE"}
    except Exception:
        pass

    # Registrar en el sistema de inventarios
    try:
        inventory_system.create_inventory(tile_x, tile_y)
    except Exception:
        pass

    return True


def place_selected_machine(
    map_manager,
    conveyor_system,
    tile_x,
    tile_y,
    selected_machine,
    selected_direction,
    drill_system=None,
    selected_in_direction=None,
    inventory_system=None,
):
    """Coloca la máquina seleccionada si la casilla y los sistemas lo permiten.

    Devuelve True si la colocación tuvo éxito, False en caso contrario.
    """
    if selected_machine == MACHINE_CONVEYOR:
        return _place_conveyor(
            map_manager,
            conveyor_system,
            tile_x,
            tile_y,
            selected_direction,
            selected_in_direction=selected_in_direction,
        )

    if selected_machine == MACHINE_DRILL:
        return _place_drill(
            map_manager,
            drill_system,
            tile_x,
            tile_y,
            selected_direction,
        )

    if selected_machine == MACHINE_INVENTORY:
        return _place_inventory(map_manager, inventory_system, tile_x, tile_y)

    return False
