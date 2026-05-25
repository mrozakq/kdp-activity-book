"""
Drawing-grid sheets for preschool free-drawing practice.

Each page shows:
  - Title (Drawing Grid N)
  - A short prompt below the title ("Draw a house!", etc.)
  - A grid of dots that act as the drawing canvas
  - A small example sketch in the upper-right corner so the kid knows what to draw

Easy   = sparse grid (~10×14 dots) — preschool
Medium = standard grid (18×24)
Hard   = dense grid (28×38) — older kids
"""
import math
from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font
from .layout import compute_activity_box, title_position, instruction_position


# (cols, rows, dot_radius_px)
DIFFICULTY_PRESETS = {
    'easy':   (10, 14, 10),
    'medium': (18, 24, 6),
    'hard':   (28, 38, 4),
}


# --- example sketches (drawn in a 300×300 RGBA box) ----------------------

def _ex_house(d, s):
    # Roof
    d.polygon([(s*0.15, s*0.45), (s*0.50, s*0.10), (s*0.85, s*0.45)],
              outline='black', width=5)
    # Wall
    d.rectangle([(s*0.20, s*0.45), (s*0.80, s*0.90)], outline='black', width=5)
    # Door
    d.rectangle([(s*0.42, s*0.62), (s*0.58, s*0.90)], outline='black', width=5)
    # Window
    d.rectangle([(s*0.27, s*0.52), (s*0.40, s*0.65)], outline='black', width=5)


def _ex_flower(d, s):
    cx, cy = s*0.5, s*0.45
    # 5 petals as circles around the center
    for i in range(5):
        a = -math.pi/2 + i * 2*math.pi/5
        px = cx + s*0.18 * math.cos(a)
        py = cy + s*0.18 * math.sin(a)
        d.ellipse([(px-s*0.12, py-s*0.12), (px+s*0.12, py+s*0.12)],
                  outline='black', width=5)
    # Center
    d.ellipse([(cx-s*0.08, cy-s*0.08), (cx+s*0.08, cy+s*0.08)],
              outline='black', width=5)
    # Stem
    d.line([(cx, cy+s*0.20), (cx, s*0.95)], fill='black', width=5)


def _ex_heart(d, s):
    cx, cy = s*0.5, s*0.45
    # Two top lobes
    d.ellipse([(cx-s*0.32, cy-s*0.20), (cx-s*0.04, cy+s*0.08)],
              outline='black', width=5)
    d.ellipse([(cx+s*0.04, cy-s*0.20), (cx+s*0.32, cy+s*0.08)],
              outline='black', width=5)
    # Bottom point — triangle
    d.polygon([(cx-s*0.30, cy-s*0.02), (cx+s*0.30, cy-s*0.02),
               (cx, cy+s*0.40)], outline='black', width=5)


def _ex_sun(d, s):
    cx, cy = s*0.5, s*0.50
    # Rays
    for i in range(8):
        a = i * math.pi / 4
        x0 = cx + s*0.22 * math.cos(a)
        y0 = cy + s*0.22 * math.sin(a)
        x1 = cx + s*0.38 * math.cos(a)
        y1 = cy + s*0.38 * math.sin(a)
        d.line([(x0, y0), (x1, y1)], fill='black', width=5)
    # Body
    d.ellipse([(cx-s*0.18, cy-s*0.18), (cx+s*0.18, cy+s*0.18)],
              outline='black', width=5)


def _ex_star(d, s):
    cx, cy = s*0.5, s*0.5
    R, r = s*0.36, s*0.15
    pts = []
    for i in range(10):
        a = -math.pi/2 + i * math.pi / 5
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad*math.cos(a), cy + rad*math.sin(a)))
    d.polygon(pts, outline='black', width=5)


def _ex_tree(d, s):
    # Foliage — 3 stacked triangles
    d.polygon([(s*0.30, s*0.35), (s*0.50, s*0.10), (s*0.70, s*0.35)],
              outline='black', width=5)
    d.polygon([(s*0.25, s*0.55), (s*0.50, s*0.28), (s*0.75, s*0.55)],
              outline='black', width=5)
    d.polygon([(s*0.20, s*0.78), (s*0.50, s*0.50), (s*0.80, s*0.78)],
              outline='black', width=5)
    # Trunk
    d.rectangle([(s*0.44, s*0.78), (s*0.56, s*0.95)], outline='black', width=5)


