"""
Path-sums puzzle for KDP Activity Book.

A grid of single-digit numbers.  The kid finds a path from the top-left
START to the bottom-right FINISH using only RIGHT or DOWN moves so that
the visited cells sum to a target value.

Generation:
- pick a random monotone path
- fill its cells with random small numbers; remember the sum (target)
- fill the rest of the grid with random numbers in the same range

There may be other paths whose sum also matches (we don't enforce uniqueness —
appropriate for kid-level puzzles).
"""
import random

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font, get_label_font
from .layout import compute_activity_box, title_position, instruction_position


# (rows, cols, value_range_max)
DIFFICULTY_PRESETS = {
    'easy':   (4, 4, 5),
    'medium': (5, 5, 7),
    'hard':   (6, 6, 9),
}


def _random_path(rows, cols, rng):
    """Return a list of (r, c) coordinates forming a monotone right/down path
    from (0, 0) to (rows-1, cols-1)."""
    moves = ['D'] * (rows - 1) + ['R'] * (cols - 1)
    rng.shuffle(moves)
    path = [(0, 0)]
    r, c = 0, 0
    for m in moves:
        if m == 'D':
            r += 1
        else:
            c += 1
        path.append((r, c))
    return path


def _make_puzzle(rows, cols, value_max, seed):
    rng = random.Random(seed)
    path = _random_path(rows, cols, rng)
    grid = [[rng.randint(1, value_max) for _ in range(cols)]
            for _ in range(rows)]
    # Re-roll path cells so we know exactly what the target is
    target = 0
    for (r, c) in path:
        v = rng.randint(1, value_max)
        grid[r][c] = v
        target += v
    return grid, target, path


def render_path_sums(canvas_size, title, grid, target):
    cw, ch = canvas_size
    rows = len(grid)
    cols = len(grid[0])

    # 2-line instruction + START/FINISH labels inside activity_box
    label_reserve = 80
    x1, y1, x2, y2 = compute_activity_box(canvas_size, has_instruction=True,
                                           instruction_lines=2,
                                           footer_reserve_px=160)
    avail_w = x2 - x1
    avail_h = (y2 - y1) - 2 * label_reserve

    cell = int(min(avail_w / cols, avail_h / rows))
    grid_w = cell * cols
    grid_h = cell * rows
    grid_left = (cw - grid_w) // 2
    grid_top = y1 + label_reserve + ((y2 - y1) - 2 * label_reserve - grid_h) // 2

    img = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    title_font = get_title_font(130)
    instr_font = get_body_font(80)
    digit_font = get_body_font(int(cell * 0.63))
    sf_font    = get_label_font(int(cell * 0.345))

    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black', font=title_font)

    ix0, iy0 = instruction_position(canvas_size, line_index=0)
    ix1, iy1 = instruction_position(canvas_size, line_index=1)
    draw.text((ix0, iy0), 'Path from START to FINISH (RIGHT or DOWN only).',
              anchor='mt', fill='black', font=instr_font)
    draw.text((ix1, iy1), f'Sum of cells on the path = {target}',
              anchor='mt', fill='black', font=instr_font)

    # Cells
    for r in range(rows):
        for c in range(cols):
            x0 = grid_left + c * cell
            y0 = grid_top + r * cell
            draw.rectangle([(x0, y0), (x0 + cell, y0 + cell)],
                           outline='black', width=6)
            draw.text((x0 + cell // 2, y0 + cell // 2),
                      str(grid[r][c]), anchor='mm',
                      fill='black', font=digit_font)

    # START / FINISH labels
    draw.text((grid_left + cell // 2, grid_top - 50),
              'START', anchor='mb', fill='black', font=sf_font)
    draw.text((grid_left + grid_w - cell // 2,
               grid_top + grid_h + 50),
              'FINISH', anchor='mt', fill='black', font=sf_font)

    return img


def generate_path_sums_image(difficulty: str, seed: int, title: str,
                             canvas_size=(2625, 3375), return_solution=False):
    rows, cols, vmax = DIFFICULTY_PRESETS.get(difficulty,
                                              DIFFICULTY_PRESETS['medium'])
    grid, target, path = _make_puzzle(rows, cols, vmax, seed)
    img = render_path_sums(canvas_size, title, grid, target)
    if return_solution:
        return img, {'type': 'pathsum',
                     'data': {'path': path, 'target': target, 'grid': grid}}
    return img
