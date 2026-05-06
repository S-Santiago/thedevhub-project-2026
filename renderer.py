import pygame
from typing import Optional

_debug_font: Optional[pygame.font.Font] = None
import GUI
from build_system import MACHINE_CONVEYOR, MACHINE_DRILL
from enums import Direction


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
    context_menu=None,
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
            
            # Dibujar la cinta: preferir `variant` persistente (CONVEYOR_FROM-TO),
            # luego intentar detectar FROM-TO en tiempo real, luego por dirección única
            # y finalmente fallback genérico.
            variant_key = getattr(belt, "variant", None)
            if variant_key and variant_key in images and images[variant_key] is not None:
                screen.blit(images[variant_key], (pos_x, pos_y))
            else:
                incoming = None
                try:
                    for d in Direction:
                        nx = cx - d.value[0]
                        ny = cy - d.value[1]
                        nb = conveyor_system.get_belt(nx, ny)
                        if nb is not None and getattr(nb, "direction", None) == d:
                            incoming = d
                            break
                except Exception:
                    incoming = None

                used = False
                if incoming is not None:
                    combo_key = f"CONVEYOR_{incoming.name}-{belt.direction.name}"
                    if combo_key in images and images[combo_key] is not None:
                        screen.blit(images[combo_key], (pos_x, pos_y))
                        used = True

                if not used:
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

    # Dibujar previsualización de colocación (hover) si la hay en debug['preview']
    if debug is not None:
        try:
            preview = debug.get("preview")
            if preview:
                p_tile = preview.get("tile")
                p_machine = preview.get("machine")
                p_dir = preview.get("direction")
                can_place = preview.get("can_place", False)
                if p_tile is not None and p_machine is not None:
                    px = offset_x + (p_tile[0] * tile_size)
                    py = offset_y + (p_tile[1] * tile_size)

                    # Cinta: intentar usar asset específico por dirección
                    # Determinar letra cardinal para la dirección (N,E,S,W)
                    dir_letter = None
                    if p_dir is not None:
                        dir_name = getattr(p_dir, "name", None) if p_dir is not None else None
                        if dir_name is None:
                            dir_name = str(p_dir)
                        letter_map = {"UP": "N", "RIGHT": "E", "DOWN": "S", "LEFT": "W"}
                        dir_letter = letter_map.get(dir_name, None)

                    if p_machine == MACHINE_CONVEYOR or p_machine == "CONVEYOR":
                        # Intentar usar asset FROM-TO para la previsualización si es aplicable
                        incoming = None
                        try:
                            if conveyor_system is not None:
                                for d in Direction:
                                    nx = p_tile[0] - d.value[0]
                                    ny = p_tile[1] - d.value[1]
                                    nb = conveyor_system.get_belt(nx, ny)
                                    if nb is not None and getattr(nb, "direction", None) == d:
                                        incoming = d
                                        break
                        except Exception:
                            incoming = None

                        surf = None
                        if incoming is not None and p_dir is not None:
                            combo_key = f"CONVEYOR_{incoming.name}-{p_dir.name}"
                            if combo_key in images and images[combo_key] is not None:
                                surf = images[combo_key].copy()

                        if surf is None:
                            dir_name = getattr(p_dir, "name", None) if p_dir is not None else None
                            dir_key = f"CONVEYOR_{dir_name}" if dir_name else "CONVEYOR"
                            if dir_key in images and images[dir_key] is not None:
                                surf = images[dir_key].copy()
                            elif "CONVEYOR" in images and images["CONVEYOR"] is not None:
                                surf = images["CONVEYOR"].copy()
                            else:
                                s = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                                color = (0, 200, 0, 90) if can_place else (200, 0, 0, 90)
                                s.fill(color)
                                if dir_letter:
                                    try:
                                        font = pygame.font.SysFont(None, max(12, int(tile_size * 0.5)))
                                        text_s = font.render(dir_letter, True, (255, 255, 255))
                                        tx = (s.get_width() - text_s.get_width()) // 2
                                        ty = (s.get_height() - text_s.get_height()) // 2
                                        s.blit(text_s, (tx, ty))
                                    except Exception:
                                        pass
                                screen.blit(s, (px, py))

                        if surf is not None:
                            surf.set_alpha(160 if can_place else 100)
                            if dir_letter:
                                try:
                                    font = pygame.font.SysFont(None, max(12, int(tile_size * 0.5)))
                                    text_s = font.render(dir_letter, True, (255, 255, 255))
                                    tx = (surf.get_width() - text_s.get_width()) // 2
                                    ty = (surf.get_height() - text_s.get_height()) // 2
                                    surf.blit(text_s, (tx, ty))
                                except Exception:
                                    pass
                            screen.blit(surf, (px, py))

                    # Taladro: asset por dirección o fallback
                    elif p_machine == MACHINE_DRILL or p_machine == "DRILL":
                        dir_name = getattr(p_dir, "name", None) if p_dir is not None else None
                        dir_key = f"DRILL_{dir_name}" if dir_name else "DRILL"
                        if dir_key in images and images[dir_key] is not None:
                            surf = images[dir_key].copy()
                            surf.set_alpha(160 if can_place else 100)
                            if dir_letter:
                                try:
                                    font = pygame.font.SysFont(None, max(12, int(tile_size * 0.5)))
                                    text_s = font.render(dir_letter, True, (255, 255, 255))
                                    tx = (surf.get_width() - text_s.get_width()) // 2
                                    ty = (surf.get_height() - text_s.get_height()) // 2
                                    surf.blit(text_s, (tx, ty))
                                except Exception:
                                    pass
                            screen.blit(surf, (px, py))
                        elif "DRILL" in images and images["DRILL"] is not None:
                            surf = images["DRILL"].copy()
                            surf.set_alpha(160 if can_place else 100)
                            if dir_letter:
                                try:
                                    font = pygame.font.SysFont(None, max(12, int(tile_size * 0.5)))
                                    text_s = font.render(dir_letter, True, (255, 255, 255))
                                    tx = (surf.get_width() - text_s.get_width()) // 2
                                    ty = (surf.get_height() - text_s.get_height()) // 2
                                    surf.blit(text_s, (tx, ty))
                                except Exception:
                                    pass
                            screen.blit(surf, (px, py))
                        else:
                            s = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                            color = (0, 200, 0, 90) if can_place else (200, 0, 0, 90)
                            s.fill(color)
                            if dir_letter:
                                try:
                                    font = pygame.font.SysFont(None, max(12, int(tile_size * 0.5)))
                                    text_s = font.render(dir_letter, True, (255, 255, 255))
                                    tx = (s.get_width() - text_s.get_width()) // 2
                                    ty = (s.get_height() - text_s.get_height()) // 2
                                    s.blit(text_s, (tx, ty))
                                except Exception:
                                    pass
                            screen.blit(s, (px, py))
        except Exception as e:
            print("[ERROR] drawing preview:", e)

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
                dir_str = getattr(selected_direction, "name", selected_direction)
                lines.append(f"Dir: {dir_str}")
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

    # Dibujar menú contextual si existe
    if context_menu is not None:
        try:
            GUI.draw_context_menu(screen, context_menu, tile_size)
        except Exception as e:
            print("[ERROR] drawing context menu:", e)

    pygame.display.flip()
