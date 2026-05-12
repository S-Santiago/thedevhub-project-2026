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
        # maquinas persistidas por coordenada absoluta: (x,y) -> machine data
        self.machine_overrides = {}

    def _ensure_chunk(self, cx, cy):
        if (cx, cy) in self.chunks:
            return
        tiles, _ = generate_chunk(cx, cy, seed=self.base_seed, chunk_size=self.chunk_size)

        # Reaplicar máquinas construidas previamente al volver a generar un chunk.
        chunk_min_x = cx * self.chunk_size
        chunk_min_y = cy * self.chunk_size
        chunk_max_x = chunk_min_x + self.chunk_size
        chunk_max_y = chunk_min_y + self.chunk_size
        for (tx, ty), machine in self.machine_overrides.items():
            if chunk_min_x <= tx < chunk_max_x and chunk_min_y <= ty < chunk_max_y:
                tile = tiles.get((tx, ty))
                if tile is not None:
                    tile["machine"] = machine

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

    def get_tiles_in_rect(self, tile_x0, tile_y0, tile_x1, tile_y1):
        """Devuelve un diccionario con los tiles cuyas coordenadas absolutas
        estén dentro del rectángulo inclusivo [tile_x0,tile_y0] - [tile_x1,tile_y1].

        Este método asegura los chunks necesarios y limita la iteración sólo a
        las celdas visibles para mejorar el rendimiento del renderizado.
        """
        result = {}
        # Normalizar rangos
        if tile_x1 < tile_x0:
            tile_x0, tile_x1 = tile_x1, tile_x0
        if tile_y1 < tile_y0:
            tile_y0, tile_y1 = tile_y1, tile_y0

        cx0 = tile_x0 // self.chunk_size
        cy0 = tile_y0 // self.chunk_size
        cx1 = tile_x1 // self.chunk_size
        cy1 = tile_y1 // self.chunk_size

        for cx in range(cx0, cx1 + 1):
            for cy in range(cy0, cy1 + 1):
                self._ensure_chunk(cx, cy)
                chunk = self.chunks.get((cx, cy), {})
                for (x, y), tile in chunk.items():
                    if tile_x0 <= x <= tile_x1 and tile_y0 <= y <= tile_y1:
                        result[(x, y)] = tile
        return result

    def get_tile(self, x, y, ensure_chunk=False):
        """Devuelve un tile por coordenada absoluta o None si no existe."""
        chunk_x = x // self.chunk_size
        chunk_y = y // self.chunk_size

        if ensure_chunk:
            self._ensure_chunk(chunk_x, chunk_y)

        chunk = self.chunks.get((chunk_x, chunk_y))
        if chunk is None:
            return None

        return chunk.get((x, y))

    def place_machine(self, x, y, machine_name, machine_data=None):
        """Marca una máquina en el tile si es válido para construir.

        `machine_data` permite guardar metadatos, por ejemplo dirección.
        Si no se proporciona, se guarda solo `machine_name`.
        """
        tile = self.get_tile(x, y, ensure_chunk=True)
        if tile is None:
            return False

        if not tile.get("canPlace"):
            return False

        if tile.get("machine") is not None:
            return False

        final_machine_data = machine_data if machine_data is not None else machine_name
        tile["machine"] = final_machine_data
        self.machine_overrides[(x, y)] = final_machine_data
        return True

    def clear_machine(self, x, y):
        """Elimina la máquina del tile si existe."""
        tile = self.get_tile(x, y, ensure_chunk=False)
        if tile is not None:
            tile["machine"] = None

        if (x, y) in self.machine_overrides:
            del self.machine_overrides[(x, y)]

    def is_machine_occupied(self, x, y):
        tile = self.get_tile(x, y, ensure_chunk=False)
        if tile is not None and tile.get("machine") is not None:
            return True

        return (x, y) in self.machine_overrides

    def get_machine_data(self, x, y):
        tile = self.get_tile(x, y, ensure_chunk=False)
        if tile is not None and tile.get("machine") is not None:
            return tile.get("machine")

        return self.machine_overrides.get((x, y))

    def can_place_machine(self, x, y):
        """Valida reglas base de construcción del mapa (terreno + ocupación)."""
        tile = self.get_tile(x, y, ensure_chunk=True)
        if tile is None:
            return False

        if not tile.get("canPlace"):
            return False

        if tile.get("machine") is not None:
            return False

        return True

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
