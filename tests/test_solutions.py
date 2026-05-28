"""
Etap 2A — verify generate_*_image(..., return_solution=True) returns a
correct solution alongside the image. These tests check the MEANING of the
solution (not just its shape), because Etap 2B renders answer-key pages from it.

Contract under test:
  - return_solution=False (default) -> a bare PIL.Image (unchanged behaviour)
  - return_solution=True            -> (PIL.Image, {'type': str, 'data': ...})
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.activity_bot.maze import generate_maze_image          # noqa: E402
from tools.activity_bot.sudoku import generate_sudoku_image      # noqa: E402
from tools.activity_bot.magic_square import generate_magic_square_image  # noqa: E402
from tools.activity_bot.path_sums import generate_path_sums_image       # noqa: E402
from tools.activity_bot.math_maze import generate_math_maze_image, _matches  # noqa: E402
from tools.activity_bot.wordsearch import generate_wordsearch_image     # noqa: E402
from tools.activity_bot.counting import generate_counting_image, OBJECT_TYPES, DIFFICULTY_PRESETS as CNT_PRESETS  # noqa: E402
from tools.activity_bot.pattern import generate_pattern_image, SHAPE_LIST  # noqa: E402


SMALL = (1200, 1600)   # small canvas keeps the tests fast


# --------------------------------------------------------------------------
# Default-mode contract: bare Image, no tuple (regression for current callers)
# --------------------------------------------------------------------------

def test_default_returns_bare_image():
    cases = [
        generate_maze_image('easy', 1, 'Maze', canvas_size=SMALL),
        generate_sudoku_image('4x4', 'easy', 1, 'Sudoku', canvas_size=SMALL),
        generate_magic_square_image('easy', 1, 'Magic', canvas_size=SMALL),
        generate_path_sums_image('easy', 1, 'Path', canvas_size=SMALL),
        generate_math_maze_image('easy', 1, 'Math', canvas_size=SMALL),
        generate_wordsearch_image('ai_kids_basics_en', 'easy', 1, 'WS', canvas_size=SMALL),
        generate_counting_image('easy', 1, 'Count', canvas_size=SMALL),
        generate_pattern_image('easy', 1, 'Pattern', canvas_size=SMALL),
    ]
    for obj in cases:
        assert isinstance(obj, Image.Image), f'expected bare Image, got {type(obj)}'


def _unpack(obj, expected_type):
    assert isinstance(obj, tuple) and len(obj) == 2, 'return_solution must yield a 2-tuple'
    img, sol = obj
    assert isinstance(img, Image.Image)
    assert isinstance(sol, dict) and sol.get('type') == expected_type
    assert 'data' in sol
    return sol['data']


# --------------------------------------------------------------------------
# Sudoku
# --------------------------------------------------------------------------

def test_sudoku_solution():
    for size_key, diff in [('4x4', 'easy'), ('6x6', 'medium')]:
        d = _unpack(generate_sudoku_image(size_key, diff, 7, 'Sudoku',
                                          canvas_size=SMALL, return_solution=True),
                    'sudoku')
        solved, br, bc, size = d['solved'], d['box_rows'], d['box_cols'], d['size']
        full = set(range(1, size + 1))
        # rows + cols
        for i in range(size):
            assert set(solved[i]) == full, f'row {i} not a permutation'
            assert set(solved[r][i] for r in range(size)) == full, f'col {i} bad'
        # boxes
        for br0 in range(0, size, br):
            for bc0 in range(0, size, bc):
                vals = [solved[br0 + dr][bc0 + dc]
                        for dr in range(br) for dc in range(bc)]
                assert set(vals) == full, f'box at {br0},{bc0} bad'


# --------------------------------------------------------------------------
# Magic square
# --------------------------------------------------------------------------

def test_magic_solution():
    for diff in ('easy', 'medium', 'hard'):
        d = _unpack(generate_magic_square_image(diff, 3, 'Magic',
                                                canvas_size=SMALL, return_solution=True),
                    'magic')
        full, ms = d['full'], d['magic_sum']
        for r in range(3):
            assert sum(full[r]) == ms, f'row {r} != {ms}'
        for c in range(3):
            assert sum(full[r][c] for r in range(3)) == ms, f'col {c} != {ms}'
        assert sum(full[i][i] for i in range(3)) == ms, 'main diag != ms'
        assert sum(full[i][2 - i] for i in range(3)) == ms, 'anti diag != ms'


# --------------------------------------------------------------------------
# Path sums
# --------------------------------------------------------------------------

def test_pathsum_solution():
    for diff in ('easy', 'medium', 'hard'):
        d = _unpack(generate_path_sums_image(diff, 5, 'Path',
                                             canvas_size=SMALL, return_solution=True),
                    'pathsum')
        path, target, grid = d['path'], d['target'], d['grid']
        rows, cols = len(grid), len(grid[0])
        assert path[0] == (0, 0)
        assert path[-1] == (rows - 1, cols - 1)
        # monotone right/down, single steps
        for (r0, c0), (r1, c1) in zip(path, path[1:]):
            assert (r1 - r0, c1 - c0) in ((1, 0), (0, 1)), 'illegal step'
        assert sum(grid[r][c] for (r, c) in path) == target, 'path sum != target'


# --------------------------------------------------------------------------
# Math maze
# --------------------------------------------------------------------------

def test_mathmaze_solution():
    for diff in ('easy', 'medium', 'hard'):
        d = _unpack(generate_math_maze_image(diff, 9, 'Math',
                                             canvas_size=SMALL, return_solution=True),
                    'mathmaze')
        path, rule, param, grid = d['path'], d['rule'], d['param'], d['grid']
        rows, cols = len(grid), len(grid[0])
        assert path[0] == (0, 0)
        assert path[-1] == (rows - 1, cols - 1)
        for (r0, c0), (r1, c1) in zip(path, path[1:]):
            assert (r1 - r0, c1 - c0) in ((1, 0), (0, 1)), 'illegal step'
        for (r, c) in path:
            assert _matches(grid[r][c], rule, param), \
                f'cell {r},{c}={grid[r][c]} breaks rule {rule}/{param}'


# --------------------------------------------------------------------------
# Word search
# --------------------------------------------------------------------------

def test_wordsearch_solution():
    d = _unpack(generate_wordsearch_image('ai_kids_director_en', 'medium', 11, 'WS',
                                          canvas_size=SMALL, return_solution=True),
                'wordsearch')
    placements, grid = d['placements'], d['grid']
    rows, cols = len(grid), len(grid[0])
    assert placements, 'no words placed'
    for (word, r, c, dr, dc) in placements:
        spelled = ''
        for i in range(len(word)):
            rr, cc = r + dr * i, c + dc * i
            assert 0 <= rr < rows and 0 <= cc < cols, 'placement out of bounds'
            spelled += grid[rr][cc]
        assert spelled == word, f'{word!r} != spelled {spelled!r}'


# --------------------------------------------------------------------------
# Counting
# --------------------------------------------------------------------------

def test_counting_solution():
    for diff in ('easy', 'medium', 'hard'):
        lo, hi = CNT_PRESETS[diff]
        d = _unpack(generate_counting_image(diff, 4, 'Count',
                                            canvas_size=SMALL, return_solution=True),
                    'counting')
        # The generator asserts placed == count internally; here we sanity-check
        # the reported answer is in range and kind is valid.
        assert lo <= d['count'] <= hi, f"count {d['count']} out of range {lo}-{hi}"
        assert d['kind'] in OBJECT_TYPES


# --------------------------------------------------------------------------
# Pattern
# --------------------------------------------------------------------------

def test_pattern_solution():
    for diff in ('easy', 'medium', 'hard'):
        d = _unpack(generate_pattern_image(diff, 2, 'Pattern',
                                           canvas_size=SMALL, return_solution=True),
                    'pattern')
        answers, rows = d['answers'], d['rows']
        assert len(answers) == rows
        for a in answers:
            assert a in SHAPE_LIST, f'bad shape {a!r}'


# --------------------------------------------------------------------------
# Maze (solver)
# --------------------------------------------------------------------------

def test_maze_solution():
    for diff in ('easy', 'medium', 'hard'):
        d = _unpack(generate_maze_image(diff, 13, 'Maze',
                                        canvas_size=SMALL, return_solution=True),
                    'maze')
        path, rows, cols, walls = d['path'], d['rows'], d['cols'], d['walls']
        assert path, 'empty path'
        assert path[0] == (0, 0)
        assert path[-1] == (rows - 1, cols - 1)
        assert len(set(path)) == len(path), 'path revisits a cell'
        for (r0, c0), (r1, c1) in zip(path, path[1:]):
            dr, dc = r1 - r0, c1 - c0
            assert (dr, dc) in ((-1, 0), (1, 0), (0, -1), (0, 1)), 'non-adjacent step'
            w = walls[r0][c0]
            if dr == -1:   open_side = not w[0]   # N
            elif dc == 1:  open_side = not w[1]   # E
            elif dr == 1:  open_side = not w[2]   # S
            else:          open_side = not w[3]   # W
            assert open_side, f'step {(r0, c0)}->{(r1, c1)} crosses a wall'
