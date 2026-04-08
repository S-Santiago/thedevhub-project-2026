from map_generator import generate_chunk
from settings import CHUNK_SIZE, VIEW_CHUNK_MARGIN, BASE_SEED, CHUNK_CACHE_RADIUS

class MapManager:
    def __init__(self, base_seed=None, chunk_size=CHUNK_SIZE, margin=VIEW_CHUNK_MARGIN):
        self.base_seed = base_seed if base_seed is not None else BASE_SEED
        self.chunk_size = chunk_size
        self.margin = margin
        self.cache_radius = CHUNK_CACHE_RADIUS
        # cache de chunks: (cx,cy) -> dict de tiles
        self.chunks = {}

    def _ensure_chunk(self, cx, cy):
        if (cx, cy) in self.chunks:
            return
        tiles, seed = generate_chunk(cx, cy, seed=self.base_seed, chunk_size=self.chunk_size)
        self.chunks[(cx, cy)] = tiles

    def ensure_chunks_for_view(self, offset_x, offset_y, tile_size, window_width, window_height):
        """Asegura que están generados los chunks que cubren la vista actual.

        offset_x/offset_y: desplazamiento en píxeles aplicados al mapa (pantalla = offset + world)
        tile_size: tamaño de cada tile en píxeles
        """
        # coordenadas del área visible en coordenadas mundo (píxeles)
        left = -offset_x
        top = -offset_y
        right = left + window_width
        bottom = top + window_height

        # convertir a coordenadas de tile
        tile_left = int(left // tile_size)
        tile_top = int(top // tile_size)
        tile_right = int(right // tile_size)
        tile_bottom = int(bottom // tile_size)

        # convertir a coordenadas de chunk
        cx_min = (tile_left) // self.chunk_size
        cy_min = (tile_top) // self.chunk_size
        cx_max = (tile_right) // self.chunk_size
        cy_max = (tile_bottom) // self.chunk_size

        # incluir margen
        cx_min -= self.margin
        cy_min -= self.margin
        cx_max += self.margin
        cy_max += self.margin

        for cx in range(cx_min, cx_max + 1):
            for cy in range(cy_min, cy_max + 1):
                self._ensure_chunk(cx, cy)

    def get_merged_tiles(self):
        """Devuelve un diccionario plano con todos los tiles generados (merge de los chunks)."""
        merged = {}
        for tiles in self.chunks.values():
            merged.update(tiles)
        return merged

    def prune_chunks_around(self, center_cx, center_cy, radius=None):
        """Eliminar de la caché los chunks que queden fuera del radio especificado."""
        if radius is None:
            radius = self.cache_radius

        to_remove = []
        for (cx, cy) in self.chunks.keys():
            if abs(cx - center_cx) > radius or abs(cy - center_cy) > radius:
                to_remove.append((cx, cy))

        for key in to_remove:
            del self.chunks[key]

    def ensure_and_prune_for_view(self, offset_x, offset_y, tile_size, window_width, window_height):
        """Combinación: asegura chunks visibles y poda según el centro de la vista."""
        # Asegurar visibles
        self.ensure_chunks_for_view(offset_x, offset_y, tile_size, window_width, window_height)

        # Calcular chunk central basado en el centro de la ventana
        left = -offset_x
        top = -offset_y
        center_x = left + (window_width / 2)
        center_y = top + (window_height / 2)

        tile_cx = int(center_x // tile_size)
        tile_cy = int(center_y // tile_size)

        center_chunk_x = tile_cx // self.chunk_size
        center_chunk_y = tile_cy // self.chunk_size

        self.prune_chunks_around(center_chunk_x, center_chunk_y)
