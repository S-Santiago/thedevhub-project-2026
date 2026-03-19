from numpy import random
from settings import MAP_SIZE, TERRAINS, MATERIALS

def generate_map():
    tiles = {}
    for x in range(MAP_SIZE):
        for y in range(MAP_SIZE):
            terrain_keys = list(TERRAINS.keys())
            tile_terrain = random.choice(terrain_keys, p=[0.95, 0.05]) # Probabilidad de 95% para GRASS y 5% para WATER
            tile_material = None
            
            # Solo asignamos material si el terreno permite colocar y con 20% de probabilidad
            if TERRAINS[tile_terrain].get("canPlace") and random.random() < 0.2:
                tile_material = random.choice(
                    list(MATERIALS.keys()), 
                    p=[0.3, 0.3, 0.1, 0.1, 0.1, 0.1]
                )

            tiles[(x, y)] = {
                "terrain": tile_terrain,
                "canPlace": TERRAINS[tile_terrain].get("canPlace"),
                "mineral": tile_material,
                "machine": None
            }
            
    return tiles