"""Front cover renderer — title, subtitle, author, decorative elements."""

import math
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from cover_config import CoverDimensions
from components.art import PALETTES

FONTS_DIR = Path(__file__).parent.parent / "assets" / "fonts"
COLORING_FONTS_DIR = (
    Path(__file__).parent.parent.parent.parent / "tools" / "coloring_bot" / "data" / "fonts"
)
ACTIVITY_FONTS_DIR = (
    Path(__file__).parent.parent.parent.parent / "tools" / "activity_bot" / "data" / "fonts"
)

# Adult (mindfulness) font priority
TITLE_FONT_CANDIDATES = [
    "Shrikhand/Shrikhand-Regular.ttf",
    "Passion_One/PassionOne-Black.ttf",
    "Oleo_Script_Swash_Caps/OleoScriptSwashCaps-Bold.ttf",
    "Lobster/Lobster-Regular.ttf",
    "Carter_One/CarterOne-Regular.ttf",
]
SUBTITLE_FONT_CANDIDATES = [
    "Calistoga/Calistoga-Regular.ttf",
    "Courgette/Courgette-Regular.ttf",
    "Pattaya/Pattaya-Regular.ttf",
]
BODY_FONT_CANDIDATES = [
    "Courgette/Courgette-Regular.ttf",
    "Calistoga/Calistoga-Regular.ttf",
    "Pattaya/Pattaya-Regular.ttf",
]

# Kids (preschool) font priority — Fredoka VF first (already downloaded for activity book),
# then existing playful fonts as fallback.
KIDS_TITLE_FONT_CANDIDATES = [
    "Fredoka-VF.ttf",                                # variable font, Bold instance via set_variation
    "Fredoka-Bold.ttf",
    "Bungee/Bungee-Regular.ttf",
    "Lilita_One/LilitaOne-Regular.ttf",
    "Bubblegum_Sans/BubblegumSans-Regular.ttf",
    "Shrikhand/Shrikhand-Regular.ttf",
    "Carter_One/CarterOne-Regular.ttf",
]
KIDS_SUBTITLE_FONT_CANDIDATES = [
    "Andika-Bold.ttf",
    "Andika-Regular.ttf",
    "Quicksand-VF.ttf",
    "Courgette/Courgette-Regular.ttf",
]
KIDS_BODY_FONT_CANDIDATES = [
    "Andika-Regular.ttf",
    "Quicksand-VF.ttf",
    "Courgette/Courgette-Regular.ttf",
]


def _load_font(size: int, candidates: list,
               variation: str | None = None) -> ImageFont.FreeTypeFont:
    """Resolve first font file present and load it.  For variable fonts a
    `variation` instance name (e.g. 'Bold') is applied if requested."""
    for rel in candidates:
        for base in [FONTS_DIR, COLORING_FONTS_DIR, ACTIVITY_FONTS_DIR]:
            p = base / rel
            if p.exists():
                try:
                    font = ImageFont.truetype(str(p), size)
                    if variation:
                        try:
                            font.set_variation_by_name(variation)
                        except Exception:
                            pass
                    return font
                except Exception:
                    continue
    return ImageFont.load_default()


def title_fonts_for_mode(mode: str) -> tuple:
    """(title_candidates, subtitle_candidates, body_candidates, title_variation)"""
    if mode == "kids":
        return (KIDS_TITLE_FONT_CANDIDATES,
                KIDS_SUBTITLE_FONT_CANDIDATES,
                KIDS_BODY_FONT_CANDIDATES,
                "Bold")
    return (TITLE_FONT_CANDIDATES,
            SUBTITLE_FONT_CANDIDATES,
            BODY_FONT_CANDIDATES,
            None)


def _text_shadow(draw: ImageDraw.ImageDraw, xy: tuple, text: str,
                 font, fill: tuple, shadow_color: tuple = (0, 0, 0, 100),
                 offset: int = 4, anchor: str = "mm"):
    draw.text((xy[0] + offset, xy[1] + offset), text,
              font=font, fill=shadow_color, anchor=anchor)
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def _luminance601(rgb) -> float:
    """Perceived luminance (Rec. 601), 0-255 scale."""
    r, g, b = rgb[0], rgb[1], rgb[2]
    return 0.299 * r + 0.587 * g + 0.114 * b


# Title and subtitle sit on a LIGHT (white) banner. A palette 'text' colour that
# was designed for a dark background (e.g. space_blue's near-white) would be
# unreadable here, so fall back to a dark navy regardless of palette. The choice
# depends on the banner (always light), not on the palette's intended bg.
_BANNER_DARK_FALLBACK = (30, 40, 70)


