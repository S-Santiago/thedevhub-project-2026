import os
import sys

import pygame
from pathlib import Path
from typing import Dict, Tuple

from settings import ASSETS_PATH, TERRAINS, MATERIALS, MACHINES

_base_images: Dict[str, pygame.Surface] = {}
_fallbacks: Dict[str, Tuple[int, int, int]] = {}
_scaled_cache: Dict[Tuple[str, int], pygame.Surface] = {}


def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funciona en entorno de desarrollo y en PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def _fallback_color(category_name: str) -> Tuple[int, int, int]:
    return (255, 0, 255) if category_name == "TERRAINS" else (100, 100, 100)


def _load_image(file_path: Path):
    try:
        return pygame.image.load(str(file_path)).convert_alpha()
    except pygame.error as e:
        print(f"[ERROR] Asset '{file_path}': {e}. Using fallback texture.")
        return None


def _register_asset(key: str, surface, fallback_color: Tuple[int, int, int]) -> None:
    _base_images[key] = surface
    _fallbacks[key] = fallback_color


def _load_directory_assets(base_name: str, assets_dir: Path, category_name: str) -> None:
    fallback_color = _fallback_color(category_name)
    for child in sorted(assets_dir.iterdir()):
        if not child.is_file() or child.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        key = f"{base_name}_{child.stem.upper()}"
        _register_asset(key, _load_image(child), fallback_color)

    # Asegurar la clave base aunque el contenido esté en subarchivos.
    _base_images.setdefault(base_name, None)
    _fallbacks.setdefault(base_name, fallback_color)


def _init_base_images():
    if _base_images:
        return

    sources = [
        ("TERRAINS", TERRAINS),
        ("MATERIALS", MATERIALS),
        ("MACHINES", MACHINES),
    ]

    assets_root = Path(resource_path(ASSETS_PATH))

    for category_name, mapping in sources:
        assets_dir = assets_root / category_name
        for name in mapping.keys():
            file_path = assets_dir / f"{name.lower()}.png"
            dir_path = assets_dir / name
            fallback_color = _fallback_color(category_name)

            # Si existe una carpeta para este asset (ej. MACHINES/CONVEYOR/RIGHT.png), cargar sus hijos
            if dir_path.exists() and dir_path.is_dir():
                _load_directory_assets(name, dir_path, category_name)

            # Si existe un fichero único (ej. machines/conveyor.png), cargarlo
            elif file_path.exists():
                _register_asset(name, _load_image(file_path), fallback_color)

            else:
                _register_asset(name, None, fallback_color)


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