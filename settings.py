MATERIALS = {
    "WOOD": {"cluster": 1, "spawn_prob": 0.15, "cluster_fill_prob": 0.2},
    "STONE": {"cluster": 2, "spawn_prob": 0.20, "cluster_fill_prob": 0.2},
    "COPPER": {"cluster": 2, "spawn_prob": 0.20, "cluster_fill_prob": 0.2},
    "IRON": {"cluster": 3, "spawn_prob": 0.25, "cluster_fill_prob": 0.2},
    "COAL": {"cluster": 2, "spawn_prob": 0.20, "cluster_fill_prob": 0.2},
}

# Compatibility aliases used by asset loading and other modules
# `ORES` mirrors all material types; `MINERALS` is the subset used for mineral-specific assets.
ORES = dict(MATERIALS)
MINERALS = dict(MATERIALS)

MACHINES = {
    "DRILL": {}, "ASSEMBLER": {}, 
    "FURNACE": {}, "INSERTER": {},
    "CONVEYOR": {},
    "CHEST": {},
}

TERRAINS = {
    "GRASS": {"canPlace": True, "cluster": 1, "cluster_fill_prob": 1.0},
    "WATER": {"canPlace": False, "cluster": 3, "spawn_prob": 0.05, "cluster_fill_prob": 0.2},
}

APP_ID = "thedevhub.project2026"
APP_NAME = "The Dev Hub"

MAP_SIZE = 20
ASSETS_PATH = "./assets/"
MIN_TILE_SIZE = 32

# Gameplay tuning
CAMERA_SPEED = 600.0
DRILL_DEFAULT_CYCLE_SECONDS = 1.5
DRILL_OUTPUT_BUFFER_CAPACITY = 3

# Chunked map settings
CHUNK_SIZE = 32
# Cuántos chunks extra cargar alrededor de la vista (margen)
VIEW_CHUNK_MARGIN = 1
# Base seed opcional para generación determinista por sesión
BASE_SEED = None
# Radio (en chunks) para mantener en caché alrededor del centro de la vista
CHUNK_CACHE_RADIUS = 3

USER_OPTIONS = {
    "screen": 1,
    "fullscreen": False,
    "fps": 60,
}