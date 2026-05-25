"""
Recognizable half-shapes for the symmetry / mirror-drawing activity.

Each shape is a list of PRIMITIVES drawn on the LEFT side of an 800×800
reference box. The mirror axis is at x=800 (right edge). The kid draws
the mirror image on the right side.

Primitive types (all use absolute pixel coordinates inside the 800×800 box):

  ('circle',         x, y, w, h)   — circle/ellipse fitting bbox
  ('ellipse',        x, y, w, h)   — same as circle (separate name for clarity)
  ('rectangle',      x, y, w, h)
  ('triangle_up',    x, y, w, h)   — apex at top-center, base at bottom
  ('triangle_down',  x, y, w, h)   — apex at bottom-center, base at top
  ('triangle_left',  x, y, w, h)   — apex at left, base at right
  ('triangle_right', x, y, w, h)   — apex at right, base at left
  ('semicircle_top',    x, y, w, h)  — flat side at bottom, dome on top
  ('semicircle_bottom', x, y, w, h)  — flat side at top, dome at bottom
  ('polygon_points', [(x1,y1), (x2,y2), ...])

Coordinates run 0..800 in x and 0..1000 in y (some shapes use y up to 1000
for stems / strings). The renderer uniformly scales by min(half_width, height).
"""

BOX_W = 800
BOX_H = 1000


butterfly_half = [
    # Upper wing — 7-vertex shape with rounded outer edge
    ('polygon_points', [
        (750, 400), (450, 130), (130, 200), (50, 350),
        (180, 460), (450, 490), (750, 460),
    ]),
    # Lower wing — 7-vertex shape
    ('polygon_points', [
        (750, 480), (480, 530), (200, 580), (100, 690),
        (220, 760), (450, 720), (750, 620),
    ]),
    # Body
    ('rectangle', 750, 220, 50, 480),
    # Antenna
    ('polygon_points', [(800, 220), (700, 80), (700, 100), (800, 230)]),
]

heart_half = [
    # Single polygon for the left half of a heart (notch at top on axis, point at bottom on axis)
    ('polygon_points', [
        (800, 280),    # top notch (on axis)
        (740, 200),    # going up-left over lobe
        (620, 150),    # top of lobe
        (450, 160),    # upper-left
        (300, 230),    # left side
        (220, 350),    # leftmost
        (220, 470),    # outer-left bottom
        (320, 590),    # bottom of left lobe
        (430, 690),    # V transition
        (560, 770),    # toward apex
        (680, 830),    # close to apex
        (800, 870),    # bottom apex (on axis)
    ]),
]

house_half = [
    # Wall
    ('rectangle',   200, 400, 600, 350),
    # Roof
    ('triangle_up', 100, 200, 700, 200),
    # Window
    ('rectangle',   350, 480, 150, 150),
    # Door (on axis side)
    ('rectangle',   650, 550, 150, 200),
]

tree_half = [
    # Foliage — large circle on top
    ('circle',    250, 100, 550, 550),
    # Trunk — narrow rectangle at axis bottom
    ('rectangle', 700, 600, 100, 200),
]

crown_half = [
    # Base
    ('rectangle',   100, 500, 700, 200),
    # 3 points (left, middle, right-on-axis)
    ('triangle_up', 100, 250, 200, 250),
    ('triangle_up', 350, 200, 200, 300),
    ('triangle_up', 600, 250, 200, 250),
    # Center gem
    ('circle',      350, 550, 100, 100),
]

star_half = [
    # Left half of 5-point star
    ('polygon_points', [
        (800, 50),    # top tip on axis
        (550, 250),   # upper inner notch
        (100, 350),   # upper-left tip
        (450, 500),   # lower-left inner notch
        (350, 800),   # lower-left tip
        (800, 650),   # lower inner notch on axis
    ]),
]

flower_half = [
    # Center — circle straddling axis (left half visible, mirrors to full circle)
    ('circle',    600, 280, 400, 400),
    # 3 petals attached to the center on its left side
    ('ellipse',   250,  80, 350, 220),    # upper-left petal
    ('ellipse',   100, 320, 500, 260),    # left petal
    ('ellipse',   250, 600, 350, 220),    # lower-left petal
    # Stem
    ('rectangle', 770, 680,  60, 320),
    # Leaf along the stem
    ('ellipse',   580, 800, 220,  80),
]

