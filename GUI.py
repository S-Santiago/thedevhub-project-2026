import pygame
from typing import Optional
from enums import Direction


# Simple context-menu helpers used by input handling and rendering.
# The helpers keep layout logic consistent between hit-testing and drawing.

MENU_BG_COLOR = (30, 30, 30, 255)
MENU_BORDER_COLOR = (200, 200, 200)
MENU_TEXT_COLOR = (255, 255, 255)
MENU_MIN_WIDTH = 140
TOOLBAR_PADDING = 6
TOOLBAR_SPACING = 6
TOOLBAR_BG = (20, 20, 20, 220)

# Última geometría renderizada de la toolbar (lista de {name, rect})
_toolbar_rects = []


def _get_font(size: int = 18) -> pygame.font.Font:
	pygame.font.init()
	return pygame.font.SysFont(None, size)


def draw_context_menu(screen, menu: dict, tile_size: int) -> None:
	"""Dibuja un menú contextual simple en la pantalla.

	menu: { 'pos': (x,y), 'options': [ {'label': str, ...}, ... ] }
	Esta función también guarda en el dict campos auxiliares `_rect` y
	`_item_height` para que la prueba de clics pueda reutilizar la misma
	geometría.
	"""
	if not menu:
		return

	items = menu.get("options", [])
	if not items:
		return

	mx, my = menu.get("pos", (0, 0))
	font = _get_font(max(14, int(tile_size * 0.35)))
	item_height = max(20, int(tile_size * 0.6))
	padding = 8

	# Icono pequeño para mostrar la dirección cuando una opción tiene 'direction'

	# Calcular ancho máximo
	max_w = MENU_MIN_WIDTH
	for opt in items:
		label = opt.get("label", "")
		label_w = font.size(label)[0]
		w = label_w + padding * 2
		if w > max_w:
			max_w = w

	box_w = max_w
	box_h = item_height * len(items)

	screen_w, screen_h = screen.get_size()
	x = mx
	y = my
	if x + box_w > screen_w:
		x = max(4, screen_w - box_w - 4)
	if y + box_h > screen_h:
		y = max(4, screen_h - box_h - 4)

	surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
	surf.fill(MENU_BG_COLOR)
	pygame.draw.rect(surf, MENU_BORDER_COLOR, surf.get_rect(), 1)

	for idx, opt in enumerate(items):
		label = opt.get("label", "")
		text_x = padding

		# Texto de la opción (sin icono)
		text_surf = font.render(label, True, MENU_TEXT_COLOR)
		text_y = idx * item_height + (item_height - text_surf.get_height()) // 2
		surf.blit(text_surf, (text_x, text_y))

	screen.blit(surf, (x, y))

	# Guardar geometría para hit-testing
	menu["_rect"] = (x, y, box_w, box_h)
	menu["_item_height"] = item_height


def menu_hit_test(menu: dict, mouse_pos) -> Optional[int]:
	"""Devuelve el índice del item del menú bajo `mouse_pos`, o None."""
	if not menu or "_rect" not in menu:
		return None

	x, y, w, h = menu["_rect"]
	mx, my = mouse_pos
	if not (x <= mx <= x + w and y <= my <= y + h):
		return None

	item_h = menu.get("_item_height", 24)
	idx = (my - y) // item_h
	if idx < 0 or idx >= len(menu.get("options", [])):
		return None

	return int(idx)


def compute_menu_geometry(menu: dict, tile_size: int, screen_size: tuple) -> None:
	"""Calcula y guarda en `menu` la geometría (_rect, _item_height) usada por el menú.

	Esto permite que el hit-test funcione inmediatamente después de crear
	el dict de menú, sin esperar a que se renderice en el siguiente frame.
	"""
	if not menu:
		return

	items = menu.get("options", [])
	if not items:
		return

	mx, my = menu.get("pos", (0, 0))
	font = _get_font(max(14, int(tile_size * 0.35)))
	item_height = max(20, int(tile_size * 0.6))
	padding = 8

	max_w = MENU_MIN_WIDTH
	for opt in items:
		label = opt.get("label", "")
		label_w = font.size(label)[0]
		w = label_w + padding * 2
		if w > max_w:
			max_w = w

	box_w = max_w
	box_h = item_height * len(items)

	screen_w, screen_h = screen_size
	x = mx
	y = my
	if x + box_w > screen_w:
		x = max(4, screen_w - box_w - 4)
	if y + box_h > screen_h:
		y = max(4, screen_h - box_h - 4)

	menu["_rect"] = (x, y, box_w, box_h)
	menu["_item_height"] = item_height


