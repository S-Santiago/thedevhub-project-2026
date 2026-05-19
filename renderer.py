import pygame
from typing import Optional

_debug_font: Optional[pygame.font.Font] = None
import GUI
from build_system import MACHINE_CONVEYOR, MACHINE_DRILL, MACHINE_INVENTORY, AVAILABLE_MACHINES
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


def _select_machine_surface(images, base_name: str, direction_name: str = None):
    """Selecciona la mejor superficie para una máquina genérica.

    Intentos: base_name_DIRECTION -> base_name_RIGHT -> base_name_EAST -> cualquier
    variante base_name_* -> base_name
    """
    candidates = []
    if direction_name:
        candidates.append(f"{base_name}_{direction_name}")
    candidates.extend([f"{base_name}_RIGHT", f"{base_name}_EAST"])  # preferir East/Right

    for key in images.keys():
        if key.startswith(f"{base_name}_"):
            candidates.append(key)

    candidates.append(base_name)

    for key in candidates:
        try:
            img = images.get(key)
            if img is not None:
                try:
                    return img.copy()
                except Exception:
                    return img
        except Exception:
            continue

    return None


def _is_chest_like_machine(machine_data) -> bool:
    if not machine_data:
        return False

    machine_name = None
    asset_key = None
    if isinstance(machine_data, dict):
        machine_name = machine_data.get("machine")
        asset_key = machine_data.get("asset_key")
    else:
        machine_name = machine_data

    machine_name_s = str(machine_name).upper() if machine_name is not None else ""
    asset_key_s = str(asset_key).upper() if asset_key is not None else ""

    if machine_name_s in ("INVENTORY", "CHEST"):
        return True
    if "CHEST" in asset_key_s or "COFRE" in asset_key_s:
        return True
    return False


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
    selected_machine=None,
):
    screen.fill((0, 0, 0))  # Limpiar pantalla cada frame
    conveyor_item_draw_calls = []
    conveyor_item_under_chest_draw_calls = []

    for (x, y), data in tiles.items():
        pos_x = offset_x + (x * tile_size)
        pos_y = offset_y + (y * tile_size)

        terrain = data.get("terrain")
        if terrain in images and images[terrain] is not None:
            screen.blit(images[terrain], (pos_x, pos_y))

        mineral = data.get("mineral")
        if mineral and mineral in images and images[mineral] is not None:
            screen.blit(images[mineral], (pos_x, pos_y))

    # Mostrar overlay de lugares construibles si se solicitó en debug
    try:
        if debug is not None and debug.get("show_placeable"):
            for (x, y), data in tiles.items():
                px = offset_x + (x * tile_size)
                py = offset_y + (y * tile_size)
                can_place = data.get("canPlace")
                machine = data.get("machine")
                if machine is not None:
                    # ocupada -> semitransparente roja
                    s = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                    s.fill((200, 0, 0, 120))
                    screen.blit(s, (px, py))
                else:
                    if can_place is True:
                        s = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                        s.fill((0, 200, 0, 70))
                        screen.blit(s, (px, py))
                    else:
                        s = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                        s.fill((0, 0, 200, 70))
                        screen.blit(s, (px, py))
    except Exception:
        pass
            
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
            
            # Encolamos los minerales para dibujarlos al final del mundo y evitar que otras capas los tapen.
            if belt.item is not None:
                pixel_pos = belt.pixel_position(tile_size)
                if pixel_pos:
                    item_x = offset_x + pixel_pos[0]
                    item_y = offset_y + pixel_pos[1]
                    
                    kind = belt.item.kind
                    item_surface = None
                    for asset_key in (f"MINERAL_{kind}", kind):
                        if asset_key in images and images[asset_key] is not None:
                            item_surface = images[asset_key]
                            break

                    if item_surface is not None:
                        # Dibujamos el material un poco más pequeño para que quepa en la cinta
                        scaled_item = pygame.transform.scale(item_surface, (int(tile_size * 0.6), int(tile_size * 0.6)))
                        # Centramos el ítem
                        item_draw_call = (scaled_item, (item_x + tile_size * 0.2, item_y + tile_size * 0.2))

                        # Si el próximo tile es un cofre/inventario, el mineral se dibuja antes
                        # para que el cofre quede visualmente por encima (efecto "guardado").
                        direction = getattr(belt, "direction", None)
                        if direction is not None:
                            dx, dy = direction.value
                            next_tile_data = tiles.get((cx + dx, cy + dy))
                            if _is_chest_like_machine(next_tile_data.get("machine") if next_tile_data else None):
                                conveyor_item_under_chest_draw_calls.append(item_draw_call)
                            else:
                                conveyor_item_draw_calls.append(item_draw_call)
                        else:
                            conveyor_item_draw_calls.append(item_draw_call)

    # Dibujar perforadoras
    if drill_system is not None:
        for (dx, dy), drill in drill_system.iter_drills():
            pos_x = offset_x + (dx * tile_size)
            pos_y = offset_y + (dy * tile_size)

            dir_name = getattr(drill.direction, "name", None) if drill.direction is not None else None
            surf = _select_machine_surface(images, "DRILL", dir_name)
            if surf is not None:
                screen.blit(surf, (pos_x, pos_y))
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

    # Ítems que van hacia cofre: se pintan antes de la capa de cofres para que estos queden encima.
    for item_surface, item_pos in conveyor_item_under_chest_draw_calls:
        screen.blit(item_surface, item_pos)

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
                        surf = _select_machine_surface(images, "DRILL", dir_name)
                        if surf is not None:
                            try:
                                surf.set_alpha(160 if can_place else 100)
                            except Exception:
                                pass
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
                    
                    # Cofre / Inventario: intentar varias claves comunes
                    elif p_machine == MACHINE_INVENTORY or p_machine == "INVENTORY":
                        asset_key = preview.get("asset_key")
                        surf = None
                        candidates = []
                        if asset_key:
                            candidates.append(asset_key)
                        candidates.extend(["INVENTORY", "CHEST_CHEST", "CHEST", "COFRE", "CONVEYOR_COFRE"])
                        for key in candidates:
                            try:
                                img = images.get(key)
                                if img is not None:
                                    try:
                                        surf = img.copy()
                                    except Exception:
                                        surf = img
                                    break
                            except Exception:
                                continue

                        if surf is not None:
                            try:
                                surf.set_alpha(160 if can_place else 100)
                            except Exception:
                                pass
                            screen.blit(surf, (px, py))
                        else:
                            s = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                            color = (0, 200, 0, 90) if can_place else (200, 0, 0, 90)
                            s.fill(color)
                            screen.blit(s, (px, py))
                    
                    # Cofre / Inventario: usar asset explícito si existe o intentar claves comunes
                    elif p_machine == MACHINE_INVENTORY or p_machine == "INVENTORY":
                        asset_key = preview.get("asset_key")
                        surf = None
                        candidates = []
                        if asset_key:
                            candidates.append(asset_key)
                        # Intentar claves comunes donde puede estar el asset del cofre
                        candidates.extend(["INVENTORY", "CHEST_CHEST", "CHEST", "COFRE", "CONVEYOR_COFRE"])
                        for key in candidates:
                            try:
                                img = images.get(key)
                                if img is not None:
                                    try:
                                        surf = img.copy()
                                    except Exception:
                                        surf = img
                                    break
                            except Exception:
                                continue

                        if surf is not None:
                            try:
                                surf.set_alpha(160 if can_place else 100)
                            except Exception:
                                pass
                            screen.blit(surf, (px, py))
                        else:
                            s = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                            color = (0, 200, 0, 90) if can_place else (200, 0, 0, 90)
                            s.fill(color)
                            screen.blit(s, (px, py))
        except Exception as e:
            print("[ERROR] drawing preview:", e)

    # Dibujar minerales de cinta al final para mantenerlos siempre en la capa superior del mundo.
    for item_surface, item_pos in conveyor_item_draw_calls:
        screen.blit(item_surface, item_pos)

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

    # Alerta de construcción / guardado
    if debug is not None and debug.get("alert"):
        try:
            font = pygame.font.SysFont(None, 20)
            text = str(debug.get("alert"))
            text_surf = font.render(text, True, (255, 255, 255))
            pad_x, pad_y = 10, 8
            box_w = text_surf.get_width() + pad_x * 2
            box_h = text_surf.get_height() + pad_y * 2
            box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            box.fill((160, 30, 30, 220))
            box.blit(text_surf, (pad_x, pad_y))
            screen.blit(box, (10, 40))
        except Exception:
            pass

    # Dibujar barra inferior de selección con imágenes (1,2,3)
    try:
        GUI.draw_bottom_toolbar(screen, images, tile_size, list(AVAILABLE_MACHINES), selected_machine)
    except Exception as e:
        print("[ERROR] drawing bottom toolbar:", e)

    # Dibujar menú contextual si existe
    if context_menu is not None:
        try:
            GUI.draw_context_menu(screen, context_menu, tile_size)
        except Exception as e:
            print("[ERROR] drawing context menu:", e)

    pygame.display.flip()
