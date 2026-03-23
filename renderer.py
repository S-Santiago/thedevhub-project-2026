import pygame


def render_frame(screen, tiles, images, tile_size, offset_x, offset_y, debug=None):
    screen.fill((0, 0, 0))  # Limpiar pantalla cada frame

    for (x, y), data in tiles.items():
        pos_x = offset_x + (x * tile_size)
        pos_y = offset_y + (y * tile_size)

        terrain = data.get("terrain")
        if terrain in images:
            screen.blit(images[terrain], (pos_x, pos_y))

        mineral = data.get("mineral")
        if mineral and mineral in images:
            screen.blit(images[mineral], (pos_x, pos_y))

        # Cuadrícula
        rect = pygame.Rect(pos_x, pos_y, tile_size, tile_size)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1)

    # Overlay de debug
    if debug is not None:
        try:
            font = pygame.font.SysFont(None, 18)

            lines = []
            lines.append(f"FPS: {debug.get('fps')}")
            mx, my = debug.get('mouse_screen', (None, None)) # Coordenadas del cursor respecto a la ventana
            lines.append(f"Mouse: {mx}, {my}")
            wx, wy = debug.get('mouse_world', (None, None)) # Coordenadas del cursor respecto al mapa (tiene en cuenta offset y zoom)
            lines.append(f"World: {int(wx) if wx is not None else None},{int(wy) if wy is not None else None}")
            tx, ty = debug.get('tile', (None, None))
            tdata = debug.get('tile_data')
            if tdata:
                lines.append(f"Tile: {tx}, {ty} ({tdata.get('terrain')}, {tdata.get('mineral')})")
            else:
                lines.append(f"Tile: {tx}, {ty}")
                
            lines.append(f"Seed: {debug.get('seed')}")

            padding = 6
            line_height = font.get_linesize()
            box_w = 200
            box_h = padding * 2 + line_height * len(lines)

            overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (5, 5))

            y = 5 + padding
            for line in lines:
                surf = font.render(line, True, (255, 255, 255))
                screen.blit(surf, (10, y))
                y += line_height
        except Exception:
            pass

    pygame.display.flip()