def _ex_balloon(d, s):
    cx = s*0.5
    # Body — egg ellipse
    d.ellipse([(cx-s*0.22, s*0.10), (cx+s*0.22, s*0.60)],
              outline='black', width=5)
    # Knot
    d.polygon([(cx-s*0.05, s*0.60), (cx+s*0.05, s*0.60), (cx, s*0.68)],
              outline='black', width=5)
    # String — wavy line
    pts = [(cx + s*0.04*math.sin(t*math.pi*2), s*0.68 + t*s*0.27)
           for t in (i/12 for i in range(13))]
    for i in range(len(pts)-1):
        d.line([pts[i], pts[i+1]], fill='black', width=4)


def _ex_car(d, s):
    # Body
    d.rectangle([(s*0.10, s*0.45), (s*0.90, s*0.72)],
                outline='black', width=5)
    # Roof
    d.polygon([(s*0.28, s*0.45), (s*0.38, s*0.25),
               (s*0.62, s*0.25), (s*0.72, s*0.45)],
              outline='black', width=5)
    # 2 wheels
    for cx in (s*0.28, s*0.72):
        d.ellipse([(cx-s*0.10, s*0.70), (cx+s*0.10, s*0.90)],
                  outline='black', width=5)


# --- prompt pool ---------------------------------------------------------

PROMPTS = [
    ('Draw a house!',   _ex_house),
    ('Draw a flower!',  _ex_flower),
    ('Draw a heart!',   _ex_heart),
    ('Draw a sun!',     _ex_sun),
    ('Draw a star!',    _ex_star),
    ('Draw a tree!',    _ex_tree),
    ('Draw a balloon!', _ex_balloon),
    ('Draw a car!',     _ex_car),
]


# --- rendering -----------------------------------------------------------

def render_dot_grid(canvas_size=(2625, 3375), title='Drawing Grid',
                    cols=18, rows=24, dot_r=6,
                    prompt='', example_fn=None):
    cw, ch = canvas_size

    has_inst = bool(prompt)
    x1, y1, x2, y2 = compute_activity_box(canvas_size,
                                          has_instruction=has_inst,
                                          instruction_lines=1)

    img  = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    # Title
    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black',
              font=get_title_font(130))

    # Prompt (instruction line)
    if prompt:
        ix, iy = instruction_position(canvas_size)
        draw.text((ix, iy), prompt, anchor='mt', fill='black',
                  font=get_body_font(80))

    # Example thumbnail in upper-right of activity area (300×300)
    thumb_size = 360
    if example_fn:
        thumb = Image.new('RGBA', (thumb_size, thumb_size), (255, 255, 255, 255))
        td = ImageDraw.Draw(thumb)
        example_fn(td, thumb_size)
        # Frame
        td.rectangle([(0, 0), (thumb_size-1, thumb_size-1)],
                     outline='black', width=4)
        # Label above
        thumb_x = x2 - thumb_size - 20
        thumb_y = y1 + 20
        img.paste(thumb, (thumb_x, thumb_y))
        # 'example' label above thumb
        draw.text((thumb_x + thumb_size // 2, thumb_y - 14),
                  'example', anchor='mb',
                  fill=(120, 120, 120), font=get_body_font(36))
        # Push the dot grid below the example
        grid_top_y = thumb_y + thumb_size + 60
    else:
        grid_top_y = y1

    # Dot grid — fits in remaining area below the example
    avail_h = y2 - grid_top_y
    avail_w = x2 - x1
    spacing = min(avail_w / (cols - 1), avail_h / (rows - 1))
    grid_w = spacing * (cols - 1)
    grid_h = spacing * (rows - 1)
    grid_left = (cw - grid_w) // 2
    grid_top  = grid_top_y + (avail_h - grid_h) // 2

    for r in range(rows):
        for c in range(cols):
            x = grid_left + c * spacing
            y = grid_top  + r * spacing
            draw.ellipse([(x - dot_r, y - dot_r), (x + dot_r, y + dot_r)],
                         fill='black')

    return img


def generate_dot_grid_image(difficulty: str, seed: int, title: str,
                            canvas_size=(2625, 3375)):
    cols, rows, dot_r = DIFFICULTY_PRESETS.get(difficulty,
                                               DIFFICULTY_PRESETS['medium'])
    prompt, example_fn = PROMPTS[seed % len(PROMPTS)]
    return render_dot_grid(canvas_size=canvas_size, title=title,
                           cols=cols, rows=rows, dot_r=dot_r,
                           prompt=prompt, example_fn=example_fn)
