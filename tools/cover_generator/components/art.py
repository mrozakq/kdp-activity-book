"""
Procedural art generator — creates floral/mandala backgrounds and decorative
overlays for the cover without any external AI API calls.
"""

import math
import random
from PIL import Image, ImageDraw, ImageFilter


# Palettes. Each gets a 'category' field: 'adult' (mindfulness pastels) or 'kids'
# (bright primaries).  Kids palettes also expose contrast-rich title/accent colours.
PALETTES = {
    # ── ADULT (mindfulness) ────────────────────────────────────────────
    "lavender": {
        "category":  "adult",
        "bg_top":    (230, 210, 245),
        "bg_bottom": (200, 175, 230),
        "petal_a":   (255, 200, 220),
        "petal_b":   (180, 150, 215),
        "accent":    (255, 230, 240),
        "spine":     (150, 100, 185),
        "text":      (80,  40,  100),
        "text_light":(255, 245, 255),
    },
    "sage": {
        "category":  "adult",
        "bg_top":    (210, 235, 215),
        "bg_bottom": (170, 210, 185),
        "petal_a":   (255, 220, 190),
        "petal_b":   (140, 190, 155),
        "accent":    (245, 255, 240),
        "spine":     (100, 155, 115),
        "text":      (40,  80,  55),
        "text_light":(245, 255, 245),
    },
    "peach": {
        "category":  "adult",
        "bg_top":    (255, 230, 210),
        "bg_bottom": (245, 195, 170),
        "petal_a":   (255, 200, 180),
        "petal_b":   (230, 160, 130),
        "accent":    (255, 245, 230),
        "spine":     (200, 120,  90),
        "text":      (100,  50,  30),
        "text_light":(255, 248, 240),
    },
    # ── KIDS (bright, preschool-friendly) ──────────────────────────────
    "rainbow_pop": {
        "category":  "kids",
        "bg_top":    (135, 220, 245),
        "bg_bottom": (255, 240, 130),
        "petal_a":   (255,  90,  90),
        "petal_b":   ( 60, 180, 245),
        "accent":    (255, 215,  60),
        "spine":     (255, 130,  40),
        "text":      ( 20,  35,  90),
        "text_light":(255, 250, 240),
    },
    "city_bright": {
        "category":  "kids",
        "bg_top":    (130, 200, 250),   # sky blue
        "bg_bottom": (255, 230, 140),   # warm yellow
        "petal_a":   (255,  90,  85),   # bright red
        "petal_b":   ( 70, 175, 110),   # green
        "accent":    (255, 215,  85),   # sun yellow
        "spine":     (235,  70,  65),   # bright red spine
        "text":      ( 20,  35,  90),   # dark navy
        "text_light":(255, 250, 240),
    },
    "space_blue": {
        "category":  "kids",
        "bg_top":    ( 18,  30,  85),
        "bg_bottom": ( 65,  45, 140),
        "petal_a":   (255, 235,  80),   # neon yellow stars
        "petal_b":   (110, 200, 255),
        "accent":    (255, 255, 255),
        "spine":     (255, 200,  60),
        "text":      (255, 250, 240),
        "text_light":(255, 250, 240),
    },
    "jungle_green": {
        "category":  "kids",
        "bg_top":    (155, 235, 175),
        "bg_bottom": (120, 200, 245),
        "petal_a":   (255, 165,  70),   # orange
        "petal_b":   ( 60, 165,  85),   # leaf green
        "accent":    (255, 245, 200),
        "spine":     (140,  85,  45),   # brown bark
        "text":      ( 30,  60,  35),
        "text_light":(255, 250, 240),
    },
    "unicorn_pink": {
        "category":  "kids",
        "bg_top":    (255, 220, 240),
        "bg_bottom": (220, 200, 255),
        "petal_a":   (255, 110, 195),   # fuchsia
        "petal_b":   (175, 235, 220),   # mint
        "accent":    (255, 220, 120),   # gold
        "spine":     (200,  90, 170),
        "text":      ( 80,  30,  85),
        "text_light":(255, 250, 240),
    },
}


