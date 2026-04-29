import pygame
from typing import Optional

_debug_font: Optional[pygame.font.Font] = None


def _get_debug_font() -> pygame.font.Font:
    global _debug_font
    if _debug_font is None:
        pygame.font.init()
        _debug_font = pygame.font.SysFont(None, 18)
    return _debug_font


def render_frame(
    screen,
    tiles,
    images,
    tile_size,
    offset_x,
    offset_y,
    debug=None,
    conveyor_system=None,
    drill_system=None,
):
    screen.fill((0, 0, 0))  # Limpiar pantalla cada frame

    for (x, y), data in tiles.items():
        pos_x = offset_x + (x * tile_size)
        pos_y = offset_y + (y * tile_size)

        terrain = data.get("terrain")
        if terrain in images and images[terrain] is not None:
            screen.blit(images[terrain], (pos_x, pos_y))

        mineral = data.get("mineral")
        if mineral and mineral in images and images[mineral] is not None:
            screen.blit(images[mineral], (pos_x, pos_y))
            
    # Dibujar las cintas transportadoras y los materiales en ellas
    if conveyor_system is not None:
        for (cx, cy), belt in conveyor_system._grid.items():
            pos_x = offset_x + (cx * tile_size)
            pos_y = offset_y + (cy * tile_size)
            
            # Dibujar la cinta: preferir asset por dirección (CONVEYOR_UP/RIGHT/...),
            # luego fallback a CONVEYOR genérico, y finalmente dibujar rect si no hay assets.
            dir_key = f"CONVEYOR_{belt.direction.name}"
            if dir_key in images and images[dir_key] is not None:
                screen.blit(images[dir_key], (pos_x, pos_y))
            elif "CONVEYOR" in images and images["CONVEYOR"] is not None:
                screen.blit(images["CONVEYOR"], (pos_x, pos_y))
            else:
                pygame.draw.rect(screen, (100, 100, 100), (pos_x, pos_y, tile_size, tile_size), 2)
            
            # Dibujar el material moviéndose encima de la cinta
            if belt.item is not None:
                pixel_pos = belt.pixel_position(tile_size)
                if pixel_pos:
                    item_x = offset_x + pixel_pos[0]
                    item_y = offset_y + pixel_pos[1]
                    
                    kind = belt.item.kind
                    if kind in images and images[kind] is not None:
                        # Dibujamos el material un poco más pequeño para que quepa en la cinta
                        scaled_item = pygame.transform.scale(images[kind], (int(tile_size * 0.6), int(tile_size * 0.6)))
                        # Centramos el ítem
                        screen.blit(scaled_item, (item_x + tile_size * 0.2, item_y + tile_size * 0.2))

    # Dibujar perforadoras
    if drill_system is not None:
        for (dx, dy), drill in drill_system._grid.items():
            pos_x = offset_x + (dx * tile_size)
            pos_y = offset_y + (dy * tile_size)

            dir_key = f"DRILL_{drill.direction.name}"
            if dir_key in images and images[dir_key] is not None:
                screen.blit(images[dir_key], (pos_x, pos_y))
            elif "DRILL" in images and images["DRILL"] is not None:
                screen.blit(images["DRILL"], (pos_x, pos_y))
            else:
                pygame.draw.rect(screen, (220, 180, 40), (pos_x, pos_y, tile_size, tile_size), 2)

            # Indicador simple de buffer en esquina para debug visual.
            if getattr(drill, "buffer_items", 0) > 0:
                radius = max(3, int(tile_size * 0.08))
                pygame.draw.circle(
                    screen,
                    (255, 240, 120),
                    (int(pos_x + tile_size * 0.85), int(pos_y + tile_size * 0.15)),
                    radius,
                )

    # Overlay de debug
    if debug is not None:
        try:
            font = _get_debug_font()

            lines = []
            lines.append(f"FPS: {debug.get('fps')}")
            mx, my = debug.get('mouse_screen', (None, None))  # Cursor respecto a la ventana
            lines.append(f"Mouse: {mx}, {my}")
            wx, wy = debug.get('mouse_world', (None, None))  # Cursor respecto al mapa
            wx_str = int(wx) if wx is not None else None
            wy_str = int(wy) if wy is not None else None
            lines.append(f"World: {wx_str},{wy_str}")
            tx, ty = debug.get('tile', (None, None))
            tdata = debug.get('tile_data')
            if tdata:
                lines.append(f"Tile: {tx}, {ty} ({tdata.get('terrain')}, {tdata.get('mineral')})")
            else:
                lines.append(f"Tile: {tx}, {ty}")

            lines.append(f"Seed: {debug.get('seed')}")
            belts = debug.get("belts")
            drills = debug.get("drills")
            if belts is not None or drills is not None:
                lines.append(f"Belts: {belts} | Drills: {drills}")

            selected_machine = debug.get("selected_machine")
            selected_direction = debug.get("selected_direction")
            lines.append(f"Build: {selected_machine if selected_machine else 'NONE'}")
            if selected_machine:
                lines.append(f"Dir: {selected_direction}")
            lines.append("1=Conveyor | 2=Drill | 0=None | R=Rotate")
            lines.append("WASD=Move camera | Click izq=Place")

            padding = 6
            line_height = font.get_linesize()
            max_line_width = max(font.size(line)[0] for line in lines) if lines else 200
            box_w = max(220, max_line_width + (padding * 2) + 4)
            box_h = padding * 2 + line_height * len(lines)

            overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (5, 5))

            y = 5 + padding
            for line in lines:
                surf = font.render(line, True, (255, 255, 255))
                screen.blit(surf, (10, y))
                y += line_height
        except Exception as e:
            print("[ERROR] render_frame debug overlay:", e)

    pygame.display.flip()
