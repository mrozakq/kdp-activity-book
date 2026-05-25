"""
Procedural coloring-page background generator.
Produces black-line-art on white at any resolution — no external API needed.

5 categories:
  0 — Floral Mandala
  1 — Geometric Mandala
  2 — Botanical / Nature
  3 — Zen Tangle
  4 — Floral Bouquet
"""

import math
import random
from PIL import Image, ImageDraw, ImageFilter

# Line thickness scales with image width — 0.7% ≈ 18px at 2625px → ~1.8mm printed
LINE_W_FACTOR = 0.007


def _lw(w: int, scale: float = 1.0) -> int:
    return max(4, int(w * LINE_W_FACTOR * scale))


# ─────────────────────────────────────────────────────────────────────────────
# Shared drawing primitives
# ─────────────────────────────────────────────────────────────────────────────

def _petal_polygon(cx, cy, length, width_ratio, angle_deg, n=20):
    """Return polygon points for one elongated oval petal."""
    a = math.radians(angle_deg)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        ex = (length / 2) * math.cos(t)
        ey = (length / 2) * width_ratio * math.sin(t)
        rx = ex * math.cos(a) - ey * math.sin(a) + cx
        ry = ex * math.sin(a) + ey * math.cos(a) + cy
        pts.append((rx, ry))
    return pts


def _draw_ring_of_petals(draw, cx, cy, r, n_petals, petal_len,
                          lw, width_ratio=0.28, angle_offset=0):
    for k in range(n_petals):
        angle = 360 / n_petals * k + angle_offset
        a = math.radians(angle)
        pcx = cx + r * math.cos(a)
        pcy = cy + r * math.sin(a)
        pts = _petal_polygon(pcx, pcy, petal_len, width_ratio, angle)
        draw.polygon(pts, fill="white", outline="black")
        draw.line(pts + [pts[0]], fill="black", width=lw)


def _draw_circle_outline(draw, cx, cy, r, lw):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill="white", outline="black", width=lw)


def _draw_arc_segment(draw, cx, cy, r_in, r_out, a1_deg, a2_deg, lw, steps=30):
    """Draw a filled arc-segment (donut slice) with black outline."""
    pts = []
    for i in range(steps + 1):
        a = math.radians(a1_deg + (a2_deg - a1_deg) * i / steps)
        pts.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a)))
    for i in range(steps, -1, -1):
        a = math.radians(a1_deg + (a2_deg - a1_deg) * i / steps)
        pts.append((cx + r_in * math.cos(a), cy + r_in * math.sin(a)))
    draw.polygon(pts, fill="white", outline="black")
    draw.line(pts + [pts[0]], fill="black", width=lw)


# ─────────────────────────────────────────────────────────────────────────────
# Category A — Floral Mandala
# ─────────────────────────────────────────────────────────────────────────────