def palettes_by_category(category: str) -> list:
    """Return ordered list of palette names with the given category."""
    return [name for name, p in PALETTES.items() if p.get("category") == category]


# Shared contrast helper — used by front_cover (title/subtitle/author) and
# back_cover (panel header). A palette 'text' colour designed for a dark
# background (high luminance, e.g. space_blue's near-white) would be unreadable
# on a light/white surface, so swap in a dark navy fallback in that case.
_LIGHT_TEXT_THRESHOLD = 140        # luminance (0-255) above which 'text' is "light"
_DARK_TEXT_FALLBACK = (30, 40, 70)


def _luminance601(rgb) -> float:
    """Perceived luminance (Rec. 601), 0-255 scale."""
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def text_on_light(palette_or_rgb) -> tuple:
    """Return a text colour guaranteed readable on a LIGHT/white surface.

    Accepts a palette dict (uses its 'text') or an RGB tuple. Returns a dark
    navy fallback when the colour is light, otherwise the colour unchanged.
    """
    col = palette_or_rgb["text"] if isinstance(palette_or_rgb, dict) else palette_or_rgb
    if _luminance601(col) > _LIGHT_TEXT_THRESHOLD:
        return _DARK_TEXT_FALLBACK
    return tuple(col)


def _gradient_bg(size: tuple, top: tuple, bottom: tuple) -> Image.Image:
    """Vertical linear gradient."""
    w, h = size
    im = Image.new("RGB", size)
    px = im.load()
    for y in range(h):
        t = y / (h - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return im


def _draw_petal(draw: ImageDraw.ImageDraw, cx: float, cy: float,
                length: float, angle_deg: float, color: tuple, width: int = 3):
    """Draw a single elongated oval petal."""
    a = math.radians(angle_deg)
    # Petal: ellipse rotated around cx,cy
    n = 24
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        ex = (length * 0.5) * math.cos(t)
        ey = (length * 0.18) * math.sin(t)
        rx = ex * math.cos(a) - ey * math.sin(a) + cx
        ry = ex * math.sin(a) + ey * math.cos(a) + cy
        pts.append((rx, ry))
    draw.polygon(pts, fill=color + (180,))
    draw.line(pts + [pts[0]], fill=color + (220,), width=max(1, width))


def _draw_flower(draw: ImageDraw.ImageDraw, cx: float, cy: float,
                 radius: float, petals: int,
                 petal_color: tuple, center_color: tuple,
                 layer: int = 1):
    """Multi-layer decorative flower."""
    for layer_i in range(layer, 0, -1):
        r = radius * (layer_i / layer)
        petal_len = r * 1.8
        for k in range(petals):
            angle = 360 / petals * k + (layer_i * 15)
            a = math.radians(angle)
            pcx = cx + r * 0.55 * math.cos(a)
            pcy = cy + r * 0.55 * math.sin(a)
            _draw_petal(draw, pcx, pcy, petal_len, angle, petal_color, width=2)

    # Center circle
    cr = radius * 0.22
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                 fill=center_color + (230,), outline=center_color + (255,), width=2)
    # Center dot
    dr = cr * 0.45
    draw.ellipse([cx - dr, cy - dr, cx + dr, cy + dr],
                 fill=(255, 255, 255, 200))


def _draw_mandala_ring(draw: ImageDraw.ImageDraw, cx: float, cy: float,
                       r_in: float, r_out: float, segments: int,
                       color: tuple):
    """Ring of curved petal arcs — simplified mandala motif."""
    for i in range(segments):
        a1 = 2 * math.pi * i / segments
        a2 = 2 * math.pi * (i + 0.45) / segments
        # Arc approximated by polygon
        pts = []
        steps = 12
        for s in range(steps + 1):
            a = a1 + (a2 - a1) * s / steps
            pts.append((cx + r_out * math.cos(a), cy + r_out * math.sin(a)))
        for s in range(steps, -1, -1):
            a = a1 + (a2 - a1) * s / steps
            pts.append((cx + r_in * math.cos(a), cy + r_in * math.sin(a)))
        draw.polygon(pts, fill=color + (160,), outline=color + (200,))


