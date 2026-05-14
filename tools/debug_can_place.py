from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from map_manager import MapManager
from asset_manager import default_save_root

save_root = Path('saves')
manager = MapManager(save_root=save_root, save_name='partida1')
meta = manager.loadMapFromJSON()
print('Loaded meta:', meta)

# Collect chunk coords known
chunk_coords = list(manager.chunks.keys())
print('Chunks in memory:', chunk_coords)

# Expand region around loaded chunks
tile_issues = []
for (cx, cy) in chunk_coords:
    base_x = cx * manager.chunk_size
    base_y = cy * manager.chunk_size
    for lx in range(manager.chunk_size):
        for ly in range(manager.chunk_size):
            x = base_x + lx
            y = base_y + ly
            tile = manager.get_tile(x, y, ensure_chunk=True)
            if tile is None:
                tile_issues.append(((x, y), 'missing_tile'))
                continue
            can_place = tile.get('canPlace')
            machine = tile.get('machine')
            # Use manager.can_place_machine check
            can_place_fn = manager.can_place_machine(x, y)
            if not can_place_fn:
                reason = None
                if machine is not None:
                    reason = f'machine_present={machine}'
                elif can_place is False:
                    reason = 'terrain_blocked'
                else:
                    reason = f'canPlace={can_place}'
                tile_issues.append(((x, y), reason, tile))

print('Found issues:', len(tile_issues))
for entry in tile_issues[:200]:
    print(entry)

# Also check some neighbor tiles beyond loaded chunks (one chunk adjacent)
adj_issues = []
for cx in range(min(c[0] for c in chunk_coords)-1, max(c[0] for c in chunk_coords)+2):
    for cy in range(min(c[1] for c in chunk_coords)-1, max(c[1] for c in chunk_coords)+2):
        base_x = cx * manager.chunk_size
        base_y = cy * manager.chunk_size
        for lx in range(manager.chunk_size):
            for ly in range(manager.chunk_size):
                x = base_x + lx
                y = base_y + ly
                # skip already checked
                if (x, y) in [t[0] for t in tile_issues]:
                    continue
                # ask can_place without forcing chunk into memory
                try:
                    tile = manager.get_tile(x, y, ensure_chunk=False)
                    can_place = manager.can_place_machine(x, y)
                    if not can_place:
                        adj_issues.append(((x, y), 'cannot_place_no_ensure', tile))
                except Exception as e:
                    adj_issues.append(((x, y), 'error', str(e)))

print('Adjacency issues (no ensure):', len(adj_issues))
for a in adj_issues[:100]:
    print(a)

print('Done')
