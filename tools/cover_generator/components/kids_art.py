"""
Kids-themed procedural backgrounds for the cover generator.

generate_kids_background(size, theme, palette, seed) returns a full-bleed RGB image
ready to drop in as the cover background. Each theme is built from simple PIL
primitives (no external assets). A subtle radial vignette toward the centre is
applied so the title pops.

Themes:
  city          buildings + cars + clouds + sun (for "town" books — the priority theme)
  space         stars + planets + moon
  jungle        trees + leaves + sun
  ocean         waves + bubbles + sun
  generic_stars stars + sparkles on gradient (fallback / decorative)
"""
import math
import random
from PIL import Image, ImageDraw, ImageFilter

from components.art import PALETTES, _gradient_bg


# ---- helpers ---------------------------------------------------------

def _vignette(img: Image.Image, strength: float = 0.35) -> Image.Image:
    """Subtle radial vignette darkening edges (or lightening centre).
    We *brighten* the centre by overlaying a soft white radial — that way the title
    area gets a slight halo to pop against the background. strength in 0..1."""
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    cx, cy = w // 2, int(h * 0.42)         # halo a bit above geometric centre
    max_r = max(w, h) * 0.55
    steps = 14
    for i in range(steps, 0, -1):
        r = max_r * i / steps
        alpha = int(255 * (1 - i / steps) * strength)
        md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=max(w, h) * 0.05))
    white = Image.new("RGB", (w, h), (255, 255, 255))
    return Image.composite(white, img, mask)


def _star(draw, cx, cy, r, color, points=5):
    """N-point star polygon centered at (cx, cy) with outer radius r."""
    inner = r * 0.42
    pts = []
    for i in range(2 * points):
        ang = -math.pi / 2 + i * math.pi / points
        rr = r if i % 2 == 0 else inner
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=color)


def _scalloped_cloud(draw, cx, cy, w, h, color):
    """Cloud silhouette: 3 overlapping ellipses for puffy look."""
    rx = w / 2
    ry = h / 2
    # Center puff (biggest)
    draw.ellipse([cx - rx * 0.7, cy - ry, cx + rx * 0.7, cy + ry], fill=color)
    # Side puffs
    draw.ellipse([cx - rx, cy - ry * 0.6, cx - rx * 0.3, cy + ry * 0.6], fill=color)
    draw.ellipse([cx + rx * 0.3, cy - ry * 0.6, cx + rx, cy + ry * 0.6], fill=color)
    # Small top bump
    draw.ellipse([cx - rx * 0.2, cy - ry * 1.3, cx + rx * 0.3, cy - ry * 0.3], fill=color)


def _sun_with_rays(draw, cx, cy, r, body_color, ray_color, rays=8):
    """Circle with triangular rays around it."""
    # Rays
    ray_len = r * 0.55
    for i in range(rays):
        ang = i * 2 * math.pi / rays
        x0 = cx + (r + 8) * math.cos(ang)
        y0 = cy + (r + 8) * math.sin(ang)
        x1 = cx + (r + ray_len) * math.cos(ang)
        y1 = cy + (r + ray_len) * math.sin(ang)
        # Triangle ray: x0,y0 = base center, x1,y1 = tip
        perp = ang + math.pi / 2
        bx0 = x0 + math.cos(perp) * (r * 0.18)
        by0 = y0 + math.sin(perp) * (r * 0.18)
        bx1 = x0 - math.cos(perp) * (r * 0.18)
        by1 = y0 - math.sin(perp) * (r * 0.18)
        draw.polygon([(bx0, by0), (x1, y1), (bx1, by1)], fill=ray_color)
    # Body
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=body_color,
                 outline=ray_color, width=max(2, int(r * 0.10)))


def _car(draw, x, y, w, h, body_color, wheel_color, window_color):
    """Simple side-view car: rounded rectangle body + 2 circle wheels + window."""
    # Body — rounded rectangle
    draw.rounded_rectangle([x, y + h * 0.30, x + w, y + h * 0.85],
                           radius=int(h * 0.15), fill=body_color)
    # Cabin/window — trapezoid on top
    cabin = [
        (x + w * 0.20, y + h * 0.30),
        (x + w * 0.32, y),
        (x + w * 0.70, y),
        (x + w * 0.85, y + h * 0.30),
    ]
    draw.polygon(cabin, fill=body_color)
    # Window pane
    win = [
        (x + w * 0.30, y + h * 0.10),
        (x + w * 0.36, y + h * 0.04),
        (x + w * 0.66, y + h * 0.04),
        (x + w * 0.74, y + h * 0.10),
        (x + w * 0.74, y + h * 0.28),
        (x + w * 0.30, y + h * 0.28),
    ]
    draw.polygon(win, fill=window_color)
    # 2 wheels
    wr = h * 0.22
    wy = y + h * 0.85 - wr * 0.40
    draw.ellipse([x + w * 0.18 - wr, wy - wr,
                  x + w * 0.18 + wr, wy + wr], fill=wheel_color)
    draw.ellipse([x + w * 0.78 - wr, wy - wr,
                  x + w * 0.78 + wr, wy + wr], fill=wheel_color)


