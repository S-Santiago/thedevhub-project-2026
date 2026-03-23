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
from asset_manager import load_images
from renderer import render_frame
from input_handler import process_event


def run():
    if platform.system() == "Windows":
        import ctypes
        
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID) # ID de la app. para que el sistema operativo la reconozca correctamente

    pygame.init()
    pygame.display.set_caption(APP_NAME) # Nombre de la ventana

    gameIcon = pygame.image.load(f"{ASSETS_PATH}/icon.png") # Icono de la ventana
    pygame.display.set_icon(gameIcon)

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

    # Carga de datos
    tiles, seed = generate_map()
    imagenes = load_images(tile_size)

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
            )

            if new_images is not None:
                imagenes = new_images

        # Preparar información de debug
        mx, my = pygame.mouse.get_pos()
        wx = mx - state["offset_x"]
        wy = my - state["offset_y"]
        tx = None
        ty = None
        tile_under = None

        if 0 <= wx < state["map_pixel_size"] and 0 <= wy < state["map_pixel_size"]:
            tx = int(wx // state["tile_size"])
            ty = int(wy // state["tile_size"])
            tile_under = tiles.get((tx, ty))

        debug_info = {
            "fps": round(clock.get_fps(), 1),
            "mouse_screen": (mx, my),
            "mouse_world": (wx, wy),
            "tile": (tx, ty),
            "tile_data": tile_under,
            "seed": seed,
        }

        render_frame(
            screen,
            tiles,
            imagenes,
            state["tile_size"],
            state["offset_x"],
            state["offset_y"],
            debug_info,
        )

        clock.tick(USER_OPTIONS["fps"])

    pygame.quit()