def _draw_small_flowers(draw: ImageDraw.ImageDraw, w: int, h: int,
                        palette: dict, count: int, rng: random.Random):
    """Scatter small accent flowers across the canvas."""
    for _ in range(count):
        x = rng.randint(0, w)
        y = rng.randint(0, h)
        r = rng.randint(20, 55)
        petals = rng.choice([5, 6, 8])
        col = rng.choice([palette["petal_a"], palette["petal_b"]])
        _draw_flower(draw, x, y, r, petals, col, palette["accent"], layer=1)


def generate_background(size: tuple, palette_name: str = "lavender",
                        seed: int = 42) -> Image.Image:
    """
    Generate a full-color floral/mandala background at `size` pixels.
    Returns RGB Image.
    """
    rng = random.Random(seed)
    palette = PALETTES.get(palette_name, PALETTES["lavender"])
    w, h = size

    # 1. Gradient base
    base = _gradient_bg(size, palette["bg_top"], palette["bg_bottom"])
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 2. Large background mandalas (3 big ones across the canvas)
    big_positions = [
        (w * 0.15, h * 0.5),
        (w * 0.5,  h * 0.5),
        (w * 0.85, h * 0.5),
    ]
    for bx, by in big_positions:
        big_r = min(w, h) * 0.32
        for ring_idx, (r_in_f, r_out_f, segs, alpha_adjust) in enumerate([
            (0.80, 1.00, 24, 140),
            (0.60, 0.78, 18, 130),
            (0.40, 0.58, 14, 120),
            (0.22, 0.38, 10, 110),
        ]):
            col = palette["petal_b"] if ring_idx % 2 == 0 else palette["petal_a"]
            _draw_mandala_ring(draw, bx, by,
                               big_r * r_in_f, big_r * r_out_f, segs, col)

        # Center flower
        _draw_flower(draw, bx, by, big_r * 0.20, 8,
                     palette["petal_a"], palette["accent"], layer=2)

    # 3. Medium decorative flowers scattered
    med_positions = [
        (w * 0.08,  h * 0.12),
        (w * 0.92,  h * 0.12),
        (w * 0.08,  h * 0.88),
        (w * 0.92,  h * 0.88),
        (w * 0.3,   h * 0.15),
        (w * 0.7,   h * 0.15),
        (w * 0.3,   h * 0.85),
        (w * 0.7,   h * 0.85),
    ]
    for mx, my in med_positions:
        r = min(w, h) * 0.08
        petals = rng.choice([6, 8])
        col = rng.choice([palette["petal_a"], palette["petal_b"]])
        _draw_flower(draw, mx, my, r, petals, col, palette["accent"], layer=2)

    # 4. Small scattered flowers
    _draw_small_flowers(draw, w, h, palette, count=40, rng=rng)

    # 5. Dot grid accent
    dot_spacing = max(60, w // 60)
    for gx in range(0, w, dot_spacing):
        for gy in range(0, h, dot_spacing):
            jx = rng.randint(-dot_spacing // 4, dot_spacing // 4)
            jy = rng.randint(-dot_spacing // 4, dot_spacing // 4)
            r = rng.randint(2, 5)
            col = rng.choice([palette["petal_a"], palette["accent"]])
            draw.ellipse([gx + jx - r, gy + jy - r,
                          gx + jx + r, gy + jy + r],
                         fill=col + (120,))

    # Composite
    base = base.convert("RGBA")
    base.alpha_composite(overlay)
    result = base.convert("RGB")

    # Soft blur to smooth out harsh edges
    result = result.filter(ImageFilter.GaussianBlur(radius=1.5))
    return result


def generate_spine_bg(size: tuple, palette_name: str = "lavender") -> Image.Image:
    """Solid spine with subtle gradient — darker accent color."""
    palette = PALETTES.get(palette_name, PALETTES["lavender"])
    w, h = size
    col = palette["spine"]
    col2 = tuple(max(0, c - 25) for c in col)
    return _gradient_bg(size, col, col2)
