import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.activity_bot.path_sums import _make_puzzle  # noqa: E402


def _count_paths(grid, target):
    R, C = len(grid), len(grid[0])
    cnt = 0

    def dfs(r, c, s):
        nonlocal cnt
        s += grid[r][c]
        if (r, c) == (R - 1, C - 1):
            if s == target:
                cnt += 1
            return
        if r + 1 < R:
            dfs(r + 1, c, s)
        if c + 1 < C:
            dfs(r, c + 1, s)

    dfs(0, 0, 0)
    return cnt


def test_unique_path_all_presets():
    for rows, cols, vmax in [(4, 4, 5), (5, 5, 7), (6, 6, 9)]:
        for seed in range(300):
            grid, target, path = _make_puzzle(rows, cols, vmax, seed)
            assert _count_paths(grid, target) == 1, \
                f"non-unique at {rows}x{cols} seed={seed}"


def test_planted_path_sums_to_target():
    for seed in range(100):
        grid, target, path = _make_puzzle(6, 6, 9, seed)
        assert sum(grid[r][c] for r, c in path) == target


def test_digits_single_figure():
    grid, target, path = _make_puzzle(6, 6, 9, 7)
    for row in grid:
        for v in row:
            assert 1 <= v <= 9
