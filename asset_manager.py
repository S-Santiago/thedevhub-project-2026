import pygame
import os
from settings import ASSETS_PATH, TERRAINS, MATERIALS, MACHINES

def load_images(tile_size):
    images = {}
    elementos = list(TERRAINS.keys()) + list(MATERIALS.keys()) + list(MACHINES.keys())
    
    for elemento in elementos:
        ruta = os.path.join(ASSETS_PATH, f"{elemento.lower()}.png")
        
        if os.path.exists(ruta):
            try:
                img = pygame.image.load(ruta).convert_alpha() 
                images[elemento] = pygame.transform.scale(img, (tile_size, tile_size))
            except pygame.error as e:
                print(f"[ERROR] Asset '{ruta}': {e}. Usando textura de reemplazo.")
                images[elemento] = _create_fallback_surface(elemento, tile_size)
        else:
            images[elemento] = _create_fallback_surface(elemento, tile_size)
            
    return images

def _create_fallback_surface(elemento, tile_size):
    # Crea una textura por defecto si falta la imagen original
    surf = pygame.Surface((tile_size, tile_size))
    color = (255, 0, 255) if elemento in TERRAINS else (100, 100, 100)
    surf.fill(color)
    
    return surf