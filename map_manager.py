import json
import random
from datetime import datetime
from pathlib import Path
import os
import tempfile

from enums import Direction
from asset_manager import default_save_root
from logic.conveyor import ConveyorBelt, ConveyorCurve
from logic.drill_system import DrillMachine
from map_generator import generate_chunk
from settings import CHUNK_SIZE, VIEW_CHUNK_MARGIN, BASE_SEED, CHUNK_CACHE_RADIUS


class MapManager:
    def __init__(self, base_seed=None, chunk_size=CHUNK_SIZE, margin=VIEW_CHUNK_MARGIN, save_root=None, save_name="partida1"):
        if base_seed is not None:
            self.base_seed = base_seed
        elif BASE_SEED is not None:
            self.base_seed = BASE_SEED
        else:
            self.base_seed = self._generate_world_seed()
        self.chunk_size = chunk_size
        self.margin = margin
        self.cache_radius = CHUNK_CACHE_RADIUS
        self.save_root = Path(save_root) if save_root is not None else default_save_root()
        self.save_name = save_name if save_name is not None else "default"
        self.save_path = self.save_root / self.save_name
        self.chunks_path = self.save_path / "chunks"
        self.meta_path = self.save_path / "meta.json"
        
        # cache de chunks: (cx,cy) -> dict de tiles
        self.chunks = {}
        # maquinas persistidas por coordenada absoluta: (x,y) -> machine data
        self.machine_overrides = {}
        
        self.save_meta = {}
        self.player_position = [0, 0]
        self.persistence_enabled = False

    def _generate_world_seed(self):
        return int(random.randint(0, 2**31 - 1))

    def _ensure_save_dirs(self):
        self.chunks_path.mkdir(parents=True, exist_ok=True)

    def _chunk_key(self, cx, cy):
        return f"{cx}_{cy}"

    def _chunk_dir(self, cx, cy):
        return self.chunks_path / self._chunk_key(cx, cy)

    def _chunk_file(self, cx, cy):
        return self._chunk_dir(cx, cy) / "data.json"

    def _tile_key(self, x, y):
        return f"{x}_{y}"

    def _parse_tile_key(self, tile_key):
        parts = str(tile_key).split("_", 1)
        if len(parts) != 2:
            raise ValueError(f"Clave de tile invalida: {tile_key}")
        return int(parts[0]), int(parts[1])

    def _normalize_machine_data(self, machine_data, machine_name=None):
        if machine_data is None and machine_name is None:
            return None

        if isinstance(machine_data, dict):
            normalized = dict(machine_data)
            machine_value = normalized.get("machine", normalized.get("type", machine_name))
            if machine_value is None:
                machine_value = machine_name
            if machine_value is None:
                return None

            normalized["machine"] = machine_value
            normalized.setdefault("type", machine_value)
            for key in ("direction", "in_direction"):
                value = normalized.get(key)
                if value is not None and not isinstance(value, str):
                    # Asume que _direction_name es una función existente o un método para formatear la dirección
                    normalized[key] = str(value)
            return normalized

        machine_value = machine_data if machine_data is not None else machine_name
        if machine_value is None:
            return None

        return {"machine": machine_value, "type": machine_value}

    def _chunk_payload_from_tiles(self, cx, cy, tiles):
        buildings = []
        base_x = cx * self.chunk_size
        base_y = cy * self.chunk_size
        # El terreno y el mineral base se regeneran de forma determinista desde la semilla.
        # Persistimos solo los cambios que el jugador introduce sobre el mapa.
        # Considerar tanto los tiles cargados como cualquier override que exista
        # en `self.machine_overrides` para este chunk.
        coords_to_check = set(tiles.keys())
        for (mx, my) in self.machine_overrides.keys():
            if base_x <= mx < base_x + self.chunk_size and base_y <= my < base_y + self.chunk_size:
                coords_to_check.add((mx, my))

        for (abs_x, abs_y) in coords_to_check:
            # Priorizar machine_overrides cuando exista
            if (abs_x, abs_y) in self.machine_overrides:
                machine_data = self.machine_overrides.get((abs_x, abs_y))
            else:
                tile = tiles.get((abs_x, abs_y))
                machine_data = tile.get("machine") if tile is not None else None

            machine_data = self._normalize_machine_data(machine_data)
            if machine_data is not None:
                building = dict(machine_data)
                building["tile"] = self._tile_key(abs_x - base_x, abs_y - base_y)
                buildings.append(building)

        return {"coords": [cx, cy], "seed": self.base_seed, "buildings": buildings}

    def _chunk_tiles_from_payload(self, payload):
        coords = payload.get("coords", [0, 0])
        cx, cy = int(coords[0]), int(coords[1])
        base_x = cx * self.chunk_size
        base_y = cy * self.chunk_size

        chunk_seed = payload.get("seed", self.base_seed)
        tiles, _ = generate_chunk(cx, cy, seed=chunk_seed, chunk_size=self.chunk_size)

        # Compatibilidad con saves antiguos que todavía incluyan la capa `tiles`.
        for tile_key, tile_data in payload.get("tiles", {}).items():
            local_x, local_y = self._parse_tile_key(tile_key)
            abs_x = base_x + local_x
            abs_y = base_y + local_y
            tile = tiles.get((abs_x, abs_y))
            if tile is None:
                continue

            if "terrain" in tile_data:
                tile["terrain"] = tile_data.get("terrain")
            if "buildable" in tile_data or "canPlace" in tile_data:
                tile["canPlace"] = tile_data.get("buildable", tile_data.get("canPlace", tile.get("canPlace")))
            if "material" in tile_data or "mineral" in tile_data:
                tile["mineral"] = tile_data.get("material", tile_data.get("mineral"))

        for building in payload.get("buildings", []):
            tile_key = building.get("tile")
            if tile_key is None:
                continue

            local_x, local_y = self._parse_tile_key(tile_key)
            abs_x = base_x + local_x
            abs_y = base_y + local_y
            tile = tiles.get((abs_x, abs_y))
            if tile is None:
                continue

            machine_data = self._normalize_machine_data(building, machine_name=building.get("machine"))
            tile["machine"] = machine_data
            self.machine_overrides[(abs_x, abs_y)] = machine_data

        return (cx, cy), tiles

    def _default_meta(self):
        # Asume SAVE_VERSION como "1.0" o definido globalmente, si está definido
        return {
            "name": self.save_name,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "version": getattr(self, "SAVE_VERSION", "1.0"),
            "seed": self.base_seed,
            "player_position": list(self.player_position),
        }

    def _atomic_write_json(self, target_path: Path, data) -> None:
        """Escribe JSON de forma atómica en el mismo directorio.

        Crea un fichero temporal en el mismo directorio y luego lo
        reemplaza con `os.replace` para minimizar archivos corruptos
        por cierres inesperados (funciona en Windows/macOS/Linux).
        """
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(prefix=target_path.name + '.', suffix='.tmp', dir=str(target_dir))
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                json.dump(data, handle, indent=4, ensure_ascii=False, sort_keys=True)
                handle.flush()
                try:
                    os.fsync(handle.fileno())
                except Exception:
                    # fsync may fail on some platforms/filesystems; ignore
                    pass
            os.replace(tmp_path, str(target_path))
        except Exception:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            raise

    def _write_meta(self):
        self._ensure_save_dirs()
        # Use atomic write to avoid partial/corrupt meta files on crash
        self._atomic_write_json(self.meta_path, self.save_meta)

    def _cleanup_empty_chunks(self):
        """Limpia solo las carpetas de chunks vacíos (sin data.json), pero mantiene meta.json"""
        if self.chunks_path.exists():
            # Buscar directorios de chunks que no tengan data.json
            for chunk_dir in self.chunks_path.iterdir():
                if chunk_dir.is_dir():
                    data_file = chunk_dir / "data.json"
                    # Si el directorio no tiene data.json, eliminarlo
                    if not data_file.exists():
                        try:
                            chunk_dir.rmdir()
                        except OSError:
                            # Si el directorio no está vacío, ignorar
                            pass

    def delete_save(self):
        """Elimina completamente la partida incluyendo meta.json y chunks"""
        if self.meta_path.exists():
            self.meta_path.unlink()
        
        self._cleanup_empty_chunks()
        
        if self.save_path.exists():
            try:
                self.save_path.rmdir()
            except OSError:
                pass

    def _save_chunk(self, cx, cy):
        tiles = self.chunks.get((cx, cy))
        if tiles is None:
            # Cargar/generar el chunk en memoria para que se reapliquen overrides
            try:
                self._ensure_chunk(cx, cy)
                tiles = self.chunks.get((cx, cy))
            except Exception:
                tiles = None

            # Si aún no está en memoria, intentar cargar desde disco
            if tiles is None:
                chunk_file = self._chunk_file(cx, cy)
                if chunk_file.exists():
                    try:
                        with chunk_file.open("r", encoding="utf-8") as handle:
                            payload = json.load(handle)
                        coords, tiles = self._chunk_tiles_from_payload(payload)
                        self.chunks[coords] = tiles
                    except Exception:
                        return False
                else:
                    return False

        payload = self._chunk_payload_from_tiles(cx, cy, tiles)

        # No guardar chunks sin máquinas; si existe un archivo previo, eliminarlo
        if not payload.get("buildings"):
            chunk_file = self._chunk_file(cx, cy)
            if chunk_file.exists():
                try:
                    chunk_file.unlink()
                except Exception:
                    pass
                try:
                    self._chunk_dir(cx, cy).rmdir()
                except Exception:
                    pass
            return False

        self._ensure_save_dirs()
        chunk_dir = self._chunk_dir(cx, cy)
        chunk_dir.mkdir(parents=True, exist_ok=True)
        # Atomic write for chunk data as well
        self._atomic_write_json(self._chunk_file(cx, cy), payload)
        return True

    def _has_persistable_content(self):
        for tile in self.get_merged_tiles().values():
            if tile.get("machine") is not None:
                return True
        return False

    def saveMapToJSON(self, chunk_coords=None, player_position=None, inventory=None):
        if player_position is not None:
            self.player_position = [int(player_position[0]), int(player_position[1])]

        # Si no hay contenido persistible (p. ej. ninguna máquina), no crear ni escribir saves.
        # Esto evita crear la carpeta de la partida ni el meta.json hasta que haya algo que guardar.
        if not self._has_persistable_content():
            return False

        # Guardar meta.json para preservar la semilla y posición del jugador
        if not self.save_meta:
            self.save_meta = self._default_meta()
        else:
            self.save_meta.update(
                {
                    "name": self.save_name,
                    "version": getattr(self, "SAVE_VERSION", "1.0"),
                    "seed": self.base_seed,
                    "player_position": list(self.player_position),
                }
            )

        self._write_meta()

        # Guardar solo los chunks que tengan máquinas
        if chunk_coords is None:
            # Recopilar todos los chunks: los cargados en memoria + los que existen en disco
            chunk_coords = list(self.chunks.keys())
            
            # Asegurar que también se guardan los chunks que existen en disco pero no están en memoria
            if self.chunks_path.exists():
                for chunk_file in self.chunks_path.rglob("data.json"):
                    try:
                        with chunk_file.open("r", encoding="utf-8") as handle:
                            payload = json.load(handle)
                        raw = payload.get("coords", [0, 0])
                        try:
                            coords = (int(raw[0]), int(raw[1]))
                        except Exception:
                            # Malformed coords en disco, ignorar
                            continue
                        if coords not in chunk_coords:
                            chunk_coords.append(coords)
                    except Exception:
                        pass

        for cx, cy in chunk_coords:
            self._save_chunk(cx, cy)

        # Limpiar chunks vacíos que no se guardaron
        self._cleanup_empty_chunks()

        self.persistence_enabled = True
        return True

    def loadMapFromJSON(self, save_name=None):
        if save_name is not None:
            self.save_name = save_name

        self.save_path = self.save_root / self.save_name
        self.chunks_path = self.save_path / "chunks"
        self.meta_path = self.save_path / "meta.json"

        self.chunks = {}
        self.machine_overrides = {}

        if self.meta_path.exists():
            with self.meta_path.open("r", encoding="utf-8") as handle:
                self.save_meta = json.load(handle)
            self._ensure_save_dirs()
        else:
            self.save_meta = self._default_meta()
            self.persistence_enabled = False
            return self.save_meta

        loaded_seed = self.save_meta.get("seed")
        if loaded_seed is not None:
            self.base_seed = loaded_seed
        self.player_position = list(self.save_meta.get("player_position", self.player_position))

        if self.chunks_path.exists():
            for chunk_file in self.chunks_path.rglob("data.json"):
                try:
                    with chunk_file.open("r", encoding="utf-8") as handle:
                        payload = json.load(handle)
                    coords, tiles = self._chunk_tiles_from_payload(payload)
                    self.chunks[coords] = tiles
                except Exception:
                    continue

        self.persistence_enabled = True
        return self.save_meta

    def _ensure_chunk(self, cx, cy):
        if (cx, cy) in self.chunks:
            return
        tiles, derived_seed = generate_chunk(cx, cy, seed=self.base_seed, chunk_size=self.chunk_size)

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

        # Aplicar machine_overrides como overlay: asegurarse de que cualquier
        # override (incluso si el chunk no está cargado) sea visible en el merge
        for (mx, my), machine in self.machine_overrides.items():
            if (mx, my) in merged:
                try:
                    merged[(mx, my)]["machine"] = machine
                except Exception:
                    merged[(mx, my)] = {"machine": machine}
            else:
                # Insertar un tile mínimo para representar el override
                merged[(mx, my)] = {"machine": machine}

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

        # Persistir automáticamente la colocación para que la interfaz y tests
        # encuentren los archivos de save inmediatamente después de colocar.
        try:
            self.saveMapToJSON()
        except Exception:
            # No propagar errores de persistencia a la lógica de colocación
            pass

        # Reproducir sonido de colocación si el mixer está inicializado (evitar fallos en tests)
        try:
            import pygame
            if getattr(pygame, "mixer", None) is not None and pygame.mixer.get_init():
                try:
                    from sound_manager import play_place_sound
                    mname = final_machine_data if isinstance(final_machine_data, str) else final_machine_data.get("machine")
                    if mname:
                        try:
                            play_place_sound(mname)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

        return True

    def restore_structures(self, conveyor_system, drill_system):
        """Reconstruye estructuras en los sistemas provistos a partir del estado guardado.

        Añade cintas y taladros encontrados en los tiles cargados.
        """
        # Importar localmente para evitar posibles dependencias circulares
        from build_system import MACHINE_CONVEYOR, MACHINE_DRILL, MACHINE_INVENTORY
        from logic.conveyor import ConveyorBelt, ConveyorCurve

        merged = self.get_merged_tiles()
        for (x, y), tile in merged.items():
            md = tile.get("machine")
            if md is None:
                continue

            # Normalizar a dict si es necesario
            if not isinstance(md, dict):
                machine_name = md
                md = {"machine": md}
            else:
                machine_name = md.get("machine")

            try:
                if machine_name == MACHINE_CONVEYOR:
                    dir_name = md.get("direction")
                    in_dir_name = md.get("in_direction")
                    dir_val = None
                    in_dir_val = None
                    try:
                        if dir_name:
                            dir_val = Direction[dir_name]
                    except Exception:
                        dir_val = None
                    try:
                        if in_dir_name:
                            in_dir_val = Direction[in_dir_name]
                    except Exception:
                        in_dir_val = None

                    if dir_val is None:
                        dir_val = Direction.RIGHT

                    if in_dir_val is not None and in_dir_val != dir_val:
                        belt = ConveyorCurve(x, y, dir_val, in_dir_val)
                    else:
                        belt = ConveyorBelt(x, y, dir_val, incoming_direction=in_dir_val)

                    try:
                        conveyor_system.add_belt(belt)
                    except Exception:
                        pass

                elif machine_name == MACHINE_DRILL:
                    dir_name = md.get("direction")
                    mineral = md.get("mineral") or md.get("material")
                    dir_val = None
                    try:
                        if dir_name:
                            dir_val = Direction[dir_name]
                    except Exception:
                        dir_val = None

                    if dir_val is None:
                        dir_val = Direction.RIGHT

                    try:
                        drill = drill_system.create_drill(x, y, dir_val, mineral)
                        drill_system.add_drill(drill)
                    except Exception:
                        pass

                elif machine_name == MACHINE_INVENTORY:
                    # Inventarios se gestionan por el sistema de inventarios externo; ignorar aquí
                    pass
            except Exception:
                # Seguir procesando otros tiles aunque uno falle
                continue

    def clear_machine(self, x, y):
        """Elimina la máquina del tile si existe."""
        tile = self.get_tile(x, y, ensure_chunk=False)
        if tile is not None:
            tile["machine"] = None

        if (x, y) in self.machine_overrides:
            # Reproducir sonido de eliminación si el mixer está inicializado
            try:
                md = self.machine_overrides.get((x, y))
                import pygame
                if getattr(pygame, "mixer", None) is not None and pygame.mixer.get_init():
                    try:
                        from sound_manager import play_delete_sound
                        mname = md if isinstance(md, str) else (md.get("machine") if isinstance(md, dict) else None)
                        if mname:
                            try:
                                play_delete_sound(mname)
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass

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