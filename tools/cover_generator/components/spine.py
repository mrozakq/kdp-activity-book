"""
Spine renderer.

At 48 pages (white paper) the spine is 0.108" = ~32 px at 300 DPI.
KDP safe zone requires 0.0625" margins on each side → usable width ≈ 32 - 19 = 13 px.
13 px is too narrow for any readable text, so we fill with a solid decorative color
and optionally add a tiny centered diamond ornament.
"""

import math
from PIL import Image, ImageDraw
from cover_config import CoverDimensions
from components.art import PALETTES


def render_spine(
    canvas: Image.Image,
    dim: CoverDimensions,
    title: str,
    palette_name: str = "lavender",
) -> Image.Image:
    """
    Render spine onto `canvas`.
    - Fills spine x-zone with solid accent gradient
    - Adds centered diamond ornament if spine ≥ 20 px wide
    - Attempts vertical title text only if spine ≥ 80 px (not possible for 48 pages)
    """
    from components.art import generate_spine_bg

    palette = PALETTES.get(palette_name, PALETTES["lavender"])
    safe  = dim.spine_safe
    x1    = dim.spine_start_px
    x2    = dim.spine_end_px
    spine_w = x2 - x1
    h     = dim.total_h_px

    # Thin spines (< ~0.3" ≈ 90 px @300DPI — i.e. most kids/activity books)
    # must NOT get a solid contrasting strip: a narrow strip in the palette's
    # spine colour (e.g. city_bright red) reads as a stray KDP-template guide
    # line down the cover. Let the full-bleed background flow across the spine
    # seamlessly instead (it already spans the whole canvas).
    THIN_SPINE_PX = 90
    if spine_w < THIN_SPINE_PX:
        return canvas

    # 1. Fill spine with accent color gradient
    spine_strip = generate_spine_bg((spine_w, h), palette_name)
    canvas.paste(spine_strip, (x1, 0))

    # 2. Ornament — only if spine wide enough
    if spine_w >= 14:
        draw = ImageDraw.Draw(canvas, "RGBA")
        cx = (x1 + x2) // 2
        cy = h // 2

        # Small diamond
        d = max(4, spine_w // 3)
        pts = [
            (cx,     cy - d),
            (cx + d, cy    ),
            (cx,     cy + d),
            (cx - d, cy    ),
        ]
        draw.polygon(pts, fill=(255, 255, 255, 180))

        # Vertical line ornaments above and below diamond
        line_col = (255, 255, 255, 120)
        line_w   = max(1, spine_w // 10)
        gap      = d + 6
        draw.line([(cx, safe["y1"]), (cx, cy - gap)],
                  fill=line_col, width=line_w)
        draw.line([(cx, cy + gap),  (cx, safe["y2"])],
                  fill=line_col, width=line_w)

    # 3. If spine is wide enough for text (100+ pages), draw vertical title
    if spine_w >= 80:
        from pathlib import Path
        from PIL import ImageFont
        COLORING_FONTS_DIR = (
            Path(__file__).parent.parent.parent.parent
            / "tools" / "coloring_bot" / "data" / "fonts"
        )
        font_path = COLORING_FONTS_DIR / "Calistoga" / "Calistoga-Regular.ttf"
        font_size = spine_w - 20
        try:
            font = ImageFont.truetype(str(font_path), font_size) if font_path.exists() \
                   else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        # Render text onto a temporary vertical strip, then rotate
        txt_h = h - dim.dpi  # leave 0.5" each end
        txt_img = Image.new("RGBA", (spine_w, txt_h), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        txt_draw.text((spine_w // 2, txt_h // 2), title,
                      font=font, fill=(255, 255, 255, 230), anchor="mm")
        txt_rotated = txt_img.rotate(90, expand=False)
        canvas.alpha_composite(
            txt_rotated,
            (x1, (h - txt_h) // 2),
        )

    return canvas