def gen_floral_mandala(size: tuple, seed: int = 0) -> Image.Image:
    rng = random.Random(seed)
    w, h = size
    im = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(im)
    lw = _lw(w)

    cx, cy = w // 2, h // 2
    max_r = min(w, h) * 0.46

    # Outer decorative border ring
    for r in [max_r * 1.02, max_r * 0.98]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="black", width=lw)

    # Five rings of petals, growing inward
    configs = [
        (max_r * 0.85, 16, max_r * 0.28, 0.22),
        (max_r * 0.65, 14, max_r * 0.24, 0.26),
        (max_r * 0.47, 12, max_r * 0.20, 0.30),
        (max_r * 0.30, 10, max_r * 0.15, 0.32),
        (max_r * 0.16,  8, max_r * 0.10, 0.36),
    ]
    for ri, (r, n, plen, wr) in enumerate(configs):
        offset = rng.uniform(0, 360 / n)
        _draw_ring_of_petals(draw, cx, cy, r, n, plen, lw, wr, offset)
        # Ring separator circle
        draw.ellipse([cx - r * 0.72, cy - r * 0.72,
                      cx + r * 0.72, cy + r * 0.72],
                     outline="black", width=max(2, lw // 2))

    # Center flower
    center_r = max_r * 0.10
    for k in range(8):
        a = math.radians(45 * k)
        pts = _petal_polygon(cx + center_r * 0.6 * math.cos(a),
                              cy + center_r * 0.6 * math.sin(a),
                              center_r * 1.5, 0.38, 45 * k)
        draw.polygon(pts, fill="white", outline="black")
        draw.line(pts + [pts[0]], fill="black", width=lw)
    _draw_circle_outline(draw, cx, cy, center_r * 0.35, lw)

    # Corner accent flowers (4 corners)
    corner_r = min(w, h) * 0.09
    for fx, fy in [(corner_r, corner_r), (w - corner_r, corner_r),
                   (corner_r, h - corner_r), (w - corner_r, h - corner_r)]:
        _draw_ring_of_petals(draw, fx, fy, corner_r * 0.55, 6, corner_r * 1.0, lw, 0.30)
        _draw_circle_outline(draw, fx, fy, corner_r * 0.18, lw)

    im = im.filter(ImageFilter.SMOOTH_MORE)
    return im


# ─────────────────────────────────────────────────────────────────────────────
# Category B — Geometric Mandala
# ─────────────────────────────────────────────────────────────────────────────

def gen_geometric_mandala(size: tuple, seed: int = 0) -> Image.Image:
    rng = random.Random(seed)
    w, h = size
    im = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(im)
    lw = _lw(w)

    cx, cy = w // 2, h // 2
    max_r = min(w, h) * 0.46

    # Outer double circle
    for r in [max_r * 1.00, max_r * 0.96]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="black", width=lw)

    # 5 concentric rings of arc-segments (like kaleidoscope)
    ring_configs = [
        (max_r * 0.95, max_r * 0.78, 24),
        (max_r * 0.76, max_r * 0.60, 18),
        (max_r * 0.58, max_r * 0.44, 14),
        (max_r * 0.42, max_r * 0.28, 10),
        (max_r * 0.26, max_r * 0.14,  8),
    ]
    for r_out, r_in, n_seg in ring_configs:
        seg_angle = 360 / n_seg
        gap = seg_angle * 0.08
        for k in range(n_seg):
            a1 = seg_angle * k + gap / 2 - 90
            a2 = seg_angle * (k + 1) - gap / 2 - 90
            _draw_arc_segment(draw, cx, cy, r_in, r_out, a1, a2, lw)

    # Inner star polygon — 12-pointed
    star_r_out = max_r * 0.13
    star_r_in  = max_r * 0.06
    n_pts = 12
    star_pts = []
    for k in range(n_pts * 2):
        r = star_r_out if k % 2 == 0 else star_r_in
        a = math.radians(360 / (n_pts * 2) * k - 90)
        star_pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(star_pts, fill="white", outline="black")
    draw.line(star_pts + [star_pts[0]], fill="black", width=lw)

    # Center dot
    cr = max_r * 0.04
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                 fill="white", outline="black", width=lw)

    # Triangular web lines in each ring
    for r_out, r_in, n_seg in ring_configs[:3]:
        seg_angle = 360 / n_seg
        mid_r = (r_out + r_in) / 2
        for k in range(n_seg):
            a = math.radians(seg_angle * k - 90)
            a2 = math.radians(seg_angle * (k + 1) - 90)
            # Radial spoke
            draw.line([(cx + r_in * math.cos(a), cy + r_in * math.sin(a)),
                       (cx + r_out * math.cos(a), cy + r_out * math.sin(a))],
                      fill="black", width=max(2, lw // 2))

    # Corner squares
    sq = min(w, h) * 0.07
    for fx, fy in [(sq, sq), (w - sq, sq), (sq, h - sq), (w - sq, h - sq)]:
        draw.rectangle([fx - sq * 0.7, fy - sq * 0.7,
                        fx + sq * 0.7, fy + sq * 0.7],
                       outline="black", width=lw)
        draw.rectangle([fx - sq * 0.4, fy - sq * 0.4,
                        fx + sq * 0.4, fy + sq * 0.4],
                       outline="black", width=max(2, lw // 2))

    return im


# ─────────────────────────────────────────────────────────────────────────────
# Category C — Botanical / Nature
# ─────────────────────────────────────────────────────────────────────────────

def _draw_leaf(draw, x, y, length, angle_deg, lw):
    a = math.radians(angle_deg)
    # Main leaf outline (two curves approximated)
    n = 20
    pts_top, pts_bot = [], []
    for i in range(n + 1):
        t = i / n  # 0..1 along leaf length
        dx = length * t * math.cos(a)
        dy = length * t * math.sin(a)
        # leaf width peaks at 40% along length
        half_w = length * 0.18 * math.sin(math.pi * t) * (1 - 0.3 * t)
        perp_a = a + math.pi / 2
        pts_top.append((x + dx + half_w * math.cos(perp_a),
                        y + dy + half_w * math.sin(perp_a)))
        pts_bot.append((x + dx - half_w * math.cos(perp_a),
                        y + dy - half_w * math.sin(perp_a)))
    pts = pts_top + list(reversed(pts_bot))
    draw.polygon(pts, fill="white", outline="black")
    draw.line(pts + [pts[0]], fill="black", width=lw)
    # Center vein
    tip_x = x + length * math.cos(a)
    tip_y = y + length * math.sin(a)
    draw.line([(x, y), (tip_x, tip_y)], fill="black", width=max(2, lw // 3))


def _draw_spiral(draw, cx, cy, max_r, turns, lw, rng):
    """Draw a simple Archimedean spiral."""
    pts = []
    steps = int(turns * 60)
    for i in range(steps + 1):
        t = i / steps
        r = max_r * t
        a = math.radians(turns * 360 * t)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    if len(pts) > 1:
        draw.line(pts, fill="black", width=lw)


def gen_botanical(size: tuple, seed: int = 0) -> Image.Image:
    rng = random.Random(seed)
    w, h = size
    im = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(im)
    lw = _lw(w)

    leaf_len = w * 0.12
    rows = 9
    cols = 6

    # Grid of leaf clusters
    for row in range(rows):
        for col in range(cols):
            cx = int(w * (col + 0.5) / cols + rng.uniform(-w * 0.02, w * 0.02))
            cy = int(h * (row + 0.5) / rows + rng.uniform(-h * 0.015, h * 0.015))
            n_leaves = rng.choice([3, 4, 5, 6])
            base_angle = rng.uniform(0, 360)
            ll = leaf_len * rng.uniform(0.7, 1.2)
            for k in range(n_leaves):
                angle = base_angle + 360 / n_leaves * k
                _draw_leaf(draw, cx, cy, ll, angle, lw)
            # Berry/seed dot at center
            br = int(lw * 1.5)
            draw.ellipse([cx - br, cy - br, cx + br, cy + br],
                         fill="white", outline="black", width=max(2, lw // 2))

    # Connecting vines (horizontal wavy lines)
    for row in range(1, rows):
        vy = int(h * row / rows)
        pts = []
        amp = h * 0.008
        freq = 12
        for xi in range(0, w + 1, w // 80):
            oy = amp * math.sin(2 * math.pi * freq * xi / w + rng.uniform(0, 6))
            pts.append((xi, vy + oy))
        if len(pts) > 1:
            draw.line(pts, fill="black", width=max(2, lw // 2))

    # Decorative border of leaves
    border_leaves = 18
    border_r_w = w * 0.48
    border_r_h = h * 0.48
    for k in range(border_leaves):
        a = math.radians(360 / border_leaves * k)
        bx = w // 2 + border_r_w * math.cos(a)
        by = h // 2 + border_r_h * math.sin(a)
        _draw_leaf(draw, bx, by, leaf_len * 1.3, math.degrees(a) + 90, lw)

    return im


# ─────────────────────────────────────────────────────────────────────────────
# Category D — Zen Tangle
# ─────────────────────────────────────────────────────────────────────────────

def _fill_section_spirals(draw, x1, y1, x2, y2, lw, rng, density=4):
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    r = min(x2 - x1, y2 - y1) * 0.35
    _draw_spiral_with_draw(draw, cx, cy, r, rng.uniform(2.5, 4.5), lw)


def _draw_spiral_with_draw(draw, cx, cy, max_r, turns, lw):
    pts = []
    steps = int(turns * 55)
    for i in range(steps + 1):
        t = i / steps
        r = max_r * t
        a = math.radians(turns * 360 * t)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    if len(pts) > 1:
        draw.line(pts, fill="black", width=lw)


def _fill_section_waves(draw, x1, y1, x2, y2, lw, rng):
    n_waves = rng.randint(5, 10)
    for i in range(n_waves):
        y = y1 + (y2 - y1) * (i + 0.5) / n_waves
        pts = []
        freq = rng.uniform(2, 5)
        amp = (y2 - y1) / n_waves * 0.38
        phase = rng.uniform(0, 6.28)
        for xi in range(int(x1), int(x2) + 1, max(1, int((x2 - x1) / 40))):
            yv = y + amp * math.sin(2 * math.pi * freq * (xi - x1) / (x2 - x1) + phase)
            pts.append((xi, yv))
        if len(pts) > 1:
            draw.line(pts, fill="black", width=lw)


def _fill_section_scales(draw, x1, y1, x2, y2, lw, rng):
    scale_r = (x2 - x1) * 0.12
    cols = max(2, int((x2 - x1) / (scale_r * 1.5)))
    rows = max(2, int((y2 - y1) / (scale_r * 0.85)))
    for row in range(rows):
        for col in range(cols):
            sx = x1 + (col + (0.5 if row % 2 else 0)) * (x2 - x1) / cols
            sy = y1 + row * (y2 - y1) / rows
            r = scale_r * rng.uniform(0.85, 1.0)
            draw.arc([sx - r, sy - r, sx + r, sy + r],
                     start=180, end=360, fill="black", width=lw)


def _fill_section_diamonds(draw, x1, y1, x2, y2, lw, rng):
    d = (x2 - x1) * 0.14
    cols = max(2, int((x2 - x1) / (d * 1.8)))
    rows = max(2, int((y2 - y1) / (d * 1.8)))
    for row in range(rows):
        for col in range(cols):
            dx = x1 + (col + 0.5) * (x2 - x1) / cols
            dy = y1 + (row + 0.5) * (y2 - y1) / rows
            pts = [(dx, dy - d), (dx + d * 0.65, dy),
                   (dx, dy + d), (dx - d * 0.65, dy)]
            draw.polygon(pts, fill="white", outline="black")
            draw.line(pts + [pts[0]], fill="black", width=lw)


def gen_zentangle(size: tuple, seed: int = 0) -> Image.Image:
    rng = random.Random(seed)
    w, h = size
    im = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(im)
    lw = _lw(w)

    # Divide canvas into irregular sections using a grid with jitter
    grid_cols = 4
    grid_rows = 5
    xs = [0] + sorted([int(w * k / grid_cols + rng.uniform(-w * 0.05, w * 0.05))
                        for k in range(1, grid_cols)]) + [w]
    ys = [0] + sorted([int(h * k / grid_rows + rng.uniform(-h * 0.04, h * 0.04))
                        for k in range(1, grid_rows)]) + [h]

    fillers = [_fill_section_spirals, _fill_section_waves,
               _fill_section_scales, _fill_section_diamonds]

    for ri in range(len(ys) - 1):
        for ci in range(len(xs) - 1):
            x1, x2 = xs[ci], xs[ci + 1]
            y1, y2 = ys[ri], ys[ri + 1]
            filler = rng.choice(fillers)
            filler(draw, x1, y1, x2, y2, lw, rng)
            # Section border
            draw.rectangle([x1, y1, x2, y2], outline="black", width=max(2, lw // 2))

    # Large spirals at corners and center for cohesion
    anchors = [(w * 0.5, h * 0.5)]
    for ax, ay in anchors:
        _draw_spiral_with_draw(draw, ax, ay, min(w, h) * 0.18, 4, lw)

    return im


# ─────────────────────────────────────────────────────────────────────────────
# Category E — Floral Bouquet
# ─────────────────────────────────────────────────────────────────────────────

def _draw_rose(draw, cx, cy, r, n_layers, lw, rng):
    """Multi-layer rose — concentric petal rings."""
    for layer in range(n_layers, 0, -1):
        ring_r = r * (layer / n_layers) * 0.7
        n_petals = 5 + layer
        plen = r * 0.55 * (layer / n_layers + 0.4)
        offset = rng.uniform(0, 360 / n_petals)
        _draw_ring_of_petals(draw, cx, cy, ring_r, n_petals, plen, lw,
                              width_ratio=0.38, angle_offset=offset)
    # Center
    cr = r * 0.10
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                 fill="white", outline="black", width=lw)


def _draw_daisy(draw, cx, cy, r, lw, rng):
    n = rng.choice([10, 12, 14])
    offset = rng.uniform(0, 360 / n)
    _draw_ring_of_petals(draw, cx, cy, r * 0.55, n, r * 1.05, lw,
                          width_ratio=0.25, angle_offset=offset)
    _draw_circle_outline(draw, cx, cy, r * 0.22, lw)
    # Center texture dots
    for _ in range(6):
        a = rng.uniform(0, 6.28)
        dr = rng.uniform(0, r * 0.15)
        _draw_circle_outline(draw, cx + dr * math.cos(a), cy + dr * math.sin(a),
                             r * 0.04, max(2, lw // 2))


def gen_floral_bouquet(size: tuple, seed: int = 0) -> Image.Image:
    rng = random.Random(seed)
    w, h = size
    im = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(im)
    lw = _lw(w)

    # Main bouquet — large central rose
    big_r = min(w, h) * 0.20
    _draw_rose(draw, w // 2, h // 2, big_r, 4, lw, rng)

    # 4 medium flowers arranged around center
    medium_r = big_r * 0.55
    positions_med = [
        (w // 2 - big_r * 1.5, h // 2 - big_r * 0.8),
        (w // 2 + big_r * 1.5, h // 2 - big_r * 0.8),
        (w // 2 - big_r * 1.1, h // 2 + big_r * 1.2),
        (w // 2 + big_r * 1.1, h // 2 + big_r * 1.2),
    ]
    for fx, fy in positions_med:
        if rng.random() > 0.5:
            _draw_rose(draw, fx, fy, medium_r, 3, lw, rng)
        else:
            _draw_daisy(draw, fx, fy, medium_r, lw, rng)

    # Small accent flowers scattered
    small_r = big_r * 0.28
    for _ in range(10):
        fx = rng.randint(int(small_r), w - int(small_r))
        fy = rng.randint(int(small_r), h - int(small_r))
        # avoid center cluster
        if math.hypot(fx - w // 2, fy - h // 2) < big_r * 1.2:
            continue
        _draw_daisy(draw, fx, fy, small_r, lw, rng)

    # Background leaves connecting flowers
    n_leaves = 28
    for _ in range(n_leaves):
        lx = rng.randint(0, w)
        ly = rng.randint(0, h)
        angle = rng.uniform(0, 360)
        ll = w * rng.uniform(0.05, 0.11)
        _draw_leaf(draw, lx, ly, ll, angle, max(2, lw // 2))

    # Decorative border
    margin = int(min(w, h) * 0.03)
    draw.rectangle([margin, margin, w - margin, h - margin],
                   outline="black", width=lw)
    draw.rectangle([margin + lw * 2, margin + lw * 2,
                    w - margin - lw * 2, h - margin - lw * 2],
                   outline="black", width=max(2, lw // 2))

    return im


# Import _draw_leaf needed by gen_floral_bouquet and gen_botanical
# (already defined in botanical section)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

GENERATORS = [
    gen_floral_mandala,
    gen_geometric_mandala,
    gen_botanical,
    gen_zentangle,
    gen_floral_bouquet,
]

CATEGORY_NAMES = [
    "Floral Mandala",
    "Geometric Mandala",
    "Botanical / Nature",
    "Zen Tangle",
    "Floral Bouquet",
]

# Folder layout under data/backgrounds/ — one slug per category index.
CATEGORY_FOLDERS = [
    "floral_mandala",
    "geometric_mandala",
    "botanical",
    "zentangle",
    "floral_bouquet",
]

from pathlib import Path as _Path
_BACKGROUNDS_DIR = _Path(__file__).parent / "data" / "backgrounds"
_IMAGE_EXTS = ("*.png", "*.jpg", "*.jpeg")


def _fit_to_canvas(img: Image.Image, size: tuple) -> Image.Image:
    """Resize `img` to fit inside `size` preserving aspect; pad with white."""
    tw, th = size
    iw, ih = img.size
    scale = min(tw / iw, th / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    resized = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", size, (255, 255, 255, 255))
    canvas.paste(resized, ((tw - nw) // 2, (th - nh) // 2),
                 resized if resized.mode == "RGBA" else None)
    return canvas


def _load_from_folder(category: int, size: tuple, seed: int) -> Image.Image | None:
    """Pick a file from data/backgrounds/<slug>/ deterministically by seed."""
    folder = _BACKGROUNDS_DIR / CATEGORY_FOLDERS[category % 5]
    if not folder.is_dir():
        return None
    files = []
    for pat in _IMAGE_EXTS:
        files.extend(folder.glob(pat))
    if not files:
        return None
    files.sort()
    chosen = files[seed % len(files)]
    return _fit_to_canvas(Image.open(chosen).convert("RGBA"), size)


def generate_background(category: int, size: tuple, seed: int = 0) -> Image.Image:
    """
    Get a coloring-page background.

    Looks first in data/backgrounds/<category_slug>/ for PNG/JPG files and
    picks one deterministically by seed. Falls back to the legacy procedural
    generator if the folder is empty or missing.

    Args:
        category: 0-4  (A=Floral Mandala, B=Geometric, C=Botanical, D=Zen, E=Bouquet)
        size: (width, height) in pixels
        seed: index/seed for deterministic picking
    """
    from_file = _load_from_folder(category, size, seed)
    if from_file is not None:
        return from_file
    return GENERATORS[category % 5](size, seed)


def background_cache(
    categories: list,
    size: tuple,
    per_category: int = 5,
) -> dict:
    """
    Pre-generate backgrounds for all categories.
    Returns dict: {category_index: [PIL.Image, ...]}
    """
    cache = {}
    for cat in categories:
        cache[cat] = [
            GENERATORS[cat](size, seed=cat * 100 + i)
            for i in range(per_category)
        ]
    return cache


def pick_background(cache: dict, category: int, quote_lines: int, design_idx: int) -> Image.Image:
    """
    Pick a background from cache.
    Long quotes (3-4 lines) → simpler patterns (lower seed index).
    Short quotes (1-2 lines) → more intricate (higher seed index).
    """
    options = cache[category]
    n = len(options)
    if quote_lines <= 2:
        # Prefer more intricate (higher index)
        idx = design_idx % n
    else:
        # Prefer simpler (lower half of cache)
        idx = design_idx % max(1, n // 2)
    return options[idx]
