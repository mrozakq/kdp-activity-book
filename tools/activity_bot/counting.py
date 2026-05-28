"""
Counting page for KDP Activity Book.

Scatters N simple shapes (stars / hearts / circles / triangles) over the page
with a question at the bottom: "How many X are there?" and a blank answer box.
Difficulty controls the count range.
"""
import math
import random

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font, get_label_font
from .layout import compute_activity_box, title_position, SAFE_MARGIN_PX


# (min_count, max_count)
DIFFICULTY_PRESETS = {
    'easy':   (5, 10),
    'medium': (10, 18),
    'hard':   (18, 30),
}

OBJECT_TYPES = ['star', 'heart', 'circle', 'triangle']
OBJECT_PL = {
    'star':     'stars',
    'heart':    'hearts',
    'circle':   'circles',
    'triangle': 'triangles',
}


def _draw_object(draw, kind, cx, cy, size):
    """Draw a single object centered at (cx, cy) with given size."""
    r = size / 2
    lw = max(4, int(size / 14))
    if kind == 'star':
        pts = []
        for i in range(10):
            angle = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr * math.cos(angle), cy + rr * math.sin(angle)))
        draw.polygon(pts, outline='black', width=lw)
    elif kind == 'heart':
        # Parametric heart, scaled to ~ size
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
        pts = [(cx, cy - h * 2 / 3),
               (cx - r, cy + h / 3),
               (cx + r, cy + h / 3)]
        draw.polygon(pts, outline='black', width=lw)


def _scatter_non_overlapping(rng, n, area, min_dist):
    """Return n (x, y) positions inside `area` (x0,y0,x1,y1), no closer than min_dist."""
    x0, y0, x1, y1 = area
    placed = []
    attempts = 0
    while len(placed) < n and attempts < n * 200:
        attempts += 1
        x = rng.uniform(x0, x1)
        y = rng.uniform(y0, y1)
        if all(math.hypot(x - px, y - py) >= min_dist for (px, py) in placed):
            placed.append((x, y))
    return placed


def render_counting(canvas_size, title, kind, count, seed):
    cw, ch = canvas_size
    rng = random.Random(seed)

    # Reserve generous footer for question + "Answer:" label + answer box.
    # 620 px keeps the box top edge well above the PDF page-number footer
    # (page number is drawn by reportlab at ~31pt = ~129px from page bottom).
    footer = 620
    x1, y1, x2, y2 = compute_activity_box(canvas_size, footer_reserve_px=footer)
    obj_area = (x1, y1, x2, y2)
    area_w = obj_area[2] - obj_area[0]
    area_h = obj_area[3] - obj_area[1]

    obj_size = int(min(area_w, area_h) / max(4, math.sqrt(count) * 1.6))
    min_dist = obj_size * 1.2

    img = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    title_font = get_title_font(130)
    q_font     = get_body_font(115)
    answer_label_font = get_label_font(76)

    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black', font=title_font)

    pad = obj_size // 2 + 10
    inner = (obj_area[0] + pad, obj_area[1] + pad,
             obj_area[2] - pad, obj_area[3] - pad)
    positions = _scatter_non_overlapping(rng, count, inner, min_dist)
    for (x, y) in positions:
        _draw_object(draw, kind, x, y, obj_size)

    # Question, then "Answer:" label, then the empty answer box.
    qy = y2 + 60
    draw.text((cw // 2, qy), f'How many {OBJECT_PL[kind]} are there?',
              anchor='mt', fill='black', font=q_font)

    lbl_y = qy + 160
    draw.text((cw // 2, lbl_y), 'Answer:', anchor='mt',
              fill='black', font=answer_label_font)

    box_w = 360
    box_h = 180
    bx = cw // 2 - box_w // 2
    by = lbl_y + 110
    draw.rectangle([(bx, by), (bx + box_w, by + box_h)],
                   outline='black', width=10)

    return img, len(positions)


def generate_counting_image(difficulty: str, seed: int, title: str,
                            canvas_size=(2625, 3375), return_solution=False):
    lo, hi = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS['medium'])
    rng = random.Random(seed)
    count = rng.randint(lo, hi)
    kind = rng.choice(OBJECT_TYPES)
    img, placed = render_counting(canvas_size, title, kind, count, seed)
    # The drawn count IS the answer — the scatter must have placed them all.
    assert placed == count, (
        f'counting scatter under-filled: wanted {count}, placed {placed}')
    if return_solution:
        return img, {'type': 'counting',
                     'data': {'count': count, 'kind': kind}}
    return img