def _building(draw, x, y, w, h, body_color, roof_color, window_color):
    """Rectangle building + triangle roof + 2-3 windows."""
    body_top = y + h * 0.20
    draw.rectangle([x, body_top, x + w, y + h], fill=body_color)
    # Roof — triangle
    draw.polygon([(x - w * 0.05, body_top),
                  (x + w * 0.5, y),
                  (x + w * 1.05, body_top)], fill=roof_color)
    # Windows — 2 cols, 1-2 rows depending on h
    win_w = w * 0.22
    win_h = h * 0.16
    rows = 2 if h > 200 else 1
    for r in range(rows):
        ry = body_top + h * (0.18 + r * 0.30)
        draw.rectangle([x + w * 0.18, ry, x + w * 0.18 + win_w, ry + win_h],
                       fill=window_color)
        draw.rectangle([x + w * 0.60, ry, x + w * 0.60 + win_w, ry + win_h],
                       fill=window_color)


# ---- theme generators ------------------------------------------------

def _city(canvas, palette, rng):
    """Buildings along the bottom 30%, cars on a road, clouds + sun on top."""
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)

    # Ground band (sidewalk) — soft accent strip
    ground_y = int(h * 0.78)
    draw.rectangle([0, ground_y, w, h],
                   fill=tuple(min(255, c + 25) for c in palette["bg_bottom"]))

    # Sun upper-right
    sun_r = int(min(w, h) * 0.07)
    _sun_with_rays(draw, int(w * 0.88), int(h * 0.14),
                   sun_r, body_color=palette["accent"],
                   ray_color=palette["petal_a"], rays=8)

    # 3 clouds upper portion
    for cx_frac, cy_frac, scale in [(0.18, 0.10, 1.0),
                                     (0.45, 0.18, 0.8),
                                     (0.70, 0.08, 0.9)]:
        _scalloped_cloud(draw,
                         int(w * cx_frac), int(h * cy_frac),
                         int(w * 0.16 * scale), int(h * 0.05 * scale),
                         color=(255, 255, 255))

    # Buildings — 6 along the bottom band
    bld_y = int(h * 0.50)
    bld_h_max = ground_y - bld_y
    n_bld = 6
    bld_w = w // n_bld
    roof_palette = [palette["petal_a"], palette["petal_b"], palette["spine"]]
    body_palette = [
        (245, 235, 210),    # cream
        palette["accent"],
        (220, 230, 245),    # pale blue
        (255, 220, 200),    # peach
    ]
    for i in range(n_bld):
        bx = i * bld_w + int(bld_w * 0.10)
        bh_frac = rng.uniform(0.55, 1.0)
        bh = int(bld_h_max * bh_frac)
        by = ground_y - bh
        _building(draw, bx, by,
                  int(bld_w * 0.80), bh,
                  body_color=rng.choice(body_palette),
                  roof_color=rng.choice(roof_palette),
                  window_color=palette["petal_b"])

    # 2 cars on the road
    car_h = int(h * 0.05)
    car_w = int(car_h * 2.2)
    car_y = ground_y - int(car_h * 0.25)
    _car(draw, int(w * 0.18), car_y, car_w, car_h,
         body_color=palette["spine"], wheel_color=(40, 40, 40),
         window_color=palette["text_light"])
    _car(draw, int(w * 0.62), car_y, car_w, car_h,
         body_color=palette["petal_b"], wheel_color=(40, 40, 40),
         window_color=palette["text_light"])

    # Small sparkles scattered in the sky
    for _ in range(20):
        sx = rng.randint(0, w)
        sy = rng.randint(0, int(h * 0.40))
        sr = rng.randint(6, 14)
        _star(draw, sx, sy, sr, palette["accent"], points=4)


