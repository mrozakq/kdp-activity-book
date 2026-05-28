"""
Magic-square puzzles for KDP Activity Book.

3x3 magic square: every row, column and diagonal sums to the same value.
We start from a known 3x3 magic square (Lo Shu), shuffle by symmetric ops,
optionally scale to a larger range, then remove cells so the kid fills them in.

Difficulty:
  easy   = remove 1-2 cells (sum given, 7-8 filled)
  medium = remove 3-4 cells (sum given)
  hard   = remove 4-5 cells (sum given), use range 1..9 + offset
"""
import random

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font
from .layout import compute_activity_box, title_position, instruction_position


# Lo Shu magic square (1..9, magic sum 15)
LO_SHU = [
    [2, 7, 6],
    [9, 5, 1],
    [4, 3, 8],
]


DIFFICULTY_PRESETS = {
    'easy':   {'holes': 2, 'offset': 0},   # numbers 1..9, sum=15
    'medium': {'holes': 3, 'offset': 0},
    'hard':   {'holes': 5, 'offset': 10},  # numbers 11..19, sum=45
}


def _symmetries(square):
    """All 8 dihedral symmetries of a 3x3 grid — each is still a magic square."""
    s = [row[:] for row in square]

    def rot90(g):
        return [[g[2 - j][i] for j in range(3)] for i in range(3)]

    def flip(g):
        return [row[::-1] for row in g]

    out = []
    cur = s
    for _ in range(4):
        out.append(cur)
        out.append(flip(cur))
        cur = rot90(cur)
    return out


def _make_puzzle(seed: int, holes: int, offset: int = 0):
    rng = random.Random(seed)
    syms = _symmetries(LO_SHU)
    # Pick the symmetry deterministically from the seed so that consecutive
    # puzzles in a volume (seeds differ by 1) get 8 *distinct* orientations —
    # consecutive `seed % 8` values cycle through all 8, guaranteeing the first
    # 8 magic squares in a volume never share a solution. We still call
    # rng.choice() to keep the RNG stream identical, so hole positions (the
    # next rng consumer) are byte-for-byte unchanged vs. before this fix.
    rng.choice(syms)               # preserve RNG consumption (do not remove)
    base = syms[seed % 8]
    full = [[v + offset for v in row] for row in base]
    magic_sum = sum(full[0])

    # Remove `holes` cells uniformly at random
    positions = [(r, c) for r in range(3) for c in range(3)]
    rng.shuffle(positions)
    puzzle = [row[:] for row in full]
    for (r, c) in positions[:holes]:
        puzzle[r][c] = 0
    return puzzle, full, magic_sum


def render_magic_square(puzzle, magic_sum: int,
                        canvas_size=(2625, 3375), title='Magic Square'):
    cw, ch = canvas_size

    x1, y1, x2, y2 = compute_activity_box(canvas_size, has_instruction=True)
    avail_w = x2 - x1
    avail_h = y2 - y1

    cell = int(min(avail_w / 3, avail_h / 3))
    grid_size = cell * 3
    grid_left = (cw - grid_size) // 2
    grid_top  = y1 + (avail_h - grid_size) // 2

    img = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    title_font = get_title_font(130)
    hint_font  = get_body_font(80)
    digit_font = get_body_font(int(cell * 0.63))

    tx, ty = title_position(canvas_size)
    ix, iy = instruction_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black', font=title_font)
    draw.text((ix, iy), f'Each row, column and diagonal = {magic_sum}',
              anchor='mt', fill='black', font=hint_font)

    # Draw grid
    lw = 8
    for k in range(4):
        x = grid_left + k * cell
        y = grid_top + k * cell
        draw.line([(x, grid_top), (x, grid_top + grid_size)], fill='black', width=lw)
        draw.line([(grid_left, y), (grid_left + grid_size, y)], fill='black', width=lw)

    for r in range(3):
        for c in range(3):
            v = puzzle[r][c]
            if v == 0:
                continue
            cx = grid_left + c * cell + cell // 2
            cy = grid_top  + r * cell + cell // 2
            draw.text((cx, cy), str(v), anchor='mm',
                      fill='black', font=digit_font)

    return img


def generate_magic_square_image(difficulty: str, seed: int, title: str,
                                canvas_size=(2625, 3375), return_solution=False):
    cfg = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS['medium'])
    puzzle, full, magic_sum = _make_puzzle(seed, cfg['holes'], cfg['offset'])
    img = render_magic_square(puzzle, magic_sum,
                              canvas_size=canvas_size, title=title)
    if return_solution:
        return img, {'type': 'magic',
                     'data': {'full': full, 'magic_sum': magic_sum}}
    return img
