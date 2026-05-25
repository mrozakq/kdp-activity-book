"""
Symmetry / mirror-drawing activity for KDP Activity Book.

A vertical dashed line splits the activity area in half. The LEFT half shows
a recognizable picture from a library of half-shapes; the RIGHT half is
empty for the kid to draw the mirror image.

Easy difficulty also gets a small thumbnail in the upper-right corner showing
the full mirrored picture as a hint.
"""
import math
import random

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font
from .layout import compute_activity_box, title_position, instruction_position
from .data.symmetry_shapes import SHAPES, DIFFICULTY_POOLS, BOX_W, BOX_H


# --- primitive rendering ---------------------------------------------

def _semicircle_top_pts(x0, y0, x1, y1, n=24):
    """Polygon approximation of the top half of an ellipse fitting the bbox.
    Flat side is at y1 (bottom), dome reaches y0 (top)."""
    cx = (x0 + x1) / 2
    rx = (x1 - x0) / 2
    ry = y1 - y0
    pts = []
    for i in range(n + 1):
        t = math.pi - i * math.pi / n   # from π (left) to 0 (right)
        pts.append((cx + rx * math.cos(t), y1 - ry * math.sin(t)))
    return pts


def _semicircle_bottom_pts(x0, y0, x1, y1, n=24):
    """Bottom-half ellipse polygon. Flat side at y0, dome at y1."""
    cx = (x0 + x1) / 2
    rx = (x1 - x0) / 2
    ry = y1 - y0
    pts = []
    for i in range(n + 1):
        t = math.pi - i * math.pi / n
        pts.append((cx + rx * math.cos(t), y0 + ry * math.sin(t)))
    return pts


def _render_primitive(draw, prim, x_off, y_off, scale, line_w=6):
    """Render one primitive at (x_off + sx*scale, y_off + sy*scale).
    sx,sy are inside the 800-unit shape box."""
    kind = prim[0]

    def to_px(sx, sy):
        return (x_off + sx * scale, y_off + sy * scale)

    if kind in ('circle', 'ellipse'):
        _, sx, sy, sw, sh = prim
        x0, y0 = to_px(sx, sy)
        x1, y1 = to_px(sx + sw, sy + sh)
        draw.ellipse([(x0, y0), (x1, y1)], outline='black', width=line_w)

    elif kind == 'rectangle':
        _, sx, sy, sw, sh = prim
        x0, y0 = to_px(sx, sy)
        x1, y1 = to_px(sx + sw, sy + sh)
        draw.rectangle([(x0, y0), (x1, y1)], outline='black', width=line_w)

    elif kind in ('triangle_up', 'triangle_down',
                  'triangle_left', 'triangle_right'):
        _, sx, sy, sw, sh = prim
        x0, y0 = to_px(sx, sy)
        x1, y1 = to_px(sx + sw, sy + sh)
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        if kind == 'triangle_up':
            pts = [(cx, y0), (x1, y1), (x0, y1)]
        elif kind == 'triangle_down':
            pts = [(x0, y0), (x1, y0), (cx, y1)]
        elif kind == 'triangle_left':
            pts = [(x0, cy), (x1, y0), (x1, y1)]
        else:  # triangle_right
            pts = [(x1, cy), (x0, y0), (x0, y1)]
        draw.polygon(pts, outline='black', width=line_w)

    elif kind == 'semicircle_top':
        _, sx, sy, sw, sh = prim
        x0, y0 = to_px(sx, sy)
        x1, y1 = to_px(sx + sw, sy + sh)
        draw.polygon(_semicircle_top_pts(x0, y0, x1, y1),
                     outline='black', width=line_w)

    elif kind == 'semicircle_bottom':
        _, sx, sy, sw, sh = prim
        x0, y0 = to_px(sx, sy)
        x1, y1 = to_px(sx + sw, sy + sh)
        draw.polygon(_semicircle_bottom_pts(x0, y0, x1, y1),
                     outline='black', width=line_w)

    elif kind == 'polygon_points':
        _, points = prim
        pts = [to_px(px, py) for (px, py) in points]
        draw.polygon(pts, outline='black', width=line_w)


def _render_shape(draw, primitives, x_off, y_off, scale, line_w=6):
    for prim in primitives:
        _render_primitive(draw, prim, x_off, y_off, scale, line_w=line_w)


# --- full page rendering ---------------------------------------------