def _space(canvas, palette, rng):
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    # Star field
    for _ in range(120):
        sx = rng.randint(0, w)
        sy = rng.randint(0, int(h * 0.85))
        sr = rng.randint(4, 14)
        _star(draw, sx, sy, sr, palette["petal_a"], points=4)
    # Planet upper-right
    pr = int(min(w, h) * 0.10)
    draw.ellipse([w * 0.82 - pr, h * 0.16 - pr,
                  w * 0.82 + pr, h * 0.16 + pr],
                 fill=palette["petal_b"], outline=palette["accent"], width=8)
    # Ring around planet
    draw.ellipse([w * 0.82 - pr * 1.6, h * 0.16 - pr * 0.35,
                  w * 0.82 + pr * 1.6, h * 0.16 + pr * 0.35],
                 outline=palette["accent"], width=6)
    # Crescent moon left
    mr = int(min(w, h) * 0.07)
    draw.ellipse([w * 0.10 - mr, h * 0.20 - mr,
                  w * 0.10 + mr, h * 0.20 + mr],
                 fill=palette["accent"])
    draw.ellipse([w * 0.10 - mr * 0.6, h * 0.20 - mr,
                  w * 0.10 + mr * 1.0, h * 0.20 + mr],
                 fill=palette["bg_top"])


def _jungle(canvas, palette, rng):
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    # Sun
    _sun_with_rays(draw, int(w * 0.88), int(h * 0.14),
                   int(min(w, h) * 0.07), body_color=palette["accent"],
                   ray_color=palette["petal_a"], rays=8)
    # Ground
    draw.rectangle([0, int(h * 0.78), w, h], fill=palette["petal_b"])
    # Trees — triangles for foliage, brown rectangles for trunks
    for cx_frac in [0.10, 0.25, 0.45, 0.65, 0.85]:
        cx = int(w * cx_frac)
        trunk_w = int(w * 0.025)
        trunk_h = int(h * 0.14)
        trunk_top = int(h * 0.78) - trunk_h
        draw.rectangle([cx - trunk_w // 2, trunk_top,
                        cx + trunk_w // 2, trunk_top + trunk_h],
                       fill=palette["spine"])
        # 3 stacked triangles
        for i, frac in enumerate([0.45, 0.32, 0.20]):
            base_y = trunk_top - int(h * 0.02) - i * int(h * 0.06)
            tw = int(w * (0.10 - i * 0.012))
            draw.polygon([(cx - tw, base_y),
                          (cx + tw, base_y),
                          (cx, base_y - int(h * 0.10))],
                         fill=palette["petal_b"])


def _ocean(canvas, palette, rng):
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    # Sun
    _sun_with_rays(draw, int(w * 0.88), int(h * 0.14),
                   int(min(w, h) * 0.07), body_color=palette["accent"],
                   ray_color=palette["petal_a"], rays=8)
    # Wave bands at bottom
    wave_top = int(h * 0.65)
    for i in range(4):
        band_y = wave_top + int(h * 0.075 * i)
        # Wave curve as polygon
        pts = []
        for x in range(0, w + 50, 50):
            yo = int(20 * math.sin(x / 90.0 + i * 0.7))
            pts.append((x, band_y + yo))
        pts.append((w, h))
        pts.append((0, h))
        col = palette["petal_b"] if i % 2 == 0 else palette["spine"]
        draw.polygon(pts, fill=col)
    # Bubbles
    for _ in range(15):
        bx = rng.randint(0, w)
        by = rng.randint(wave_top, h - 20)
        br = rng.randint(8, 24)
        draw.ellipse([bx - br, by - br, bx + br, by + br],
                     outline=palette["text_light"], width=4)


def _generic_stars(canvas, palette, rng):
    w, h = canvas.size
    draw = ImageDraw.Draw(canvas)
    for _ in range(100):
        sx = rng.randint(0, w)
        sy = rng.randint(0, h)
        sr = rng.randint(8, 22)
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                     fill=palette["petal_a"] if rng.random() > 0.5
                     else palette["petal_b"])


_THEMES = {
    "city":          _city,
    "space":         _space,
    "jungle":        _jungle,
    "ocean":         _ocean,
    "generic_stars": _generic_stars,
}


def generate_kids_background(size: tuple, theme: str = "city",
                             palette_name: str = "city_bright",
                             seed: int = 42) -> Image.Image:
    """Build a kid-friendly themed cover background. Returns RGB Image."""
    rng = random.Random(seed)
    palette = PALETTES.get(palette_name, PALETTES["city_bright"])
    canvas = _gradient_bg(size, palette["bg_top"], palette["bg_bottom"])
    fn = _THEMES.get(theme, _city)
    fn(canvas, palette, rng)
    # Subtle vignette / halo behind title
    canvas = _vignette(canvas, strength=0.30)
    return canvas
