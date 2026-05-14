from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from map_manager import MapManager

save_root = Path('saves')
manager = MapManager(save_root=save_root, save_name='partida1')
manager.loadMapFromJSON()

issues = []
for (cx, cy), tiles in manager.chunks.items():
    base_x = cx * manager.chunk_size
    base_y = cy * manager.chunk_size
    for lx in range(manager.chunk_size):
        for ly in range(manager.chunk_size):
            x = base_x + lx
            y = base_y + ly
            tile = manager.get_tile(x, y, ensure_chunk=True)
            if tile is None:
                continue
            canPlace = tile.get('canPlace')
            machine = tile.get('machine')
            can_place_method = manager.can_place_machine(x, y)
            if canPlace and machine is None and not can_place_method:
                issues.append(((x,y), tile))

print('Found discrepancies:', len(issues))
for it in issues[:200]:
    print(it)
