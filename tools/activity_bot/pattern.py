"""
Pattern-completion sheet for KDP Activity Book.

Each row shows a short sequence of shapes following a simple rule
(ABAB, AABB, ABC, …) with the last cell empty for the kid to fill in.
6-8 such rows per page.
"""
import math
import random

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_label_font
from .layout import compute_activity_box, title_position


DIFFICULTY_PRESETS = {
    'easy':   {'rows': 6, 'cells': 5, 'patterns': ['AB', 'AAB', 'ABB']},
    'medium': {'rows': 7, 'cells': 6, 'patterns': ['AB', 'ABC', 'AAB', 'ABBC']},
    'hard':   {'rows': 8, 'cells': 7, 'patterns': ['ABC', 'AABB', 'ABBC', 'ABCD']},
}

# Up to 4 distinct shape primitives (A=star, B=heart, C=circle, D=triangle)
SHAPE_LIST = ['star', 'heart', 'circle', 'triangle']


def _draw_object(draw, kind, cx, cy, size):
    r = size / 2
    lw = max(4, int(size / 14))
    if kind == 'star':
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        draw.polygon(pts, outline='black', width=lw)
    elif kind == 'heart':
        pts = []
        for i in range(48):
            t = i / 48 * 2 * math.pi
            x = 16 * math.sin(t) ** 3
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t)
                  - 2 * math.cos(3 * t) - math.cos(4 * t))
            pts.append((cx + x / 17 * r, cy + y / 17 * r))
        draw.polygon(pts, outline='black', width=lw)
    elif kind == 'circle':
        draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)],
                     outline='black', width=lw)
    elif kind == 'triangle':
        h = r * math.sqrt(3)
        pts = [(cx, cy - h * 2 / 3), (cx - r, cy + h / 3), (cx + r, cy + h / 3)]
        draw.polygon(pts, outline='black', width=lw)


def render_pattern(canvas_size, title, difficulty, seed):
    cw, ch = canvas_size
    cfg = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS['medium'])
    rng = random.Random(seed)

    x1, y1, x2, y2 = compute_activity_box(canvas_size)
    avail_w = x2 - x1
    avail_h = y2 - y1

    rows = cfg['rows']
    cells = cfg['cells']
    cell_w = avail_w / cells
    cell_h = avail_h / rows
    cell = min(cell_w, cell_h)
    obj_size = int(cell * 0.6)

    grid_w = cell * cells
    grid_h = cell * rows
    grid_left = (cw - grid_w) // 2
    grid_top = y1 + (avail_h - grid_h) // 2

    img = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    title_font = get_title_font(130)
    q_font = get_label_font(int(cell * 0.69))

    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black', font=title_font)

    answers = []  # correct shape for each row's '?' cell, top-to-bottom
    for r_idx in range(rows):
        pat = rng.choice(cfg['patterns'])  # e.g. 'AAB'
        n_distinct = len(set(pat))
        # Distinct shapes mapped from A..D
        shapes = rng.sample(SHAPE_LIST, n_distinct)
        # Build the sequence by repeating the pattern
        sequence = []
        for i in range(cells):
            ch_letter = pat[i % len(pat)]
            sequence.append(shapes[ord(ch_letter) - ord('A')])
        answers.append(sequence[cells - 1])
        # Last cell: empty (question mark)
        row_y = grid_top + r_idx * cell + cell / 2
        for c_idx in range(cells):
            cx = grid_left + c_idx * cell + cell / 2
            if c_idx == cells - 1:
                # Empty answer box
                box = obj_size
                draw.rectangle([(cx - box / 2, row_y - box / 2),
                                (cx + box / 2, row_y + box / 2)],
                               outline='black', width=6)
                draw.text((cx, row_y), '?', anchor='mm',
                          fill='black', font=q_font)
            else:
                _draw_object(draw, sequence[c_idx], cx, row_y, obj_size)

    return img, answers


def generate_pattern_image(difficulty: str, seed: int, title: str,
                           canvas_size=(2625, 3375), return_solution=False):
    img, answers = render_pattern(canvas_size, title, difficulty, seed)
    if return_solution:
        return img, {'type': 'pattern',
                     'data': {'answers': answers, 'rows': len(answers)}}
    return img
