import pygame
from typing import Optional

_debug_font: Optional[pygame.font.Font] = None
import GUI
from build_system import MACHINE_CONVEYOR, MACHINE_DRILL, MACHINE_INVENTORY
from enums import Direction


def _get_debug_font() -> pygame.font.Font:
    global _debug_font
    if _debug_font is None:
        pygame.font.init()
        _debug_font = pygame.font.SysFont(None, 18)
    return _debug_font


def _direction_letter(direction):
    name = getattr(direction, "name", None) if direction is not None else None
    if name is None:
        return None
    return {"UP": "N", "RIGHT": "E", "DOWN": "S", "LEFT": "W"}.get(name, None)


def _conveyor_asset_candidates(incoming_direction, outgoing_direction):
    out_name = getattr(outgoing_direction, "name", None) if outgoing_direction is not None else None
    candidates = []

    if out_name is None:
        return ["CONVEYOR"]

    if incoming_direction is not None:
        entry_direction = None
        if incoming_direction == Direction.UP:
            entry_direction = Direction.DOWN
        elif incoming_direction == Direction.DOWN:
            entry_direction = Direction.UP
        elif incoming_direction == Direction.LEFT:
            entry_direction = Direction.RIGHT
        elif incoming_direction == Direction.RIGHT:
            entry_direction = Direction.LEFT

        if entry_direction is not None and entry_direction != outgoing_direction:
            candidates.append(f"CONVEYOR_{entry_direction.name}-{out_name}")

    candidates.append(f"CONVEYOR_{out_name}")
    candidates.append("CONVEYOR")
    return candidates


def _select_conveyor_surface(images, incoming_direction, outgoing_direction):
    for key in _conveyor_asset_candidates(incoming_direction, outgoing_direction):
        if key in images and images[key] is not None:
            return images[key].copy()
    return None


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
        for (cx, cy), belt in conveyor_system.iter_belts():
            pos_x = offset_x + (cx * tile_size)
            pos_y = offset_y + (cy * tile_size)
            surf = None
            try:
                incoming_direction = getattr(belt, "incoming_direction", getattr(belt, "in_direction", None))
                outgoing_direction = getattr(belt, "direction", None)
                surf = _select_conveyor_surface(images, incoming_direction, outgoing_direction)
            except Exception:
                surf = None

            if surf is not None:
                screen.blit(surf, (pos_x, pos_y))
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
        for (dx, dy), drill in drill_system.iter_drills():
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

    # Dibujar máquinas genéricas (p.ej. cofres / inventarios) a partir de tile['machine']
    try:
        for (x, y), data in tiles.items():
            machine = data.get("machine")
            if not machine:
                continue

            # Normalizar a nombre y asset_key
            asset_key = None
            machine_name = None
            if isinstance(machine, dict):
                machine_name = machine.get("machine")
                asset_key = machine.get("asset_key")
            else:
                machine_name = machine

            if machine_name == MACHINE_INVENTORY or machine_name == "INVENTORY":
                # Si hay una key explícita, usarla; si no, intentar 'INVENTORY'
                if asset_key is None:
                    asset_key = "INVENTORY"

                if asset_key in images and images[asset_key] is not None:
                    px = offset_x + (x * tile_size)
                    py = offset_y + (y * tile_size)
                    screen.blit(images[asset_key], (px, py))
    except Exception:
        pass

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

                    dir_letter = _direction_letter(p_dir)

                    if p_machine == MACHINE_CONVEYOR or p_machine == "CONVEYOR":
                        surf = None
                        try:
                            surf = _select_conveyor_surface(images, preview.get("in_direction"), p_dir)
                        except Exception:
                            surf = None

                        if surf is not None:
                            surf.set_alpha(160 if can_place else 100)
                            try:
                                font = pygame.font.SysFont(None, max(10, int(tile_size * 0.35)))
                                incoming_letter = _direction_letter(preview.get("in_direction"))
                                outgoing_letter = _direction_letter(p_dir)
                                if incoming_letter is not None and outgoing_letter is not None:
                                    text_s = font.render(f"{incoming_letter}\u2192{outgoing_letter}", True, (255, 255, 255))
                                elif outgoing_letter is not None:
                                    text_s = font.render(outgoing_letter, True, (255, 255, 255))
                                else:
                                    text_s = None

                                if text_s is not None:
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
    if debug is not None and debug.get("fps") is not None:
        try:
            font = _get_debug_font()

            lines = []
            lines.append(f"FPS: {debug.get('fps')}")
            tx, ty = debug.get('tile', (None, None))
            lines.append(f"X: {tx}  Y: {ty}")
            lines.append(f"Seed: {debug.get('seed')}")

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

                    # Determinar letra cardinal para la dirección (N,E,S,W)
                    dir_letter = None
                    if p_dir is not None:
                        dir_name = getattr(p_dir, "name", None) if p_dir is not None else None
                        if dir_name is None:
                            dir_name = str(p_dir)
                        letter_map = {"UP": "N", "RIGHT": "E", "DOWN": "S", "LEFT": "W"}
                        dir_letter = letter_map.get(dir_name, None)

                    # Cinta: usar la misma selección de asset que el render normal
                    if p_machine == MACHINE_CONVEYOR or p_machine == "CONVEYOR":
                        p_in = preview.get("in_direction")
                        chosen = None
                        try:
                            chosen = _select_conveyor_surface(images, p_in, p_dir)
                        except Exception:
                            chosen = None

                        if chosen is not None:
                            surf = chosen
                            surf.set_alpha(160 if can_place else 100)

                            # Dibujar texto encima: si hay in_direction mostrar "N→E",
                            # si no, mostrar la letra de salida.
                            try:
                                font = pygame.font.SysFont(None, max(10, int(tile_size * 0.35)))
                                in_letter = _direction_letter(p_in)
                                out_letter = _direction_letter(p_dir)
                                if in_letter is not None and out_letter is not None:
                                    text_s = font.render(f"{in_letter}\u2192{out_letter}", True, (255, 255, 255))
                                else:
                                    if out_letter:
                                        text_s = font.render(out_letter, True, (255, 255, 255))
                                    else:
                                        text_s = None

                                if text_s is not None:
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
                            screen.blit(s, (px, py))

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

    # Nota: la barra de selección se ha eliminado a petición del usuario.

    # Dibujar menú contextual si existe
    if context_menu is not None:
        try:
            GUI.draw_context_menu(screen, context_menu, tile_size)
        except Exception as e:
            print("[ERROR] drawing context menu:", e)

    pygame.display.flip()
