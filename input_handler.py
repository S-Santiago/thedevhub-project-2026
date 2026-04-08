import pygame


def process_event(event: pygame.event.Event, state: dict, load_images: callable, MIN_TILE_SIZE: int, MAP_SIZE: int, flags, display_idx, screen, map_manager=None):
    # Se asume que `state` es un diccionario y se muta en sitio
    if event.type == pygame.QUIT:
        state["running"] = False
        return screen, None

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        state["running"] = False
        return screen, None

    if event.type == pygame.MOUSEBUTTONDOWN:
        if event.button == 1:
            state["is_dragging"] = True
            state["last_mouse_pos"] = event.pos
        return screen, None

    if event.type == pygame.MOUSEBUTTONUP:
        if event.button == 1:
            state["is_dragging"] = False
        return screen, None

    if event.type == pygame.MOUSEMOTION:
        if state.get("is_dragging"):
            dx = event.pos[0] - state.get("last_mouse_pos", (0, 0))[0]
            dy = event.pos[1] - state.get("last_mouse_pos", (0, 0))[1]
            state["offset_x"] += dx
            state["offset_y"] += dy
            state["last_mouse_pos"] = event.pos
        # En cada movimiento del ratón, garantizar y podar chunks según la nueva vista (si se proporcionó map_manager)
        if map_manager is not None:
            map_manager.ensure_and_prune_for_view(state["offset_x"], state["offset_y"], state["tile_size"], state["window_width"], state["window_height"])
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

            state["tile_size"] = new_tile_size
            imagenes = load_images(new_tile_size)
            state["map_pixel_size"] = new_tile_size * MAP_SIZE

            if state["window_width"] < state["min_window_width"] or state["window_height"] < state["min_window_height"]:
                state["window_width"] = max(state["window_width"], state["min_window_width"])
                state["window_height"] = max(state["window_height"], state["min_window_height"])
                state["offset_x"] = (state["window_width"] - state["map_pixel_size"]) // 2
                state["offset_y"] = (state["window_height"] - state["map_pixel_size"]) // 2
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
        screen = pygame.display.set_mode((state["window_width"], state["window_height"]), flags, display=display_idx)

        return screen, None

    return screen, None
