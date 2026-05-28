import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.activity_bot.magic_square import _make_puzzle, _symmetries, LO_SHU  # noqa: E402


def _valid(full):
    ms = sum(full[0])
    for i in range(3):
        assert sum(full[i]) == ms
        assert sum(full[r][i] for r in range(3)) == ms
    assert sum(full[i][i] for i in range(3)) == ms
    assert sum(full[i][2 - i] for i in range(3)) == ms


def test_eight_distinct_solutions_per_volume():
    # consecutive seeds (as produced by activity.py: seed_base+4000+n) → all distinct
    for seed_base in (0, 777, 12345, 99999):
        fulls = []
        for n in range(1, 9):
            _, full, _ = _make_puzzle(seed_base + 4000 + n, holes=3)
            fulls.append(tuple(tuple(r) for r in full))
        assert len({*fulls}) == 8, f"collisions at seed_base={seed_base}"


def test_puzzles_valid_and_clues_consistent():
    for seed in range(4001, 4101):
        puz, full, ms = _make_puzzle(seed, holes=3)
        _valid(full)
        for r in range(3):
            for c in range(3):
                if puz[r][c] != 0:
                    assert puz[r][c] == full[r][c]


def test_symmetries_are_unique():
    syms = _symmetries(LO_SHU)
    assert len(syms) == 8
    assert len({tuple(tuple(r) for r in g) for g in syms}) == 8
