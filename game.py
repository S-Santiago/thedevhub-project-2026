import pygame
import platform

from settings import (
    APP_ID,
    APP_NAME,
    MAP_SIZE,
    MIN_TILE_SIZE,
    USER_OPTIONS,
    ASSETS_PATH,
)

from map_generator import generate_map
from map_manager import MapManager
from asset_manager import load_images
from renderer import render_frame
from input_handler import process_event
from logic.conveyor import ConveyorSystem, ConveyorBelt
from enums import Direction
from enum import Enum


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
    
    # --------- CINTAS DE PRUEBA --------------------------------
    conveyor_system.add_belt(ConveyorBelt(5, 5, Direction.RIGHT))
    conveyor_system.add_belt(ConveyorBelt(6, 5, Direction.RIGHT))
    conveyor_system.place_material(5, 5, "IRON")

    # Asegurar chunks iniciales centrados en la vista actual
    map_manager.ensure_chunks_for_view(offset_x, offset_y, tile_size, window_width, window_height)
    tiles = map_manager.get_merged_tiles()

    state = {
        "is_dragging": False,
        "last_mouse_pos": (0, 0),
        "running": True,
        "offset_x": offset_x,
        "offset_y": offset_y,
        "tile_size": tile_size,
        "window_width": window_width,
        "window_height": window_height,
        "map_pixel_size": map_pixel_size,
        "baseline_map_pixel_size": baseline_map_pixel_size,
        "min_window_width": min_window_width,
        "min_window_height": min_window_height,
    }
    
    dt = 0.0

    while state["running"]:
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
            )

            if new_images is not None:
                images = new_images

        conveyor_system.update(dt)

        # Preparar información de debug
        mx, my = pygame.mouse.get_pos()
        wx = mx - state["offset_x"]
        wy = my - state["offset_y"]
        tx = None
        ty = None
        tile_under = None

        # Obtener tiles cacheadas (la generación ahora se dispara desde input_handler en MOUSEMOTION)
        tiles = map_manager.get_merged_tiles()

        if wx is not None and wy is not None:
            tx = int(wx // state["tile_size"])
            ty = int(wy // state["tile_size"])
            tile_under = tiles.get((tx, ty))

        debug_info = {
            "fps": round(clock.get_fps(), 1),
            "mouse_screen": (mx, my),
            "mouse_world": (wx, wy),
            "tile": (tx, ty),
            "tile_data": tile_under,
            "seed": map_manager.base_seed,
        }

        render_frame(
            screen,
            tiles,
            images,
            state["tile_size"],
            state["offset_x"],
            state["offset_y"],
            debug_info,
            conveyor_system
        )

        dt = clock.tick(USER_OPTIONS["fps"]) / 1000.0

    pygame.quit()