def render_symmetry(canvas_size, title, shape_name, show_hint=False):
    cw, ch = canvas_size

    x1, y1, x2, y2 = compute_activity_box(canvas_size, has_instruction=True,
                                           instruction_lines=1)
    aw = x2 - x1
    ah = y2 - y1
    mid_x = x1 + aw // 2
    half_w = mid_x - x1

    primitives = SHAPES[shape_name]

    # Uniform scale: fit the 800-wide shape into half_w, and the BOX_H-tall
    # shape into ah; pick the smaller scale so the shape isn't distorted.
    scale = min(half_w / BOX_W, ah / BOX_H)
    shape_w_px = BOX_W * scale
    shape_h_px = BOX_H * scale

    # Anchor shape so its right edge (x = BOX_W) sits at mid_x.
    # Center vertically in the activity area.
    x_off = mid_x - BOX_W * scale
    y_off = y1 + (ah - shape_h_px) // 2

    img = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    # Title
    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt',
              fill='black', font=get_title_font(130))

    # Instruction
    ix, iy = instruction_position(canvas_size)
    draw.text((ix, iy), 'Draw the other half — copy the picture as a mirror!',
              anchor='mt', fill='black', font=get_body_font(80))

    # Activity-area border
    draw.rectangle([(x1, y1), (x2, y2)], outline=(180, 180, 180), width=3)

    # Mirror axis — vertical dashed line
    dash = 30
    yc = y1
    while yc < y2:
        draw.line([(mid_x, yc), (mid_x, min(yc + dash, y2))],
                  fill='black', width=4)
        yc += dash * 2

    # Draw the shape onto its own layer, then keep ONLY the part left of the
    # mirror axis. Some shapes (apple/flower body circle, balloon) are centred
    # on the axis and would otherwise render whole — leaving the child nothing
    # to mirror. Clipping at mid_x guarantees an empty right half.
    shape_layer = Image.new('L', (cw, ch), 255)
    _render_shape(ImageDraw.Draw(shape_layer), primitives,
                  x_off, y_off, scale, line_w=8)
    ImageDraw.Draw(shape_layer).rectangle([(mid_x, 0), (cw, ch)], fill=255)
    mask = shape_layer.point(lambda p: 255 if p < 128 else 0)
    img.paste((0, 0, 0), (0, 0), mask)

    # Optional hint thumbnail (full mirrored picture) in upper-right corner
    if show_hint:
        thumb_size = 300
        margin = 24
        hx = x2 - thumb_size - margin
        hy = y1 + margin

        # Render hint into a separate small Image, then mirror it pixel-wise
        # for the right half. This guarantees the right half is the exact mirror.
        hint_full = Image.new('RGB', (thumb_size, thumb_size), 'white')
        hint_draw = ImageDraw.Draw(hint_full)
        # Shape fits in left half of thumb
        thumb_scale = min((thumb_size / 2) / BOX_W, thumb_size / BOX_H)
        thumb_shape_h = BOX_H * thumb_scale
        thumb_x_off = (thumb_size // 2) - BOX_W * thumb_scale
        thumb_y_off = (thumb_size - thumb_shape_h) // 2
        _render_shape(hint_draw, primitives,
                      thumb_x_off, thumb_y_off, thumb_scale, line_w=3)
        # Mirror the left half pixel-wise
        left_strip = hint_full.crop((0, 0, thumb_size // 2, thumb_size))
        right_strip = left_strip.transpose(Image.FLIP_LEFT_RIGHT)
        hint_full.paste(right_strip, (thumb_size // 2, 0))
        # Frame
        ImageDraw.Draw(hint_full).rectangle(
            [(0, 0), (thumb_size - 1, thumb_size - 1)],
            outline='black', width=4)
        img.paste(hint_full, (hx, hy))

        # Label above the thumbnail
        draw.text((hx + thumb_size // 2, hy - 14), 'hint',
                  anchor='mb', fill=(120, 120, 120), font=get_body_font(36))

    return img


def generate_symmetry_image(difficulty: str, seed: int, title: str,
                            canvas_size=(2625, 3375)):
    pool = DIFFICULTY_POOLS.get(difficulty, DIFFICULTY_POOLS['medium'])
    # Deterministic rotation through the pool so consecutive symmetry pages
    # in a book use DIFFERENT shapes (no random duplicates).
    shape_name = pool[seed % len(pool)]
    show_hint = (difficulty == 'easy')
    return render_symmetry(canvas_size, title, shape_name,
                           show_hint=show_hint)