balloon_half = [
    # Body — oval CENTRED on the mirror axis (x spans 500..1100, centre=800)
    # so the clipped left half mirrors back into a single round balloon.
    ('ellipse',       500, 130, 600, 620),
    # Knot — small triangle on the axis, just under the body
    ('triangle_down', 758, 740,  84,  64),
    # String — narrow band on the axis going down
    ('polygon_points', [(790, 800), (790, 1000), (810, 1000), (810, 800)]),
]

cat_face_half = [
    # Head
    ('circle',         200, 200, 600, 600),
    # Ear — triangle on top
    ('triangle_up',    350, 100, 200, 200),
    # Eye
    ('circle',         500, 400,  80,  80),
    # Nose — small triangle on axis
    ('triangle_down',  720, 500,  80,  60),
    # 3 whiskers — thin polygons from cheek to far left
    ('polygon_points', [(700, 520), (400, 490), (400, 500), (700, 530)]),
    ('polygon_points', [(700, 550), (400, 550), (400, 560), (700, 560)]),
    ('polygon_points', [(700, 580), (400, 610), (400, 620), (700, 590)]),
]

robot_half = [
    # Antenna ball
    ('circle',     740,  30, 120,  80),
    # Antenna stem
    ('rectangle',  770, 100,  30,  80),
    # Head
    ('rectangle',  450, 180, 350, 280),
    # Eye
    ('circle',     580, 260, 100, 100),
    # Body
    ('rectangle',  350, 460, 450, 300),
    # Arm
    ('rectangle',  200, 510, 150, 100),
    # Leg
    ('rectangle',  550, 760, 150, 200),
]

ice_cream_half = [
    # Cone — triangle pointing down
    ('triangle_down', 300, 400, 500, 400),
    # Scoop 1 — half-circle on top of cone
    ('semicircle_top', 280, 200, 540, 220),
    # Scoop 2 — smaller half-circle on top
    ('semicircle_top', 380,  50, 360, 180),
]

car_half = [
    # Body
    ('rectangle',      100, 400, 700, 200),
    # Roof — trapezoid
    ('polygon_points', [(200, 400), (300, 250), (800, 250), (800, 400)]),
    # Window in roof
    ('rectangle',      350, 280, 400, 110),
    # Wheel
    ('circle',         200, 550, 200, 200),
]

cup_half = [
    # Cup body — trapezoid narrower at bottom
    ('polygon_points', [(250, 200), (800, 200), (800, 750), (300, 750)]),
    # Handle — semicircle on left
    ('semicircle_bottom', 50, 350, 300, 250),
    # Decorative band
    ('rectangle',      400, 400, 350, 150),
]

apple_half = [
    # Apple body — circle straddling the axis (mirrors to a full round apple)
    ('circle',    500, 350, 600, 600),
    # Stem — short rectangle on the axis at the top
    ('rectangle', 760, 210,  80, 170),
    # Leaf — small ellipse beside the stem, pointing left
    ('ellipse',   560, 250, 220, 110),
]

# DISABLED: crescent moon — mirroring the half-crescent produces a lens / eye
# shape that does not read as a recognizable object for a 3-5 year old.
# Replaced in the easy pool by `apple` (a half-circle that mirrors into a
# clear round apple). Definition removed; see git history if ever needed.


# DISABLED: shapes not recognizable after multiple iterations.
# (butterfly — wings don't read as wings; cat_face — eye off the head, whiskers
# misaligned; tree — foliage and trunk disconnected; flower — petals scattered)
# Polygon definitions are kept above for reference but excluded from SHAPES.
SHAPES = {
    'heart':      heart_half,
    'house':      house_half,
    'crown':      crown_half,
    'star':       star_half,
    'balloon':    balloon_half,
    'robot':      robot_half,
    'ice_cream':  ice_cream_half,
    'car':        car_half,
    'cup':        cup_half,
    'apple':      apple_half,
}


DIFFICULTY_POOLS = {
    # Order matters: Symmetry page n -> pool[(seed_base+7000+n) % len]. Index 5
    # (Symmetry 1) is 'balloon' so the half-drawing and the hint thumbnail
    # both clearly read as a balloon (apple kept for later pages).
    'easy':   ['heart', 'star', 'crown', 'apple', 'ice_cream', 'balloon'],
    'medium': ['house', 'car', 'cup'],
    'hard':   ['robot'],
}
