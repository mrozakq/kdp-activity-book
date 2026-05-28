"""
Kid-friendly sudoku for KDP Activity Book.

Sizes:
  4x4 with 2x2 boxes (numbers 1-4)
  6x6 with 2-row × 3-col boxes (numbers 1-6)

Algorithm: randomized backtracking to fill solved grid,
then remove cells until target "givens" count is reached.
We don't enforce unique-solution constraint (overkill for kids);
the removal is symmetric to keep things visually balanced.
"""
import random

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font
from .layout import compute_activity_box, title_position


# (size, box_rows, box_cols, easy_givens, medium_givens, hard_givens)
SUDOKU_PRESETS = {
    '4x4': (4, 2, 2, 9, 7, 5),     # out of 16 cells
    '6x6': (6, 2, 3, 22, 18, 14),  # out of 36 cells
}


def _generate_solved(size: int, box_rows: int, box_cols: int, seed: int):
    """Fill an N×N sudoku grid via randomized backtracking."""
    rng = random.Random(seed)
    grid = [[0] * size for _ in range(size)]

    def valid(r, c, v):
        for i in range(size):
            if grid[r][i] == v or grid[i][c] == v:
                return False
        br, bc = (r // box_rows) * box_rows, (c // box_cols) * box_cols
        for i in range(br, br + box_rows):
            for j in range(bc, bc + box_cols):
                if grid[i][j] == v:
                    return False
        return True

    def backtrack(pos: int) -> bool:
        if pos == size * size:
            return True
        r, c = divmod(pos, size)
        vals = list(range(1, size + 1))
        rng.shuffle(vals)
        for v in vals:
            if valid(r, c, v):
                grid[r][c] = v
                if backtrack(pos + 1):
                    return True
                grid[r][c] = 0
        return False

    backtrack(0)
    return grid


def _make_puzzle(grid, givens: int, seed: int):
    """Remove cells from a solved grid until only `givens` cells remain. Symmetric."""
    size = len(grid)
    rng = random.Random(seed + 1)
    puzzle = [row[:] for row in grid]

    # Cell pairs for 180° symmetry (each pair removed together)
    cells = [(r, c) for r in range(size) for c in range(size)]
    pairs = set()
    seen = set()
    for (r, c) in cells:
        if (r, c) in seen:
            continue
        mirror = (size - 1 - r, size - 1 - c)
        pairs.add(((r, c), mirror))
        seen.add((r, c))
        seen.add(mirror)

    pair_list = list(pairs)
    rng.shuffle(pair_list)

    target_remove = size * size - givens
    removed = 0
    for ((r1, c1), (r2, c2)) in pair_list:
        if removed >= target_remove:
            break
        if (r1, c1) == (r2, c2):
            puzzle[r1][c1] = 0
            removed += 1
        else:
            puzzle[r1][c1] = 0
            puzzle[r2][c2] = 0
            removed += 2

    return puzzle


def render_sudoku(puzzle, box_rows: int, box_cols: int,
                  canvas_size=(2550, 3300), title='Sudoku'):
    size = len(puzzle)
    cw, ch = canvas_size

    x1, y1, x2, y2 = compute_activity_box(canvas_size)
    avail = min(x2 - x1, y2 - y1)
    cell = avail // size
    grid_size = cell * size

    off_x = (cw - grid_size) // 2
    off_y = y1 + (y2 - y1 - grid_size) // 2

    img = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    title_font = get_title_font(130)
    digit_font = get_body_font(int(cell * 0.63))

    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black', font=title_font)

    # Thin lines for every cell
    thin = 3
    thick = 10
    for i in range(size + 1):
        # Vertical
        w = thick if i % box_cols == 0 else thin
        x = off_x + i * cell
        draw.line([(x, off_y), (x, off_y + grid_size)], fill='black', width=w)
        # Horizontal
        w = thick if i % box_rows == 0 else thin
        y = off_y + i * cell
        draw.line([(off_x, y), (off_x + grid_size, y)], fill='black', width=w)

    # Digits in filled cells
    for r in range(size):
        for c in range(size):
            v = puzzle[r][c]
            if v == 0:
                continue
            x = off_x + c * cell + cell // 2
            y = off_y + r * cell + cell // 2
            draw.text((x, y), str(v), anchor='mm',
                      fill='black', font=digit_font)

    return img


def generate_sudoku_image(size_key: str, difficulty: str, seed: int, title: str,
                          canvas_size=(2550, 3300), return_solution=False):
    if size_key not in SUDOKU_PRESETS:
        size_key = '4x4'
    size, br, bc, e_g, m_g, h_g = SUDOKU_PRESETS[size_key]
    givens = {'easy': e_g, 'medium': m_g, 'hard': h_g}.get(difficulty, m_g)

    solved = _generate_solved(size, br, bc, seed)
    puzzle = _make_puzzle(solved, givens, seed)
    img = render_sudoku(puzzle, br, bc, canvas_size=canvas_size, title=title)
    if return_solution:
        return img, {'type': 'sudoku',
                     'data': {'solved': solved, 'box_rows': br,
                              'box_cols': bc, 'size': size}}
    return img