def _banner_text_color(palette) -> tuple:
    if _luminance601(palette["text"]) > 140:
        return _BANNER_DARK_FALLBACK
    return palette["text"]


def _wrap_text(text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def _draw_corner_flourish(draw: ImageDraw.ImageDraw, cx: float, cy: float,
                          size: float, palette: dict, flip_x: bool = False, flip_y: bool = False):
    """Draw a simple L-shaped vine flourish in a corner."""
    sx = -1 if flip_x else 1
    sy = -1 if flip_y else 1
    col = palette["petal_b"] + (180,)
    # Stem
    draw.line([
        (cx, cy),
        (cx + sx * size * 0.6, cy + sy * size * 0.05),
        (cx + sx * size, cy + sy * size * 0.4),
        (cx + sx * size * 1.05, cy + sy * size),
    ], fill=col, width=max(2, int(size * 0.04)))
    # Small circles along stem
    for t in [0.3, 0.55, 0.8]:
        bx = cx + sx * size * t
        by = cy + sy * size * t * 0.8
        r = max(3, int(size * 0.05))
        draw.ellipse([bx - r, by - r, bx + r, by + r],
                     fill=palette["petal_a"] + (200,))


def _starburst_badge(canvas: Image.Image, cx: int, cy: int, r: int,
                     text: str, fill_color: tuple, text_color: tuple,
                     font, rotate_deg: float = 15):
    """Star-burst badge with centered text — composited onto `canvas`."""
    pad = int(r * 0.45)
    size = (r + pad) * 2
    badge = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    inner_r = r * 0.78
    pts = []
    n_points = 14
    for i in range(2 * n_points):
        ang = -math.pi / 2 + i * math.pi / n_points
        rr = r if i % 2 == 0 else inner_r
        pts.append((size / 2 + rr * math.cos(ang),
                    size / 2 + rr * math.sin(ang)))
    bd.polygon(pts, fill=fill_color)
    shadow = badge.filter(ImageFilter.GaussianBlur(radius=8))
    bd.text((size / 2, size / 2), text, anchor="mm",
            fill=text_color, font=font)
    rotated = badge.rotate(rotate_deg, resample=Image.BICUBIC, expand=True)
    sh = shadow.rotate(rotate_deg, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(sh, (cx - sh.size[0] // 2 + 8,
                                cy - sh.size[1] // 2 + 8))
    canvas.alpha_composite(rotated, (cx - rotated.size[0] // 2,
                                     cy - rotated.size[1] // 2))


def render_front_cover(
    canvas: Image.Image,
    dim: CoverDimensions,
    title: str,
    subtitle: str,
    author: str,
    palette_name: str = "lavender",
    decorative_image: Image.Image = None,
    cover_mode: str = "adult",
    mascot_image: Image.Image = None,
    badge_text: str = "",
) -> Image.Image:
    """
    Draw front cover content onto `canvas` (full-bleed canvas).
    All drawing is clipped to front_safe zone.
    Returns modified canvas.
    """
    palette = PALETTES.get(palette_name, PALETTES["lavender"])
    draw = ImageDraw.Draw(canvas, "RGBA")
    is_kids = (cover_mode == "kids")
    title_cands, sub_cands, body_cands, title_var = title_fonts_for_mode(cover_mode)

    safe = dim.front_safe
    safe_w = safe["x2"] - safe["x1"]
    safe_h = safe["y2"] - safe["y1"]
    cx = (safe["x1"] + safe["x2"]) // 2    # horizontal centre
    cy = (safe["y1"] + safe["y2"]) // 2    # vertical centre

    # ── Decorative chrome (corner vines + double border) — ADULT mode only ──
    if not is_kids:
        flr = safe_w * 0.12
        _draw_corner_flourish(draw, safe["x1"] + flr*0.1, safe["y1"] + flr*0.1, flr, palette)
        _draw_corner_flourish(draw, safe["x2"] - flr*0.1, safe["y1"] + flr*0.1, flr, palette,
                              flip_x=True)
        _draw_corner_flourish(draw, safe["x1"] + flr*0.1, safe["y2"] - flr*0.1, flr, palette,
                              flip_y=True)
        _draw_corner_flourish(draw, safe["x2"] - flr*0.1, safe["y2"] - flr*0.1, flr, palette,
                              flip_x=True, flip_y=True)

        margin = int(safe_w * 0.03)
        bx1, by1 = safe["x1"] + margin, safe["y1"] + margin
        bx2, by2 = safe["x2"] - margin, safe["y2"] - margin
        col_border = palette["petal_b"] + (160,)
        draw.rectangle([bx1, by1, bx2, by2],
                       outline=col_border, width=max(3, int(safe_w * 0.005)))
        inner_off = int(safe_w * 0.012)
        draw.rectangle([bx1 + inner_off, by1 + inner_off,
                        bx2 - inner_off, by2 - inner_off],
                       outline=col_border, width=max(1, int(safe_w * 0.002)))

    # ── Optional decorative/preview image (lower third) ──────────────────────
    if decorative_image:
        deco_h = int(safe_h * 0.32)
        deco_w = int(safe_w * 0.80)
        deco = decorative_image.convert("RGBA").resize((deco_w, deco_h), Image.LANCZOS)
        # Fade edges using a mask
        mask = Image.new("L", (deco_w, deco_h), 0)
        mdraw = ImageDraw.Draw(mask)
        fade = deco_h // 5
        for y in range(deco_h):
            alpha = 200
            if y < fade:
                alpha = int(200 * y / fade)
            elif y > deco_h - fade:
                alpha = int(200 * (deco_h - y) / fade)
            mdraw.line([(0, y), (deco_w, y)], fill=alpha)
        deco.putalpha(mask)
        deco_x = cx - deco_w // 2
        deco_y = safe["y2"] - deco_h - int(safe_h * 0.10)
        canvas.alpha_composite(deco, (deco_x, deco_y))
        draw = ImageDraw.Draw(canvas, "RGBA")  # refresh after composite

    # ── Semi-transparent title banner ────────────────────────────────────────
    title_zone_h = int(safe_h * 0.30)
    title_zone_y1 = safe["y1"] + int(safe_h * 0.06)
    title_zone_y2 = title_zone_y1 + title_zone_h
    banner_col = (255, 255, 255, 90)
    draw.rounded_rectangle(
        [safe["x1"] + int(safe_w * 0.05), title_zone_y1,
         safe["x2"] - int(safe_w * 0.05), title_zone_y2],
        radius=int(safe_w * 0.04),
        fill=banner_col,
    )

    # ── Mascot sticker (kids mode, optional) — placed below title zone ──────
    if is_kids and mascot_image is not None:
        m_h = int(safe_h * 0.30)
        ratio = mascot_image.size[0] / mascot_image.size[1]
        m_w = int(m_h * ratio)
        mascot = mascot_image.convert("RGBA").resize((m_w, m_h), Image.LANCZOS)
        mx = cx - m_w // 2
        my = title_zone_y2 + int(safe_h * 0.18)
        # Drop shadow underneath (offset, blurred)
        shadow = Image.new("RGBA", (m_w + 30, m_h + 30), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.ellipse([10, m_h - 20, m_w + 20, m_h + 30], fill=(0, 0, 0, 110))
        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
        canvas.alpha_composite(shadow, (mx - 15, my))
        canvas.alpha_composite(mascot, (mx, my))
        draw = ImageDraw.Draw(canvas, "RGBA")

    # ── Title ────────────────────────────────────────────────────────────────
    title_font_size = int(safe_w * 0.14)
    title_font = _load_font(title_font_size, title_cands, variation=title_var)
    title_lines = _wrap_text(title, title_font, int(safe_w * 0.88))
    total_title_h = len(title_lines) * title_font_size * 1.15
    title_y_start = title_zone_y1 + (title_zone_h - total_title_h) // 2 + title_font_size // 2

    text_col = _banner_text_color(palette)
    shadow_col = (0, 0, 0, 80)
    for i, line in enumerate(title_lines):
        ty = int(title_y_start + i * title_font_size * 1.15)
        _text_shadow(draw, (cx, ty), line, title_font,
                     fill=text_col, shadow_color=shadow_col, offset=3, anchor="mm")

    # ── Subtitle ─────────────────────────────────────────────────────────────
    sub_font_size = int(safe_w * 0.055)
    sub_font = _load_font(sub_font_size, sub_cands)
    sub_lines = _wrap_text(subtitle, sub_font, int(safe_w * 0.82))
    subtitle_y = title_zone_y2 + int(safe_h * 0.04)

    sub_banner_h = len(sub_lines) * sub_font_size * 1.3 + int(safe_h * 0.025)
    draw.rounded_rectangle(
        [safe["x1"] + int(safe_w * 0.10), subtitle_y - int(sub_font_size * 0.3),
         safe["x2"] - int(safe_w * 0.10), subtitle_y + int(sub_banner_h)],
        radius=int(safe_w * 0.025),
        fill=(255, 255, 255, 70),
    )
    for i, line in enumerate(sub_lines):
        sy = int(subtitle_y + i * sub_font_size * 1.3 + sub_font_size * 0.5)
        _text_shadow(draw, (cx, sy), line, sub_font,
                     fill=text_col, shadow_color=shadow_col, offset=2, anchor="mm")

    # ── Author byline (+ age badge beside it) at the bottom ─────────────────
    author_font_size = int(safe_w * 0.045)
    author_y = safe["y2"] - int(safe_h * 0.045)
    has_author = bool(author and author.strip())

    if has_author and is_kids and badge_text:
        # Badge + author pill as ONE centred group near the bottom.
        author_font = _load_font(author_font_size, body_cands)
        atxt = f"by {author.strip()}"
        ab = author_font.getbbox(atxt)
        atw = ab[2] - ab[0]
        pad_h = int(author_font_size * 0.85)
        pill_w = atw + 2 * pad_h
        pill_h = int(author_font_size * 1.85)

        badge_r = round(0.50 * dim.dpi)            # ~1.0" diameter
        gap = round(0.30 * dim.dpi)

        # Vertically: keep badge bottom ≤ 10.70" from PDF top (≤ 10.75 limit).
        cy = min(author_y, round(10.70 * dim.dpi) - badge_r)

        left_limit = dim.front_trim_start_px + round(0.5 * dim.dpi)   # ≥9.22"
        right_limit = dim.front_trim_end_px - round(0.375 * dim.dpi)   # ≤16.84"

        # Shrink badge if the group can't fit between the limits.
        while badge_r >= round(0.36 * dim.dpi):
            group_w = 2 * badge_r + gap + pill_w
            if group_w <= (right_limit - left_limit):
                break
            badge_r -= round(0.03 * dim.dpi)
        group_w = 2 * badge_r + gap + pill_w
        group_left = cx - group_w // 2
        group_left = max(group_left, left_limit)
        group_left = min(group_left, right_limit - group_w)

        b_cx = group_left + badge_r
        pill_x1 = group_left + 2 * badge_r + gap
        pill_x2 = pill_x1 + pill_w
        pill_y1 = cy - pill_h // 2
        pill_y2 = cy + pill_h // 2

        # Pill drop shadow (consistent soft shadow) + opaque white pill.
        sl = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(sl).rounded_rectangle(
            [pill_x1 + 4, pill_y1 + 8, pill_x2 + 4, pill_y2 + 8],
            radius=pill_h // 2, fill=(0, 0, 0, 70))
        canvas.alpha_composite(sl.filter(ImageFilter.GaussianBlur(7)))
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rounded_rectangle([pill_x1, pill_y1, pill_x2, pill_y2],
                               radius=pill_h // 2, fill=(255, 255, 255, 255))
        draw.text(((pill_x1 + pill_x2) // 2, cy), atxt, font=author_font,
                  fill=palette["text"], anchor="mm")

        # Badge text shrunk to fit inside the star.
        fs = int(badge_r * 0.50)
        badge_font = _load_font(fs, title_cands, variation=title_var)
        while fs > 10:
            bb = badge_font.getbbox(badge_text)
            if (bb[2] - bb[0]) <= badge_r * 1.40 \
                    and (bb[3] - bb[1]) <= badge_r * 0.90:
                break
            fs -= 4
            badge_font = _load_font(fs, title_cands, variation=title_var)
        _starburst_badge(canvas, b_cx, cy, badge_r, badge_text,
                         fill_color=palette["petal_a"] + (255,),
                         text_color=palette["text_light"],
                         font=badge_font, rotate_deg=10)

    elif has_author:
        author_font = _load_font(author_font_size, body_cands)
        box_x1 = safe["x1"] + int(safe_w * 0.20)
        box_x2 = safe["x2"] - int(safe_w * 0.20)
        box_y1 = author_y - int(author_font_size * 0.85)
        box_y2 = author_y + int(author_font_size * 0.65)
        draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2],
                               radius=int(safe_w * 0.02), fill=(255, 255, 255, 80))
        _text_shadow(draw, (cx, author_y), f"by {author.strip()}", author_font,
                     fill=palette["text"], shadow_color=shadow_col, offset=2,
                     anchor="mm")

    elif not is_kids:
        # Adult mode: blank signature box (kids books don't have signed copies)
        box_x1 = safe["x1"] + int(safe_w * 0.20)
        box_x2 = safe["x2"] - int(safe_w * 0.20)
        box_y1 = author_y - int(author_font_size * 0.85)
        box_y2 = author_y + int(author_font_size * 0.65)
        draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2],
                               radius=int(safe_w * 0.02), fill=(255, 255, 255, 220))
        line_y = box_y2 - int((box_y2 - box_y1) * 0.22)
        draw.line([(box_x1 + int(safe_w * 0.06), line_y),
                   (box_x2 - int(safe_w * 0.06), line_y)],
                  fill=palette["text"] + (160,), width=max(2, int(safe_w * 0.003)))

    return canvas
