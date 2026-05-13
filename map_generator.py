from numpy import random
from settings import MAP_SIZE, TERRAINS, ORES
import time


def _place_cluster(tiles, material, cx, cy):
    """Coloca una mina en forma de cluster centrado en (cx,cy).

    Se intenta colocar en cada celda del cluster si el terreno permite colocar.
    No sobrescribe minerales ya colocados y no coloca en terrenos con canPlace=False (agua).
    """
    size = ORES.get(material, {}).get("cluster", 1)
    half = size // 2

    fill_prob = ORES.get(material, {}).get("cluster_fill_prob", 1.0)

    for i in range(cx - half, cx - half + size):
        for j in range(cy - half, cy - half + size):
            tile = tiles.get((i, j))
            if tile is None:
                continue
            terrain = tile["terrain"]
            # El centro siempre se coloca, el resto con probabilidad
            is_center = (i == cx and j == cy)
            if not TERRAINS[terrain].get("canPlace"):
                continue
            if tile.get("mineral") is not None:
                continue
            if is_center or random.random() < fill_prob:
                tile["mineral"] = material


def _place_terrain_cluster(tiles, terrain_name, cx, cy):
    """Coloca un cluster de terreno (por ejemplo agua) centrado en (cx,cy).

    Sobrescribe el `terrain` y `canPlace` de las celdas afectadas.
    """
    size = TERRAINS.get(terrain_name, {}).get("cluster", 1)
    half = size // 2

    fill_prob = TERRAINS.get(terrain_name, {}).get("cluster_fill_prob", 1.0)

    for i in range(cx - half, cx - half + size):
        for j in range(cy - half, cy - half + size):
            tile = tiles.get((i, j))
            if tile is None:
                continue
            is_center = (i == cx and j == cy)
            if is_center or random.random() < fill_prob:
                tile["terrain"] = terrain_name
                tile["canPlace"] = TERRAINS[terrain_name].get("canPlace")


def generate_map(seed=None):
    """Genera el mapa y devuelve (tiles, seed).

    La generación se hace en dos pasadas: una para terrenos y otra
    para colocar minerales como clusters según `ORES[<name>]["cluster"]`.
    Si una celda del cluster es agua no se coloca en esa celda, pero sí en el resto.
    """
    if seed is None:
        seed = int(time.time() * 1000) & 0x7FFFFFFF

    random.seed(seed)

    tiles = {}

    # Primera pasada: llenar el mapa con un terreno por defecto (GRASS si existe)
    default_terrain = "GRASS" if "GRASS" in TERRAINS else list(TERRAINS.keys())[0]
    for x in range(MAP_SIZE):
        for y in range(MAP_SIZE):
            tiles[(x, y)] = {
                "terrain": default_terrain,
                "canPlace": TERRAINS[default_terrain].get("canPlace"),
                "mineral": None,
                "machine": None,
            }

    # Colocar clusters de terrenos (por ejemplo WATER) según spawn_prob y tamaño
    for terrain_name, info in TERRAINS.items():
        if terrain_name == default_terrain:
            continue
        spawn_prob = info.get("spawn_prob", 0)
        if spawn_prob <= 0:
            continue
        for x in range(MAP_SIZE):
            for y in range(MAP_SIZE):
                if random.random() < spawn_prob:
                    _place_terrain_cluster(tiles, terrain_name, x, y)

    # Preparar lista de materiales y probabilidades si están definidas
    material_keys = list(MATERIALS.keys())
    spawn_probs = None
    if material_keys and all("spawn_prob" in MATERIALS[m] for m in material_keys):
        probs = [MATERIALS[m]["spawn_prob"] for m in material_keys]
        total = sum(probs) or 1
        spawn_probs = [p / total for p in probs]

    # Segunda pasada: asignar minerales por clusters
    for x in range(MAP_SIZE):
        for y in range(MAP_SIZE):
            tile = tiles[(x, y)]
            if tile["canPlace"] and tile.get("mineral") is None and random.random() < 0.2:
                if spawn_probs:
                    material = random.choice(material_keys, p=spawn_probs)
                else:
                    material = random.choice(material_keys)

                _place_cluster(tiles, material, x, y)

    return tiles, seed


def _derive_chunk_seed(base_seed, cx, cy):
    # Mezclar coordenadas del chunk con la semilla base para determinismo por-chunk
    if base_seed is None:
        base = int(time.time() * 1000) & 0x7FFFFFFF
    else:
        base = int(base_seed) & 0x7FFFFFFF
    return (base + (cx * 1000003) + (cy * 9176)) & 0x7FFFFFFF


def generate_chunk(chunk_x, chunk_y, seed=None, chunk_size=8):
    """Genera un chunk de tamaño `chunk_size` en coordenadas de chunk (chunk_x,chunk_y).

    Devuelve un diccionario con tiles con keys como (abs_x, abs_y) y la semilla usada.
    Las coordenadas absoluttas se calculan como:
        abs_x = chunk_x * chunk_size + local_x
    """
    # derivar semilla por chunk para que sea reproducible
    derived = _derive_chunk_seed(seed, chunk_x, chunk_y)
    random.seed(derived)

    tiles = {}

    default_terrain = "GRASS" if "GRASS" in TERRAINS else list(TERRAINS.keys())[0]

    base_x = chunk_x * chunk_size
    base_y = chunk_y * chunk_size

    # Inicializar celdas del chunk
    for lx in range(chunk_size):
        for ly in range(chunk_size):
            abs_x = base_x + lx
            abs_y = base_y + ly
            tiles[(abs_x, abs_y)] = {
                "terrain": default_terrain,
                "canPlace": TERRAINS[default_terrain].get("canPlace"),
                "mineral": None,
                "machine": None,
            }

    # Colocar clusters de terrenos según spawn_prob dentro del chunk
    for terrain_name, info in TERRAINS.items():
        if terrain_name == default_terrain:
            continue
        spawn_prob = info.get("spawn_prob", 0)
        if spawn_prob <= 0:
            continue
        for lx in range(chunk_size):
            for ly in range(chunk_size):
                if random.random() < spawn_prob:
                    _place_terrain_cluster(tiles, terrain_name, base_x + lx, base_y + ly)

    # Preparar lista de materiales y probabilidades si están definidas
    material_keys = list(ORES.keys())
    spawn_probs = None
    if material_keys and all("spawn_prob" in ORES[m] for m in material_keys):
        probs = [ORES[m]["spawn_prob"] for m in material_keys]
        total = sum(probs) or 1
        spawn_probs = [p / total for p in probs]

    # Asignar minerales por clusters dentro del chunk
    for lx in range(chunk_size):
        for ly in range(chunk_size):
            abs_x = base_x + lx
            abs_y = base_y + ly
            tile = tiles[(abs_x, abs_y)]
            if tile["canPlace"] and tile.get("mineral") is None and random.random() < 0.2:
                if spawn_probs:
                    material = random.choice(material_keys, p=spawn_probs)
                else:
                    material = random.choice(material_keys)

                _place_cluster(tiles, material, abs_x, abs_y)

    return tiles, derived