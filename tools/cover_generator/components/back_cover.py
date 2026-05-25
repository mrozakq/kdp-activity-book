"""Back cover renderer — hook line, bullets, barcode reserve area."""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from cover_config import CoverDimensions
from components.art import PALETTES
from components.front_cover import (
    _load_font, _text_shadow, _wrap_text,
    TITLE_FONT_CANDIDATES, SUBTITLE_FONT_CANDIDATES, BODY_FONT_CANDIDATES,
    title_fonts_for_mode,
)


def _starburst_badge(canvas: Image.Image, cx: int, cy: int, r: int,
                     text: str, fill_color: tuple, text_color: tuple,
                     font, rotate_deg: float = 15):
    """Draw a circular star-burst badge (multi-point star) with text inside.
    Rendered to a temp RGBA then rotated and pasted onto canvas."""
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
    # Drop shadow
    shadow = badge.filter(ImageFilter.GaussianBlur(radius=8))
    bd.text((size / 2, size / 2), text,
            anchor="mm", fill=text_color, font=font)
    badge = Image.alpha_composite(
        Image.new("RGBA", (size, size), (0, 0, 0, 0)).filter(ImageFilter.GaussianBlur(1)),
        badge,
    )
    rotated = badge.rotate(rotate_deg, resample=Image.BICUBIC, expand=True)
    # Shadow plate
    sh = shadow.rotate(rotate_deg, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(sh, (cx - sh.size[0] // 2 + 8, cy - sh.size[1] // 2 + 8))
    canvas.alpha_composite(rotated, (cx - rotated.size[0] // 2,
                                     cy - rotated.size[1] // 2))


def _draw_star_marker(draw, cx, cy, r, color):
    """Small 5-point filled star, used as kids bullet marker."""
    pts = []
    inner = r * 0.42
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else inner
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    draw.polygon(pts, fill=color)


def render_back_cover(
    canvas: Image.Image,
    dim: CoverDimensions,
    hook: str,
    bullets: list[str],
    author_bio: str = "",
    tagline: str = "",
    palette_name: str = "lavender",
    cover_mode: str = "adult",
    badge_text: str = "",
    cta_text: str = "",
) -> Image.Image:
    """
    Draw back cover content onto `canvas` (full-bleed canvas).
    Respects back_safe zone and reserves barcode area (WHITE).
    """
    palette = PALETTES.get(palette_name, PALETTES["lavender"])
    draw = ImageDraw.Draw(canvas, "RGBA")
    is_kids = (cover_mode == "kids")
    title_cands, sub_cands, body_cands, title_var = title_fonts_for_mode(cover_mode)

    safe = dim.back_safe
    bz   = dim.barcode_zone
    safe_w = safe["x2"] - safe["x1"]
    safe_h = safe["y2"] - safe["y1"]
    cx = (safe["x1"] + safe["x2"]) // 2

    # ── Decorative border (adult only) ───────────────────────────────────────
    if not is_kids:
        margin = int(safe_w * 0.03)
        col_border = palette["petal_b"] + (140,)
        draw.rectangle(
            [safe["x1"] + margin, safe["y1"] + margin,
             safe["x2"] - margin, safe["y2"] - margin],
            outline=col_border, width=max(3, int(safe_w * 0.005))
        )

    shadow_col = (0, 0, 0, 80)

    # ── Hook line ────────────────────────────────────────────────────────────
    # Hard right-edge limit for ANY back-cover element: 0.125" inside the
    # back-cover trim → x ≤ 8.375" from the PDF left edge (8.5" trim).
    SAFE_RIGHT_PX = round((dim.bleed + dim.trim_w - 0.125) * dim.dpi)

    if is_kids:
        # BIG bold hook inside a rounded ribbon banner in accent/spine color.
        pad = int(safe_w * 0.05)
        rib_x1 = safe["x1"] + pad
        rib_x2 = min(safe["x2"] - pad, SAFE_RIGHT_PX)
        ribbon_inner_w = (rib_x2 - rib_x1) - int(safe_w * 0.06)

        # Hook must fit the ribbon width AND finish above the white panel
        # top (3.5") so the bubble never overlaps the panel.
        HOOK_BOTTOM_MAX = round(3.35 * dim.dpi)
        hook_top = safe["y1"] + int(safe_h * 0.07)
        hook_font_size = int(safe_w * 0.095)
        while hook_font_size > int(safe_w * 0.040):
            hook_font = _load_font(hook_font_size, title_cands,
                                   variation=title_var)
            hook_lines = _wrap_text(hook, hook_font, ribbon_inner_w)
            widest = max((hook_font.getbbox(ln)[2] - hook_font.getbbox(ln)[0])
                         for ln in hook_lines) if hook_lines else 0
            tot_h = len(hook_lines) * hook_font_size * 1.2
            rib_bottom = hook_top + tot_h + hook_font_size * 0.30
            if widest <= ribbon_inner_w and rib_bottom <= HOOK_BOTTOM_MAX:
                break
            hook_font_size -= 4
        hook_font = _load_font(hook_font_size, title_cands,
                               variation=title_var)
        hook_lines = _wrap_text(hook, hook_font, ribbon_inner_w)
        hook_y = hook_top
        hook_total_h = int(len(hook_lines) * hook_font_size * 1.2)

        rib_y1 = hook_y - int(hook_font_size * 0.55)
        rib_y2 = hook_y + hook_total_h + int(hook_font_size * 0.30)
        # Shadow plate
        shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow_layer)
        sd.rounded_rectangle(
            [rib_x1 + 8, rib_y1 + 12, rib_x2 + 8, rib_y2 + 12],
            radius=int(safe_w * 0.04), fill=(0, 0, 0, 80),
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=10))
        canvas.alpha_composite(shadow_layer)
        draw = ImageDraw.Draw(canvas, "RGBA")
        # Ribbon body
        draw.rounded_rectangle(
            [rib_x1, rib_y1, rib_x2, rib_y2],
            radius=int(safe_w * 0.04), fill=palette["spine"] + (255,),
        )
        for i, line in enumerate(hook_lines):
            ty = int(hook_y + i * hook_font_size * 1.2 + hook_font_size * 0.4)
            draw.text((cx, ty), line, anchor="mm",
                      fill=palette["accent"], font=hook_font)
        sep_y = rib_y2 + int(safe_h * 0.035)
    else:
        hook_font_size = int(safe_w * 0.075)
        hook_font = _load_font(hook_font_size, SUBTITLE_FONT_CANDIDATES)
        hook_lines = _wrap_text(hook, hook_font, int(safe_w * 0.85))
        hook_y = safe["y1"] + int(safe_h * 0.08)
        hook_total_h = len(hook_lines) * hook_font_size * 1.3

        hook_banner_pad = int(safe_w * 0.04)
        draw.rounded_rectangle(
            [safe["x1"] + hook_banner_pad,
             hook_y - int(hook_font_size * 0.4),
             safe["x2"] - hook_banner_pad,
             hook_y + int(hook_total_h) + int(hook_font_size * 0.2)],
            radius=int(safe_w * 0.03),
            fill=(255, 255, 255, 80),
        )
        for i, line in enumerate(hook_lines):
            ty = int(hook_y + i * hook_font_size * 1.3 + hook_font_size * 0.4)
            _text_shadow(draw, (cx, ty), line, hook_font,
                         fill=palette["text"], shadow_color=shadow_col,
                         offset=2, anchor="mm")
        sep_y = hook_y + int(hook_total_h) + int(safe_h * 0.04)
        draw.line([(safe["x1"] + int(safe_w * 0.1), sep_y),
                   (safe["x2"] - int(safe_w * 0.1), sep_y)],
                  fill=palette["petal_b"] + (160,),
                  width=max(2, int(safe_h * 0.003)))

    # ── Adult bullet points (kids uses the white marketing panel below) ──────
    if not is_kids:
        bullet_font_size = int(safe_w * 0.054)
        bullet_font = _load_font(bullet_font_size, body_cands)
        bullet_x = safe["x1"] + int(safe_w * 0.08)
        bullet_y = sep_y + int(safe_h * 0.04)
        bullet_col = palette["text"]
        for raw_bullet in bullets:
            bullet = raw_bullet.strip()
            while bullet[:1] in ('★', '•', '-', '*', '·'):
                bullet = bullet[1:].lstrip()
            marker_r = max(8, int(safe_w * 0.022))
            m_cx = bullet_x + marker_r
            m_cy = bullet_y + bullet_font_size // 2
            draw.ellipse([m_cx - marker_r, m_cy - marker_r,
                          m_cx + marker_r, m_cy + marker_r],
                         fill=palette["petal_b"] + (220,))
            text_x = bullet_x + marker_r * 3
            b_lines = _wrap_text(bullet, bullet_font, int(safe_w * 0.78))
            for j, bl in enumerate(b_lines):
                ty = bullet_y + j * int(bullet_font_size * 1.2)
                draw.text((text_x, ty), bl, font=bullet_font, fill=bullet_col)
            bullet_y += len(b_lines) * int(bullet_font_size * 1.2) \
                + int(safe_h * 0.025)

    # ── Kids: solid WHITE marketing panel over the landscape ────────────────
    # Copy on the busy city background is unreadable, so all marketing text
    # lives inside an opaque rounded-white panel; the landscape stays visible
    # above (hook bubble) and below (ground strip) for brand continuity.
    if is_kids:
        def _pin(v):
            return round(v * dim.dpi)

        PX1, PX2 = _pin(0.75), _pin(7.75)        # ≤ 8.375" (clear of spine)
        PY1, PY2 = _pin(3.5),  _pin(8.5)         # bottom ≤ barcode top (9.5")
        RAD = _pin(0.15)
        PAD = _pin(0.4)
        ix1, ix2 = PX1 + PAD, PX2 - PAD
        iy1, iy2 = PY1 + PAD, PY2 - PAD
        inner_w = ix2 - ix1
        inner_h = iy2 - iy1

        header_txt = "What's Inside?"
        panel_bullets = [
            "7 different activity types — never boring",
            "Builds counting & problem-solving skills",
            "Develops fine motor coordination",
            "Includes dedication page — perfect gift",
        ]
        body_txt = (
            "Take your little explorer on a fun adventure through a busy "
            "little town! Packed with mazes, coloring, counting puzzles, "
            "and more — perfect for screen-free quiet time at home, on a "
            "plane, or anywhere learning happens."
        )
        cta_txt = (cta_text or "").strip()
        navy = palette["text"]
        gray = (70, 70, 70)
        star_col = palette["spine"]

        def _pt(pt, s):
            return max(11, int(pt * dim.dpi / 72.0 * s))

        def _layout(s):
            """Return (blocks, total_h) for scale s. blocks describe what to
            draw so a fitting scale can be chosen before rendering."""
            hf = _load_font(_pt(34, s), title_cands, variation=title_var)
            bf = _load_font(_pt(28, s), body_cands)
            df = _load_font(_pt(22, s), body_cands)
            cf = _load_font(_pt(22, s), sub_cands)
            mk = max(6, int(bf.size * 0.30))          # star marker radius
            bullet_indent = mk * 3
            y = 0
            blocks = []
            hh = hf.getbbox("Ay")[3]
            blocks.append(("h", hf, header_txt, 0, y))
            y += int(hh * 1.25) + _pin(0.12)
            for bt in panel_bullets:
                wlines = _wrap_text(bt, bf, inner_w - bullet_indent)
                blocks.append(("b", bf, wlines, bullet_indent, y, mk))
                lh = int(bf.size * 1.28)
                y += len(wlines) * lh + int(bf.size * 0.45)
            y += _pin(0.12)
            for bl in _wrap_text(body_txt, df, inner_w):
                blocks.append(("p", df, bl, 0, y))
                y += int(df.size * 1.4)
            if cta_txt:
                y += _pin(0.14)
                for cl in _wrap_text(cta_txt, cf, inner_w):
                    blocks.append(("c", cf, cl, 0, y))
                    y += int(cf.size * 1.3)
            return blocks, y

        scale = 1.0
        while scale >= 0.45:
            blocks, total_h = _layout(scale)
            if total_h <= inner_h:
                break
            scale -= 0.05

        # Drop shadow + panel
        shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow_layer).rounded_rectangle(
            [PX1 + 6, PY1 + 10, PX2 + 6, PY2 + 10],
            radius=RAD, fill=(0, 0, 0, 70))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=9))
        canvas.alpha_composite(shadow_layer)
        draw = ImageDraw.Draw(canvas, "RGBA")
        draw.rounded_rectangle([PX1, PY1, PX2, PY2], radius=RAD,
                               fill=(255, 255, 255, 255))

        for blk in blocks:
            kind = blk[0]
            if kind == "h":
                _, f, txt, dx, y = blk
                draw.text((ix1, iy1 + y), txt, font=f, fill=navy)
            elif kind == "b":
                _, f, wlines, indent, y, mk = blk
                m_cy = iy1 + y + int(f.size * 0.55)
                _draw_star_marker(draw, ix1 + mk, m_cy, mk,
                                  star_col + (255,))
                for k, wl in enumerate(wlines):
                    draw.text((ix1 + indent, iy1 + y + k * int(f.size * 1.28)),
                              wl, font=f, fill=gray)
            elif kind == "p":
                _, f, txt, dx, y = blk
                draw.text((ix1, iy1 + y), txt, font=f, fill=gray)
            else:  # "c" closing CTA line
                _, f, txt, dx, y = blk
                draw.text((ix1, iy1 + y), txt, font=f, fill=star_col)

    # ── Tagline (small, above barcode) — adult only (kids uses CTA instead) ──
    if tagline and not is_kids:
        tag_font_size = int(safe_w * 0.040)
        tag_font = _load_font(tag_font_size, BODY_FONT_CANDIDATES)
        tag_y = bz["y1"] - int(safe_h * 0.02)
        tag_lines = _wrap_text(tagline, tag_font, int(safe_w * 0.75))
        for i, tl in enumerate(tag_lines):
            ty = tag_y - (len(tag_lines) - i) * int(tag_font_size * 1.2)
            draw.text((safe["x1"] + int(safe_w * 0.05), ty), tl,
                      font=tag_font, fill=palette["text"])

    # ── Author bio (adult only — kids back cover has no room; hook banner,
    #    bullets, badge and CTA pill already fill it) ──────────────────────────
    if author_bio and not is_kids:
        bio_font_size = int(safe_w * 0.036)
        bio_font = _load_font(bio_font_size, BODY_FONT_CANDIDATES)
        bio_y = bz["y1"] - int(safe_h * 0.02) - int(bio_font_size * 4)
        bio_lines = _wrap_text(author_bio, bio_font, int(safe_w * 0.60))
        for i, bl in enumerate(bio_lines):
            ty = bio_y + i * int(bio_font_size * 1.25)
            draw.text((safe["x1"] + int(safe_w * 0.05), ty), bl,
                      font=bio_font, fill=palette["text"])

    # ── BARCODE SAFE ZONE — solid pure-white, drawn LAST so nothing overlays
    #    it. 2.5"×1.5" centred at (7.5", 10.25") from the PDF top-left, fully
    #    opaque #FFFFFF — generously larger than KDP's 2"×1.2" footprint so no
    #    background colour can bleed in around the eventual barcode. ──────────
    d_ = dim.dpi
    cx_in, cy_in, w_in, h_in = 7.5, 10.25, 2.5, 1.5
    bx1 = round((cx_in - w_in / 2) * d_)
    bx2 = round((cx_in + w_in / 2) * d_)
    by1 = round((cy_in - h_in / 2) * d_)
    by2 = round((cy_in + h_in / 2) * d_)
    draw.rectangle([bx1, by1, bx2, by2], fill=(255, 255, 255, 255))

    return canvas
