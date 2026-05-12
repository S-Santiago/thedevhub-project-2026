import pygame
from pathlib import Path
from typing import Dict, Tuple

from settings import ASSETS_PATH, TERRAINS, MATERIALS, MACHINES

_base_images: Dict[str, pygame.Surface] = {}
_fallbacks: Dict[str, Tuple[int, int, int]] = {}
_scaled_cache: Dict[Tuple[str, int], pygame.Surface] = {}


def _init_base_images():
    if _base_images:
        return

    sources = [
        ("TERRAINS", TERRAINS),
        ("MATERIALS", MATERIALS),
        ("MACHINES", MACHINES),
    ]

    assets_root = Path(ASSETS_PATH)

    for category_name, mapping in sources:
        assets_dir = assets_root / category_name
        for name in mapping.keys():
            file_path = assets_dir / f"{name.lower()}.png"
            dir_path = assets_dir / name

            # Si existe una carpeta para este asset (ej. MACHINES/CONVEYOR/RIGHT.png), cargar sus hijos
            if dir_path.exists() and dir_path.is_dir():
                for child in sorted(dir_path.iterdir()):
                    if child.is_file() and child.suffix.lower() in ('.png', '.jpg', '.jpeg'):
                        key = f"{name}_{child.stem.upper()}"
                        try:
                            _base_images[key] = pygame.image.load(str(child)).convert_alpha()
                        except pygame.error as e:
                            print(f"[ERROR] Asset '{child}': {e}. Using fallback texture.")
                            _base_images[key] = None
                        _fallbacks[key] = (255, 0, 255) if category_name == "TERRAINS" else (100, 100, 100)

                # Asegurar que la clave base existe (puede usarse como fallback genérico)
                _base_images.setdefault(name, None)
                _fallbacks.setdefault(name, (255, 0, 255) if category_name == "TERRAINS" else (100, 100, 100))

            # Si existe un fichero único (ej. machines/conveyor.png), cargarlo
            elif file_path.exists():
                try:
                    _base_images[name] = pygame.image.load(str(file_path)).convert_alpha()
                except pygame.error as e:
                    print(f"[ERROR] Asset '{file_path}': {e}. Using fallback texture.")
                    _base_images[name] = None
                _fallbacks[name] = (255, 0, 255) if category_name == "TERRAINS" else (100, 100, 100)

            else:
                _base_images[name] = None
                _fallbacks[name] = (255, 0, 255) if category_name == "TERRAINS" else (100, 100, 100)


def load_images(tile_size: int) -> Dict[str, pygame.Surface]:
    """Load and scale all base images (with fallbacks).

    Returns a mapping name -> pygame.Surface sized to `tile_size`.
    """
    _init_base_images()
    images: Dict[str, pygame.Surface] = {}

    for name, img in _base_images.items():
        cache_key = (name, tile_size)
        # Reusar superficie escalada si ya existe
        if cache_key in _scaled_cache:
            images[name] = _scaled_cache[cache_key]
            continue

        if img is not None:
            try:
                surf = pygame.transform.scale(img, (tile_size, tile_size))
            except Exception as e:
                print(f"[ERROR] Scaling image for {name}: {e}. Using fallback.")
                surf = _create_fallback_surface(_fallbacks.get(name, (255, 0, 255)), tile_size)
        else:
            surf = _create_fallback_surface(_fallbacks.get(name, (255, 0, 255)), tile_size)

        _scaled_cache[cache_key] = surf
        images[name] = surf

    return images


def _create_fallback_surface(color: Tuple[int, int, int], tile_size: int) -> pygame.Surface:
    surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
    surf.fill(color)
    return surf