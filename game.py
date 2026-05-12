import pygame
import platform

from settings import (
    APP_ID,
    APP_NAME,
    MAP_SIZE,
    MIN_TILE_SIZE,
    CAMERA_SPEED,
    USER_OPTIONS,
    ASSETS_PATH,
)

from build_system import MACHINE_CONVEYOR
from map_manager import MapManager
from asset_manager import load_images
from renderer import render_frame
from input_handler import process_event
from logic.conveyor import ConveyorSystem
from logic.drill_system import DrillSystem
from enums import Direction


def run():
    if platform.system() == "Windows":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)

    pygame.init()
    pygame.display.set_caption(APP_NAME)

    # Intentar cargar el icono si existe (no crítico)
    try:
        game_icon = pygame.image.load(f"{ASSETS_PATH}/icon.png")
        pygame.display.set_icon(game_icon)
    except Exception:
        pass

    # Configuración de pantalla
    screens = pygame.display.get_desktop_sizes()
    selected_screen = USER_OPTIONS["screen"]

    display_idx = 0
    if selected_screen <= len(screens):
        display_idx = selected_screen - 1

    tile_size = MIN_TILE_SIZE
    baseline_map_pixel_size = MIN_TILE_SIZE * MAP_SIZE

    if USER_OPTIONS["fullscreen"]:
        window_width, window_height = screens[display_idx]
        tile_size = window_height // MAP_SIZE
    else:
        window_width = tile_size * MAP_SIZE
        window_height = tile_size * MAP_SIZE

    map_pixel_size = tile_size * MAP_SIZE
    min_window_width = baseline_map_pixel_size
    min_window_height = baseline_map_pixel_size

    offset_x = (window_width - map_pixel_size) // 2
    offset_y = (window_height - map_pixel_size) // 2

    flags = pygame.FULLSCREEN if USER_OPTIONS["fullscreen"] else pygame.RESIZABLE
    screen = pygame.display.set_mode((window_width, window_height), flags, display=display_idx)

    clock = pygame.time.Clock()

    # Carga de datos (ahora por chunks)
    map_manager = MapManager()
    images = load_images(tile_size)
    
    # Inicializar el sistema de cintas
    conveyor_system = ConveyorSystem()
    drill_system = DrillSystem()

    # Asegurar chunks iniciales centrados en la vista actual
    map_manager.ensure_chunks_for_view(offset_x, offset_y, tile_size, window_width, window_height)
    tiles = map_manager.get_merged_tiles()

    state = {
        "running": True,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "offset_x_f": float(offset_x),
        "offset_y_f": float(offset_y),
        "tile_size": tile_size,
        "window_width": window_width,
        "window_height": window_height,
        "map_pixel_size": map_pixel_size,
        "baseline_map_pixel_size": baseline_map_pixel_size,
        "min_window_width": min_window_width,
        "min_window_height": min_window_height,
        "camera_speed": CAMERA_SPEED,
        "selected_machine": MACHINE_CONVEYOR,
        "selected_direction": Direction.RIGHT,
        "selected_in_direction": None,
    }
    
    dt = 0.0

    while state["running"]:
        dt = clock.tick(USER_OPTIONS["fps"]) / 1000.0
        for event in pygame.event.get():
            screen, new_images = process_event(
                event,
                state,
                load_images,
                MIN_TILE_SIZE,
                MAP_SIZE,
                flags,
                display_idx,
                screen,
                map_manager,
                conveyor_system,
                drill_system,
            )

            if new_images is not None:
                images = new_images

        keys = pygame.key.get_pressed()
        move_x = 0
        move_y = 0

        # Se mueve la cámara, no el cursor: A/W/S/D desplazan el mundo.
        if keys[pygame.K_a]:
            move_x += 1
        if keys[pygame.K_d]:
            move_x -= 1
        if keys[pygame.K_w]:
            move_y += 1
        if keys[pygame.K_s]:
            move_y -= 1

        if move_x != 0 or move_y != 0:
            state["offset_x_f"] += move_x * state["camera_speed"] * dt
            state["offset_y_f"] += move_y * state["camera_speed"] * dt
            state["offset_x"] = int(state["offset_x_f"])
            state["offset_y"] = int(state["offset_y_f"])

            map_manager.ensure_and_prune_for_view(
                state["offset_x"],
                state["offset_y"],
                state["tile_size"],
                state["window_width"],
                state["window_height"],
            )

        conveyor_system.update(dt)
        drill_system.update(dt, conveyor_system)

        # Preparar información de debug
        mx, my = pygame.mouse.get_pos()
        wx = mx - state["offset_x"]
        wy = my - state["offset_y"]
        tx = None
        ty = None
        tile_under = None

        # Obtener sólo tiles visibles para el viewport actual (mejora rendimiento)
        left = -state["offset_x"]
        top = -state["offset_y"]
        right = left + state["window_width"]
        bottom = top + state["window_height"]

        tile_left = int(left // state["tile_size"])
        tile_top = int(top // state["tile_size"])
        tile_right = int(right // state["tile_size"])
        tile_bottom = int(bottom // state["tile_size"])

        tiles = map_manager.get_tiles_in_rect(tile_left, tile_top, tile_right, tile_bottom)

        if wx is not None and wy is not None:
            tx = int(wx // state["tile_size"])
            ty = int(wy // state["tile_size"])
            tile_under = tiles.get((tx, ty))

        # Calcular previsualización: si hay una máquina seleccionada y un tile bajo el cursor,
        # indicamos si es posible colocar ahí según las reglas de MapManager.
        preview = None
        sel_machine = state.get("selected_machine")
        sel_direction = state.get("selected_direction")
        if sel_machine is not None and tx is not None and ty is not None:
            can_place = map_manager.can_place_machine(tx, ty)
            
            # Detectar dirección entrante automáticamente (igual que en _place_conveyor)
            in_direction = state.get("selected_in_direction")
            if in_direction is None and sel_machine == "CONVEYOR" and conveyor_system is not None:
                try:
                    for d in Direction:
                        dx, dy = d.value
                        neighbor = conveyor_system.get_belt(tx - dx, ty - dy)
                        if neighbor is not None and neighbor.direction == d:
                            in_direction = d
                            break
                except Exception:
                    in_direction = None
            
            preview = {
                "tile": (tx, ty),
                "machine": sel_machine,
                "direction": sel_direction,
                "in_direction": in_direction,
                "can_place": can_place,
            }

        debug_info = {
            "fps": round(clock.get_fps(), 1),
            "mouse_screen": (mx, my),
            "mouse_world": (wx, wy),
            "tile": (tx, ty),
            "tile_data": tile_under,
            "seed": map_manager.base_seed,
            "selected_machine": state.get("selected_machine"),
            "selected_direction": state.get("selected_direction"),
            "belts": len(conveyor_system),
            "drills": len(drill_system),
            "preview": preview,
        }

        render_frame(
            screen,
            tiles,
            images,
            state["tile_size"],
            state["offset_x"],
            state["offset_y"],
            debug_info,
            conveyor_system,
            drill_system,
            state.get("context_menu"),
        )
        

    pygame.quit()