def draw_toolbar(screen, images: dict, tile_size: int, machines: list, selected_machine: str) -> None:
	"""Dibuja una barra horizontal simple con iconos de `machines` en la esquina superior izquierda.

	Guarda la geometría en `_toolbar_rects` para hit-testing.
	"""
	global _toolbar_rects
	_toolbar_rects = []

	if not machines:
		return

	icon_size = max(16, int(tile_size * 0.75))
	padding = TOOLBAR_PADDING
	spacing = TOOLBAR_SPACING

	x0 = 8
	y0 = 8

	for i, name in enumerate(machines):
		x = x0 + padding + i * (icon_size + spacing)
		y = y0 + padding

		surf = images.get(name)
		if surf is None:
			s = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
			s.fill((100, 100, 100))
			surf_to_blit = s
		else:
			try:
				surf_to_blit = pygame.transform.scale(surf, (icon_size, icon_size))
			except Exception:
				surf_to_blit = surf

		screen.blit(surf_to_blit, (x, y))

		# Resaltar seleccionado
		if name == selected_machine:
			pygame.draw.rect(screen, (255, 240, 120), (x - 2, y - 2, icon_size + 4, icon_size + 4), 2)

		_toolbar_rects.append({"name": name, "rect": (x, y, icon_size, icon_size)})


def toolbar_hit_test(mouse_pos):
	"""Devuelve el nombre de la máquina clicada en la toolbar o None."""
	global _toolbar_rects
	if not _toolbar_rects:
		return None
	mx, my = mouse_pos
	for item in _toolbar_rects:
		x, y, w, h = item["rect"]
		if x <= mx <= x + w and y <= my <= y + h:
			return item["name"]
	return None


def draw_bottom_toolbar(screen, images: dict, tile_size: int, machines: list, selected_machine: str = None):
	"""Dibuja una barra de selección en la parte inferior de la pantalla.

	- Muestra la imagen de cada máquina (si existe) y un número índice (1,2,3...).
	- Resalta la opción seleccionada con un borde.
	- Actualiza `_toolbar_rects` para que `toolbar_hit_test` funcione.
	"""
	global _toolbar_rects
	_toolbar_rects = []

	if not machines:
		return

	screen_w, screen_h = screen.get_size()
	padding = 8
	spacing = 10

	# Tamaño del icono: intentar usar tile_size, con límites razonables
	icon_size = max(16, min(64, int(tile_size * 1)))
	bar_height = icon_size + padding * 2

	# Centrar la barra horizontalmente
	total_width = len(machines) * icon_size + (len(machines) - 1) * spacing
	start_x = max(8, (screen_w - total_width) // 2)
	y = screen_h - bar_height - 8

	font = None
	try:
		pygame.font.init()
		font = pygame.font.SysFont(None, max(12, int(icon_size * 0.28)))
	except Exception:
		font = None

	for idx, name in enumerate(machines):
		x = start_x + idx * (icon_size + spacing)
		rect = (x, y + padding, icon_size, icon_size)

		# Seleccionar asset preferido:
		# Preferir variante direccional (RIGHT / EAST) si existe, luego cualquier
		# child del asset (p. ej. CONVEYOR_RIGHT), y por último el asset base.
		surf = None
		candidates = []
		# Preferir RIGHT/EAST para máquinas orientables
		candidates.append(f"{name}_RIGHT")
		candidates.append(f"{name}_EAST")
		# Añadir cualquier variante disponible en images que empiece por NAME_
		for key in images.keys():
			if key.startswith(f"{name}_"):
				candidates.append(key)
		# Finalmente, el asset base
		candidates.append(name)

		for key in candidates:
			try:
				img = images.get(key)
				if img is not None:
					try:
						surf = pygame.transform.scale(img, (icon_size, icon_size))
					except Exception:
						try:
							surf = img.copy()
						except Exception:
							surf = img
					break
			except Exception:
				continue

		if surf is None:
			s = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
			s.fill((80, 80, 80))
			surf = s

		# Dibujar fondo del icono
		bg = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
		bg.fill((20, 20, 20, 200))
		screen.blit(bg, (rect[0], rect[1]))

		# Blit del icono centrado
		try:
			screen.blit(surf, (rect[0], rect[1]))
		except Exception:
			pass

		# Dibujar número índice en esquina superior izquierda del icono
		try:
			num_s = font.render(str(idx + 1), True, (255, 255, 255)) if font else None
			if num_s is not None:
				screen.blit(num_s, (rect[0] + 4, rect[1] + 2))
		except Exception:
			pass

		# Resaltar seleccionado
		try:
			if selected_machine is not None and selected_machine == name:
				pygame.draw.rect(screen, (255, 240, 120), (rect[0] - 2, rect[1] - 2, rect[2] + 4, rect[3] + 4), 2)
			else:
				pygame.draw.rect(screen, (60, 60, 60), (rect[0] - 1, rect[1] - 1, rect[2] + 2, rect[3] + 2), 1)
		except Exception:
			pass

		_toolbar_rects.append({"name": name, "rect": (rect[0], rect[1], rect[2], rect[3])})

	# Small label left of bar: hint for keys
	try:
		hint_font = pygame.font.SysFont(None, 16)
		hint_s = hint_font.render("1-3: Selección rápida", True, (200, 200, 200))
		screen.blit(hint_s, (max(8, start_x - 140), y + icon_size // 2 - hint_s.get_height() // 2))
	except Exception:
		pass



  