import pygame
import os
from settings import ASSETS_PATH, TERRAINS, MATERIALS, MACHINES

_base_images = {}
_fallbacks = {}

def _init_base_images():
    if _base_images: return
    sources = [
        ("TERRAINS", TERRAINS),
        ("MATERIALS", MATERIALS),
        ("MACHINES", MACHINES),
    ]

    for category_name, mapping in sources:
        for elemento in mapping.keys():
            ruta = os.path.join(ASSETS_PATH, category_name, f"{elemento.lower()}.png")
            if os.path.exists(ruta):
                try:
                    _base_images[elemento] = pygame.image.load(ruta).convert_alpha()
                except pygame.error as e:
                    print(f"[ERROR] Asset '{ruta}': {e}. Usando textura de reemplazo.")
                    _base_images[elemento] = None
            else:
                _base_images[elemento] = None

            _fallbacks[elemento] = (255, 0, 255) if category_name == "TERRAINS" else (100, 100, 100)

def load_images(tile_size):
    _init_base_images()
    images = {}
    
    for elemento, img in _base_images.items():
        if img is not None:
            images[elemento] = pygame.transform.scale(img, (tile_size, tile_size))
        else:
            images[elemento] = _create_fallback_surface(_fallbacks[elemento], tile_size)
            
    return images

def _create_fallback_surface(color, tile_size):
    surf = pygame.Surface((tile_size, tile_size))
    surf.fill(color)
    return surf