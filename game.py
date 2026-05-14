import ctypes
import os
import pygame
import platform
import traceback
from pathlib import Path

from settings import (
    APP_ID,
    APP_NAME,
    MAP_SIZE,
    MIN_TILE_SIZE,
    CAMERA_SPEED,
    USER_OPTIONS,
    BASE_SEED,
)

from build_system import MACHINE_CONVEYOR
from map_manager import MapManager
from asset_manager import default_save_root, load_images, resource_path
from renderer import render_frame
from input_handler import process_event
from logic.conveyor import ConveyorSystem
from logic.drill_system import DrillSystem
from logic.inventory import InventorySystem
from enums import Direction


def _show_save_slot_dialog():
    """Show save slot dialog using pygame. Returns None if user closes the dialog."""
    SAVE_SLOTS = ["partida1", "partida2", "partida3"]
    save_root = default_save_root()
    
    # Initialize pygame for dialog
    pygame.init()
    
    # Create dialog window
    dialog_width = 500
    dialog_height = 400
    dialog_surface = pygame.display.set_mode((dialog_width, dialog_height))
    pygame.display.set_caption("Seleccionar Partida")
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    LIGHT_GRAY = (240, 240, 240)
    GREEN = (76, 175, 80)
    DARK_GREEN = (69, 160, 73)
    BLUE = (33, 150, 243)
    RED = (244, 67, 54)
    ORANGE = (255, 152, 0)
    GRAY = (150, 150, 150)
    
    # Font
    font_title = pygame.font.Font(None, 28)
    font_button = pygame.font.Font(None, 20)
    font_small = pygame.font.Font(None, 14)
    
    selected_slot = [SAVE_SLOTS[0]]
    
    def _slot_has_save(slot_name):
        """Check if a slot has a saved game"""
        meta_path = save_root / slot_name / "meta.json"
        return meta_path.exists()
    
    def _delete_save(slot_name):
        """Delete all content from a save slot"""
        from map_manager import MapManager
        try:
            mm = MapManager(save_root=save_root, save_name=slot_name)
            mm.delete_save()
            return True
        except Exception as e:
            print(f"Error deleting save: {e}")
            return False
    
    class Button:
        def __init__(self, x, y, width, height, text, slot=None, action=None):
            self.rect = pygame.Rect(x, y, width, height)
            self.text = text
            self.slot = slot
            self.action = action
            self.hovered = False
            
        def draw(self, surface):
            color = DARK_GREEN if self.hovered else GREEN
            pygame.draw.rect(surface, color, self.rect)
            pygame.draw.rect(surface, BLACK, self.rect, 2)
            
            text_surface = font_button.render(self.text, True, WHITE)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)
            
        def update(self, mouse_pos):
            self.hovered = self.rect.collidepoint(mouse_pos)
            
        def is_clicked(self, mouse_pos):
            return self.rect.collidepoint(mouse_pos)
    
    class DeleteButton:
        def __init__(self, x, y, width, height, text, slot):
            self.rect = pygame.Rect(x, y, width, height)
            self.text = text
            self.slot = slot
            self.hovered = False
            
        def draw(self, surface):
            color = (200, 50, 50) if self.hovered else RED
            pygame.draw.rect(surface, color, self.rect)
            pygame.draw.rect(surface, BLACK, self.rect, 1)
            
            text_surface = font_small.render(self.text, True, WHITE)
            text_rect = text_surface.get_rect(center=self.rect.center)
            surface.blit(text_surface, text_rect)
            
        def update(self, mouse_pos):
            self.hovered = self.rect.collidepoint(mouse_pos)
            
        def is_clicked(self, mouse_pos):
            return self.rect.collidepoint(mouse_pos)
    
    # Create buttons
    button_width = 100
    button_height = 40
    delete_button_width = 70
    delete_button_height = 25
    
    start_x = (dialog_width - button_width * 3 - 30) // 2
    start_y = 120
    
    buttons = []
    delete_buttons = []
    
    for i, slot in enumerate(SAVE_SLOTS):
        x = start_x + i * (button_width + 15)
        button = Button(x, start_y, button_width, button_height, slot.capitalize(), slot)
        buttons.append(button)
        
        # Delete button below each slot
        has_save = _slot_has_save(slot)
        delete_btn = DeleteButton(
            x + (button_width - delete_button_width) // 2,
            start_y + button_height + 5,
            delete_button_width,
            delete_button_height,
            "Borrar",
            slot
        )
        delete_buttons.append((delete_btn, has_save))
    
    # Continue button
    continue_button = Button(
        (dialog_width - 120) // 2,
        start_y + 110,
        120,
        40,
        "Continuar"
    )
    
    clock = pygame.time.Clock()
    done = False
    result = None
    
    while not done:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                result = None
                done = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check slot buttons
                for button in buttons:
                    if button.is_clicked(mouse_pos):
                        selected_slot[0] = button.slot
                
                # Check delete buttons
                for delete_btn, has_save in delete_buttons:
                    if has_save and delete_btn.is_clicked(mouse_pos):
                        _delete_save(delete_btn.slot)
                
                # Check continue button
                if continue_button.is_clicked(mouse_pos):
                    result = selected_slot[0]
                    done = True
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    result = selected_slot[0]
                    done = True
                elif event.key == pygame.K_ESCAPE:
                    result = None
                    done = True
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    idx = event.key - pygame.K_1
                    if idx < len(SAVE_SLOTS):
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_SHIFT:
                            # Shift+1/2/3 para borrar
                            _delete_save(SAVE_SLOTS[idx])
                        else:
                            selected_slot[0] = SAVE_SLOTS[idx]
        
        # Update button hover states
        for button in buttons:
            button.update(mouse_pos)
        continue_button.update(mouse_pos)
        for delete_btn, _ in delete_buttons:
            delete_btn.update(mouse_pos)
        
        # Draw
        dialog_surface.fill(LIGHT_GRAY)
        
        # Title
        title = font_title.render("Elige un slot de guardado:", True, BLACK)
        title_rect = title.get_rect(center=(dialog_width // 2, 30))
        dialog_surface.blit(title, title_rect)
        
        # Selected slot indicator
        selected_text = font_button.render(f"Seleccionado: {selected_slot[0].capitalize()}", True, BLUE)
        selected_rect = selected_text.get_rect(center=(dialog_width // 2, 70))
        dialog_surface.blit(selected_text, selected_rect)
        
        # Draw slot buttons with save status
        for i, button in enumerate(buttons):
            button.draw(dialog_surface)
            has_save = _slot_has_save(button.slot)
            status_text = "📁" if has_save else "Vacío"
            status_surface = font_small.render(status_text, True, BLUE if has_save else GRAY)
            status_rect = status_surface.get_rect(center=(button.rect.centerx, button.rect.bottom + 30))
            dialog_surface.blit(status_surface, status_rect)
        
        # Draw delete buttons (only if slot has save)
        for delete_btn, has_save in delete_buttons:
            if has_save:
                delete_btn.draw(dialog_surface)
        
        continue_button.draw(dialog_surface)
        
        # Instructions
        instr1 = font_small.render("Presiona 1, 2, 3 para seleccionar | Shift+1/2/3 para borrar", True, (50, 50, 50))
        instr1_rect = instr1.get_rect(center=(dialog_width // 2, dialog_height - 30))
        dialog_surface.blit(instr1, instr1_rect)
        
        instr2 = font_small.render("O haz clic en los botones. ESC para salir", True, (50, 50, 50))
        instr2_rect = instr2.get_rect(center=(dialog_width // 2, dialog_height - 10))
        dialog_surface.blit(instr2, instr2_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    return result


def run():
    if platform.system() == "Windows":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception as e:
            print(f"No se pudo establecer App ID de Windows: {e}")

    # Elegir slot antes de inicializar la ventana principal del juego.
    selected_save_name = _show_save_slot_dialog()
    
    # Si el usuario cierra el diálogo de selección, salir de la aplicación
    if selected_save_name is None:
        pygame.quit()
        return

    pygame.init()
    pygame.display.set_caption(APP_NAME)

    # Intentar cargar el icono si existe (no crítico)
    icon_path = "<no-resuelto>"
    try:
        # Forzamos la normalización de la ruta absoluta para Windows
        icon_path = os.path.abspath(resource_path("assets/icon.png"))
        pygame.display.set_icon(pygame.image.load(icon_path))
    except Exception as e:
        # Si estamos en modo ventana, esto nos salvará la vida para depurar
        error_msg = f"Ruta intentada:\n{icon_path}\n\nError:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        ctypes.windll.user32.MessageBoxW(0, error_msg, "Depuración de Icono", 0)

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
    save_root = default_save_root()
    map_manager = MapManager(save_root=save_root, save_name=selected_save_name)
    map_manager.loadMapFromJSON()
    # Centrar la cámara en la posición guardada (player_position almacena la tile central)
    try:
        px, py = map_manager.player_position
        py = int(py)
        offset_x = - (px * tile_size) + (window_width / 2)
        offset_y = - (py * tile_size) + (window_height / 2)
    except Exception:
        # Fallback a la posición por defecto ya calculada
        pass
        
    images = load_images(tile_size)
    
    # Inicializar el sistema de cintas
    conveyor_system = ConveyorSystem()
    drill_system = DrillSystem()
    inventory_system = InventorySystem()

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
        "debug_mode": False,
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
                inventory_system,
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

        conveyor_system.update(dt, map_manager, inventory_system)
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

        debug_info = {"preview": preview}
        if state.get("debug_mode", False):
            current_seed = map_manager.base_seed if map_manager.base_seed is not None else BASE_SEED
            debug_info.update({
                "fps": round(clock.get_fps(), 1),
                "mouse_screen": (mx, my),
                "mouse_world": (wx, wy),
                "tile": (tx, ty),
                "tile_data": tile_under,
                "seed": current_seed,
                "selected_machine": state.get("selected_machine"),
                "selected_direction": state.get("selected_direction"),
            })

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