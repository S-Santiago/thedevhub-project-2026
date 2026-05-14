from pathlib import Path
import sys

# Ensure workspace root is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from map_generator import generate_chunk


def test_generate_chunk_deterministic():
    tiles1, s1 = generate_chunk(0, 0, seed=42, chunk_size=4)
    tiles2, s2 = generate_chunk(0, 0, seed=42, chunk_size=4)
    assert s1 == s2
    assert tiles1 == tiles2


def test_generate_chunk_different_seeds():
    _, s1 = generate_chunk(0, 0, seed=42, chunk_size=4)
    _, s2 = generate_chunk(0, 0, seed=43, chunk_size=4)
    assert s1 != s2
