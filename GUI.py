import pygame
from typing import Optional
from enums import Direction


# Simple context-menu helpers used by input handling and rendering.
# The helpers keep layout logic consistent between hit-testing and drawing.

MENU_BG_COLOR = (30, 30, 30, 220)
MENU_BORDER_COLOR = (200, 200, 200)
MENU_TEXT_COLOR = (255, 255, 255)
MENU_MIN_WIDTH = 140


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

	max_w = MENU_MIN_WIDTH
	for opt in items:
		label = opt.get("label", "")
		w = font.size(label)[0] + padding * 2
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
		text_surf = font.render(label, True, MENU_TEXT_COLOR)
		text_y = idx * item_height + (item_height - text_surf.get_height()) // 2
		surf.blit(text_surf, (padding, text_y))

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



  