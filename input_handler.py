import pygame

from build_system import (
    MACHINE_CONVEYOR,
    MACHINE_DRILL,
    place_selected_machine,
    rotate_machine_direction,
    screen_to_tile,
)
from enums import Direction
import GUI


def process_event(
    event: pygame.event.Event,
    state: dict,
    load_images: callable,
    MIN_TILE_SIZE: int,
    MAP_SIZE: int,
    flags,
    display_idx,
    screen,
    map_manager=None,
    conveyor_system=None,
    drill_system=None,
):
    # Se asume que `state` es un diccionario y se muta en sitio
    if event.type == pygame.QUIT:
        state["running"] = False
        return screen, None

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            state["running"] = False
            return screen, None

        # Seleccion de maquina (por ahora solo conveyor)
        if event.key == pygame.K_1:
            state["selected_machine"] = MACHINE_CONVEYOR
            return screen, None

        # Deseleccionar para navegar sin construir
        if event.key == pygame.K_0:
            state["selected_machine"] = None
            return screen, None

        if event.key == pygame.K_2:
            state["selected_machine"] = MACHINE_DRILL
            return screen, None

        # Rotar direccion de colocacion
        # Rotar direccion de colocacion: R = rotar derecha (horario), Shift+R = rotar izquierda (antihorario)
        if event.key == pygame.K_r:
            mods = pygame.key.get_mods()
            current_direction = state.get("selected_direction", Direction.RIGHT)
            if mods & pygame.KMOD_SHIFT:
                from build_system import rotate_machine_direction_ccw

                state["selected_direction"] = rotate_machine_direction_ccw(current_direction)
            else:
                state["selected_direction"] = rotate_machine_direction(current_direction)

            return screen, None

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        # Si hay un menú contextual abierto, priorizar su selección
        context_menu = state.get("context_menu")
        if context_menu is not None:
            idx = GUI.menu_hit_test(context_menu, event.pos)
            if idx is not None:
                opt = context_menu["options"][idx]
                action = opt.get("action")
                if action == "rotate_cw":
                    current_direction = state.get("selected_direction", Direction.RIGHT)
                    state["selected_direction"] = rotate_machine_direction(current_direction)

                elif action == "rotate_ccw":
                    # evitar dependencia circular importando la función localmente
                    from build_system import rotate_machine_direction_ccw

                    current_direction = state.get("selected_direction", Direction.RIGHT)
                    state["selected_direction"] = rotate_machine_direction_ccw(current_direction)

                elif action == "delete":
                    # Eliminar cualquier máquina en la celda del menú (cinta o taladro)
                    tile = context_menu.get("tile")
                    if tile is not None and map_manager is not None:
                        tx, ty = tile
                        if conveyor_system is not None:
                            conveyor_system.remove_belt(tx, ty)
                        if drill_system is not None:
                            drill_system.remove_drill(tx, ty)
                        map_manager.clear_machine(tx, ty)

                elif opt.get("machine") is not None:
                    # seleccionar máquina y, si viene, la dirección asociada
                    state["selected_machine"] = opt.get("machine")
                    if opt.get("direction") is not None:
                        state["selected_direction"] = opt.get("direction")

                # Cerrar menú después de la acción
                state["context_menu"] = None
            else:
                # clic fuera del menú lo cierra
                state["context_menu"] = None

            return screen, None

        # Clic izquierdo para construir cuando hay maquina seleccionada
        selected_machine = state.get("selected_machine")

        if selected_machine and map_manager is not None and conveyor_system is not None:
            tile_x, tile_y = screen_to_tile(
                event.pos,
                state["offset_x"],
                state["offset_y"],
                state["tile_size"],
            )

            selected_direction = state.get("selected_direction", Direction.RIGHT)
            place_selected_machine(
                map_manager,
                conveyor_system,
                tile_x,
                tile_y,
                selected_machine,
                selected_direction,
                drill_system,
            )

        return screen, None

    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
        # Clic derecho: abrir menú contextual de construcción
        tile_x, tile_y = screen_to_tile(
            event.pos,
            state["offset_x"],
            state["offset_y"],
            state["tile_size"],
        )

        options = [
            {"label": "Conveyor ↑", "machine": MACHINE_CONVEYOR, "direction": Direction.UP},
            {"label": "Conveyor →", "machine": MACHINE_CONVEYOR, "direction": Direction.RIGHT},
            {"label": "Conveyor ↓", "machine": MACHINE_CONVEYOR, "direction": Direction.DOWN},
            {"label": "Conveyor ←", "machine": MACHINE_CONVEYOR, "direction": Direction.LEFT},
            {"label": "Drill", "machine": MACHINE_DRILL},
            {"label": "Delete", "action": "delete"},
            {"label": "Rotar derecha (R)", "action": "rotate_cw"},
            {"label": "Rotar izquierda (Shift+R)", "action": "rotate_ccw"},
            {"label": "Cancel", "action": "cancel"},
        ]

        state["context_menu"] = {"pos": event.pos, "tile": (tile_x, tile_y), "options": options}
        return screen, None

    if event.type == pygame.MOUSEWHEEL:
        zoom_factor = 1.1 if event.y > 0 else 0.9

        mouse_x, mouse_y = pygame.mouse.get_pos()

        map_x = mouse_x - state["offset_x"]
        map_y = mouse_y - state["offset_y"]

        new_tile_size = int(state["tile_size"] * zoom_factor)
        new_tile_size = max(MIN_TILE_SIZE, min(new_tile_size, 200))

        if new_tile_size != state["tile_size"]:
            scale = new_tile_size / state["tile_size"]
            state["offset_x"] = mouse_x - (map_x * scale)
            state["offset_y"] = mouse_y - (map_y * scale)
            state["offset_x_f"] = float(state["offset_x"])
            state["offset_y_f"] = float(state["offset_y"])

            state["tile_size"] = new_tile_size
            imagenes = load_images(new_tile_size)
            state["map_pixel_size"] = new_tile_size * MAP_SIZE

            if state["window_width"] < state["min_window_width"] or state["window_height"] < state["min_window_height"]:
                state["window_width"] = max(state["window_width"], state["min_window_width"])
                state["window_height"] = max(state["window_height"], state["min_window_height"])
                state["offset_x"] = (state["window_width"] - state["map_pixel_size"]) // 2
                state["offset_y"] = (state["window_height"] - state["map_pixel_size"]) // 2
                state["offset_x_f"] = float(state["offset_x"])
                state["offset_y_f"] = float(state["offset_y"])
                screen = pygame.display.set_mode((state["window_width"], state["window_height"]), flags, display=display_idx)

            # Después de hacer zoom, puede que necesitemos generar/podar chunks si hay map_manager
            if map_manager is not None:
                map_manager.ensure_and_prune_for_view(state["offset_x"], state["offset_y"], state["tile_size"], state["window_width"], state["window_height"])
            return screen, imagenes

    if event.type == pygame.VIDEORESIZE:
        # Asegurar tamaño mínimo en base al mapa en zoom normal
        min_w = state["baseline_map_pixel_size"]
        min_h = state["baseline_map_pixel_size"]

        new_w = max(event.w, min_w)
        new_h = max(event.h, min_h)

        state["window_width"] = int(new_w)
        state["window_height"] = int(new_h)
        state["offset_x"] = (state["window_width"] - state["map_pixel_size"]) // 2
        state["offset_y"] = (state["window_height"] - state["map_pixel_size"]) // 2
        state["offset_x_f"] = float(state["offset_x"])
        state["offset_y_f"] = float(state["offset_y"])
        screen = pygame.display.set_mode((state["window_width"], state["window_height"]), flags, display=display_idx)

        if map_manager is not None:
            map_manager.ensure_and_prune_for_view(state["offset_x"], state["offset_y"], state["tile_size"], state["window_width"], state["window_height"])

        return screen, None

    return screen, None
