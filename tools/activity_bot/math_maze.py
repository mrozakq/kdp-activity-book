"""
Math-maze puzzle for KDP Activity Book.

A rectangular grid (rows × cols) of single- or two-digit numbers.  The kid
walks from the top-left START to the bottom-right FINISH using RIGHT / DOWN
moves but is only allowed to step on cells that satisfy a printed RULE
(e.g. "step only on even numbers").

Generation guarantees one valid path: we plant such a path with rule-matching
numbers, then fill the rest of the grid with non-matching numbers.
"""
import random

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font, get_label_font
from .layout import compute_activity_box, title_position, instruction_position


# (rows, cols, rule_kind, rule_param_choices, value_range)
DIFFICULTY_PRESETS = {
    'easy':   (5, 5,  'even_odd', [],            (1, 9)),
    'medium': (6, 6,  'multiple', [2, 3, 4, 5],  (1, 20)),
    'hard':   (7, 7,  'multiple', [3, 4, 5, 6],  (1, 30)),
}


def _matches(v, kind, param):
    if kind == 'even':
        return v % 2 == 0
    if kind == 'odd':
        return v % 2 == 1
    if kind == 'multiple':
        return v % param == 0
    return False


def _pick_rule(rng, kind, params):
    if kind == 'even_odd':
        return rng.choice(['even', 'odd']), None
    return 'multiple', rng.choice(params)


def _random_path(rows, cols, rng):
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


def _make_puzzle(rows, cols, rule_kind, rule_params, vlo, vhi, seed):
    rng = random.Random(seed)
    rule, param = _pick_rule(rng, rule_kind, rule_params)
    path = set(_random_path(rows, cols, rng))

    matching = [v for v in range(vlo, vhi + 1) if _matches(v, rule, param)]
    non_matching = [v for v in range(vlo, vhi + 1) if not _matches(v, rule, param)]
    if not matching or not non_matching:
        # Edge case — broaden range
        matching = matching or [param or 2]
        non_matching = non_matching or [1]

    grid = [[None] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            if (r, c) in path:
                grid[r][c] = rng.choice(matching)
            else:
                grid[r][c] = rng.choice(non_matching)

    return grid, rule, param


def _rule_text(rule, param):
    if rule == 'even':
        return 'Step only on EVEN numbers'
    if rule == 'odd':
        return 'Step only on ODD numbers'
    if rule == 'multiple':
        return f'Step only on multiples of {param}'
    return ''


def render_math_maze(canvas_size, title, grid, rule, param):
    cw, ch = canvas_size
    rows = len(grid)
    cols = len(grid[0])

    label_reserve = 80
    x1, y1, x2, y2 = compute_activity_box(canvas_size, has_instruction=True,
                                           instruction_lines=1,
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
    digit_font = get_body_font(int(cell * 0.575))
    sf_font    = get_label_font(int(cell * 0.345))

    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black', font=title_font)
    ix, iy = instruction_position(canvas_size)
    draw.text((ix, iy),
              _rule_text(rule, param) + '   (only RIGHT or DOWN moves)',
              anchor='mt', fill='black', font=instr_font)

    for r in range(rows):
        for c in range(cols):
            x0 = grid_left + c * cell
            y0 = grid_top + r * cell
            draw.rectangle([(x0, y0), (x0 + cell, y0 + cell)],
                           outline='black', width=6)
            draw.text((x0 + cell // 2, y0 + cell // 2),
                      str(grid[r][c]), anchor='mm',
                      fill='black', font=digit_font)

    draw.text((grid_left + cell // 2, grid_top - 50),
              'START', anchor='mb', fill='black', font=sf_font)
    draw.text((grid_left + grid_w - cell // 2,
               grid_top + grid_h + 50),
              'FINISH', anchor='mt', fill='black', font=sf_font)

    return img


def generate_math_maze_image(difficulty: str, seed: int, title: str,
                             canvas_size=(2625, 3375)):
    rows, cols, rule_kind, params, (vlo, vhi) = DIFFICULTY_PRESETS.get(
        difficulty, DIFFICULTY_PRESETS['medium'])
    grid, rule, param = _make_puzzle(rows, cols, rule_kind, params,
                                     vlo, vhi, seed)
    return render_math_maze(canvas_size, title, grid, rule, param)
