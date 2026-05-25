"""
Color-by-number sheets for KDP Activity Book.

Each subject is built as a list of polygon `Region`s, each tagged with a
`color_id` (1-8). The generator:

  1. Draws every polygon outline in black on white (no fills — kid colors them).
  2. Stamps the color number at the polygon's centroid, with a small white pad
     behind the digit so it stays readable when it lands on an outline.
  3. Renders a legend at the bottom: filled colored swatch + number + name.

Templates are procedural (compositions of ellipses, circles, triangles, etc.)
rather than SVG files — they are deterministic by seed and trivial to compose.
"""
import math
import random
from dataclasses import dataclass
from typing import List, Tuple

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font, get_label_font


COLORS = {
    1: ('Red',    (220,  53,  69)),
    2: ('Blue',   ( 13, 110, 253)),
    3: ('Yellow', (255, 193,   7)),
    4: ('Green',  ( 25, 135,  84)),
    5: ('Orange', (253, 126,  20)),
    6: ('Brown',  (133,  77,  14)),
    7: ('Pink',   (240, 100, 160)),
    8: ('Purple', (111,  66, 193)),
}


@dataclass
class Region:
    polygon: List[Tuple[float, float]]   # normalized 0..1 coords
    color_id: int
    preset: bool = False                 # if True, drawn solid black (no number, no legend entry)


# --- geometry helpers --------------------------------------------------

def _ellipse(cx, cy, rx, ry, n=40):
    return [(cx + rx * math.cos(2 * math.pi * i / n),
             cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _ellipse_rot(cx, cy, rx, ry, angle, n=40):
    cos_t, sin_t = math.cos(angle), math.sin(angle)
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = rx * math.cos(t)
        y = ry * math.sin(t)
        out.append((cx + x * cos_t - y * sin_t,
                    cy + x * sin_t + y * cos_t))
    return out


def _circle(cx, cy, r, n=32):
    return _ellipse(cx, cy, r, r, n)


def _mirror_x(poly, axis=0.5):
    return [(2 * axis - x, y) for (x, y) in poly]


def _centroid(poly):
    n = len(poly)
    if n < 3:
        return (sum(x for x, _ in poly) / n,
                sum(y for _, y in poly) / n)
    a = cx = cy = 0.0
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a *= 0.5
    if abs(a) < 1e-9:
        return (sum(x for x, _ in poly) / n,
                sum(y for _, y in poly) / n)
    return (cx / (6 * a), cy / (6 * a))


def _bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))


def _sun(cx, cy, r, rays=8):
    """Sun = 2N-vertex star with `rays` outer points. Sharper than a plain circle."""
    R = r * 1.7
    pts = []
    for i in range(rays * 2):
        ang = -math.pi / 2 + i * math.pi / rays
        rr = R if i % 2 == 0 else r
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts


def _cloud(cx, cy, w, h):
    """Bumpy-top, flat-bottom cloud polygon. Three visible humps on top."""
    hw = w / 2
    hh = h / 2
    return [
        (cx - hw,         cy + hh * 0.40),
        (cx - hw * 0.95,  cy + hh * 0.05),
        (cx - hw * 0.85,  cy - hh * 0.20),
        (cx - hw * 0.65,  cy - hh * 0.55),   # bump 1
        (cx - hw * 0.40,  cy - hh * 0.25),   # valley
        (cx - hw * 0.10,  cy - hh * 0.80),   # bump 2 (tallest)
        (cx + hw * 0.20,  cy - hh * 0.30),   # valley
        (cx + hw * 0.55,  cy - hh * 0.60),   # bump 3
        (cx + hw * 0.80,  cy - hh * 0.20),
        (cx + hw * 0.95,  cy + hh * 0.05),
        (cx + hw,         cy + hh * 0.40),
    ]


def _star_pts(cx, cy, R, n=5):
    """N-point star polygon (2N vertices alternating outer/inner radius)."""
    r = R * 0.40
    pts = []
    for i in range(2 * n):
        ang = -math.pi / 2 + i * math.pi / n
        rr = R if i % 2 == 0 else r
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts


def _point_segment_dist(px, py, ax, ay, bx, by):
    """Distance from point (px,py) to segment (ax,ay)-(bx,by)."""
    abx = bx - ax
    aby = by - ay
    len_sq = abx * abx + aby * aby
    if len_sq < 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * abx + (py - ay) * aby) / len_sq))
    cx = ax + t * abx
    cy = ay + t * aby
    return math.hypot(px - cx, py - cy)


def _inscribed_radius(poly):
    """Distance from centroid to nearest polygon edge. For convex polygons this
    is a good approximation of the largest inscribed circle radius at the centroid."""
    cx, cy = _centroid(poly)
    n = len(poly)
    min_d = float('inf')
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        d = _point_segment_dist(cx, cy, ax, ay, bx, by)
        if d < min_d:
            min_d = d
    return min_d


def _find_leader_target(cx, cy, fs, occupied, pic_bounds, max_dist=420, step=24):
    """Find a free target position (outside the source region) to place a leadered
    number. occupied = list of (x0, y0, x1, y1) bboxes already taken.
    Returns (tx, ty) or None if no spot found."""
    text_hw = fs * 0.40
    text_hh = fs * 0.50
    bx0, by0, bx1, by1 = pic_bounds
    for dist in range(70, max_dist, step):
        for ang_deg in (-60, -120, -90, -30, -150, 0, 180, 60, 30, 120, 150):
            ang = math.radians(ang_deg)
            tx = cx + dist * math.cos(ang)
            ty = cy + dist * math.sin(ang)
            if tx - text_hw < bx0 or tx + text_hw > bx1: continue
            if ty - text_hh < by0 or ty + text_hh > by1: continue
            ok = True
            for (ox0, oy0, ox1, oy1) in occupied:
                if (tx + text_hw + 6 > ox0 and tx - text_hw - 6 < ox1
                    and ty + text_hh + 6 > oy0 and ty - text_hh - 6 < oy1):
                    ok = False
                    break
            if ok:
                return (tx, ty)
    return None


# --- EASY templates (5-8 regions, 3-4 colors) --------------------------

def tpl_heart():
    """Heart: two top lobes + middle band + lower band + point. 5 regions."""
    left  = _circle(0.36, 0.35, 0.14, 40)
    right = _circle(0.64, 0.35, 0.14, 40)
    mid   = [(0.20, 0.42), (0.80, 0.42), (0.68, 0.58), (0.32, 0.58)]
    low   = [(0.32, 0.58), (0.68, 0.58), (0.58, 0.74), (0.42, 0.74)]
    pt    = [(0.42, 0.74), (0.58, 0.74), (0.50, 0.92)]
    return [
        Region(left, 1), Region(right, 1),
        Region(mid, 7), Region(low, 8), Region(pt, 1),
    ]


def tpl_star():
    """5-point star: 5 outer arm-triangles + inner pentagon. 6 regions.

    Inner radius is a large fraction of the outer radius so the arm triangles
    are fat/stubby — this guarantees each arm has a big enough inscribed
    circle for its number to be drawn at the centroid (no fragile tiny-font
    / leader-line fallback, so EVERY region always shows a clear number)."""
    cx, cy = 0.5, 0.50
    R = 0.42
    r = R * 0.52          # fatter arms than the old 0.42 ratio
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = R if i % 2 == 0 else r
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    pentagon = [pts[i] for i in range(1, 10, 2)]
    # Center = yellow(3); arms alternate red(1)/orange(5) for a nice look.
    arm_colors = [1, 5, 1, 5, 3]
    regions = [Region(pentagon, 3)]
    for k in range(5):
        outer = pts[2 * k]
        left  = pts[(2 * k - 1) % 10]
        right = pts[(2 * k + 1) % 10]
        regions.append(Region([left, outer, right], arm_colors[k]))
    return regions


def tpl_flower_simple():
    """5 ellipse petals (pointing outward) + center + stem + leaf. 8 regions, 3 colors."""
    fc = (0.50, 0.35)
    petals = []
    for i in range(5):
        ang = -math.pi / 2 + i * 2 * math.pi / 5
        px = fc[0] + 0.17 * math.cos(ang)
        py = fc[1] + 0.17 * math.sin(ang)
        petals.append(_ellipse_rot(px, py, 0.12, 0.06, ang))
    center = _circle(*fc, 0.07)
    stem   = [(0.48, 0.39), (0.52, 0.39), (0.52, 0.92), (0.48, 0.92)]
    leaf   = _ellipse_rot(0.40, 0.70, 0.10, 0.04, math.pi * 0.15)
    regions = [Region(p, 7) for p in petals]
    regions += [Region(center, 3), Region(stem, 4), Region(leaf, 4)]
    return regions


def tpl_ice_cream():
    """Ice cream cone: 2 scoops + cone + cherry on top. 5 regions, 4 colors."""
    # Top scoop (smaller)
    scoop_top = _circle(0.50, 0.32, 0.12)
    # Bottom scoop (larger, overlapping)
    scoop_bot = _circle(0.50, 0.50, 0.18)
    # Cone — triangle pointing down
    cone = [(0.32, 0.62), (0.68, 0.62), (0.50, 0.95)]
    # Cherry on top
    cherry = _circle(0.50, 0.16, 0.05)
    # Stem — small dark rectangle
    stem = [(0.49, 0.10), (0.51, 0.10), (0.51, 0.15), (0.49, 0.15)]
    return [
        Region(scoop_top, 7),    # pink
        Region(scoop_bot, 3),    # yellow
        Region(cone, 6),         # brown
        Region(cherry, 1),       # red
        Region(stem, 4),         # green
    ]


def tpl_car():
    """Side-view car: body + roof + 2 wheels + headlight.
    5 cleanly separated regions, 3 colors."""
    body     = [(0.10, 0.55), (0.90, 0.55), (0.90, 0.72), (0.10, 0.72)]
    # Trapezoid roof on top of body, narrower at the top
    roof     = [(0.28, 0.55), (0.38, 0.42), (0.62, 0.42), (0.72, 0.55)]
    wheel_l  = _circle(0.28, 0.78, 0.07)
    wheel_r  = _circle(0.72, 0.78, 0.07)
    headlight = _circle(0.86, 0.62, 0.025)
    return [
        Region(body, 2),         # blue
        Region(roof, 3),         # yellow
        Region(wheel_l, 6),      # brown
        Region(wheel_r, 6),
        Region(headlight, 3),    # yellow
    ]


def tpl_balloon():
    """Balloon body + knot + string. 3 regions, 2 colors.
    The string is a preset solid-black region — wide enough to clearly read
    as a filled shape (matches the '= already filled' legend entry)."""
    balloon = _ellipse(0.50, 0.34, 0.20, 0.26)
    knot    = [(0.46, 0.58), (0.54, 0.58), (0.50, 0.65)]
    # Wider string so the black fill is obviously a filled region, not a line.
    string  = [(0.478, 0.65), (0.522, 0.65), (0.522, 0.94), (0.478, 0.94)]
    return [
        Region(balloon, 1),      # red
        Region(knot, 5),         # orange
        Region(string, 0, preset=True),    # solid black string (already filled)
    ]


# --- MEDIUM templates (8-12 regions, 5-6 colors) -----------------------

def tpl_butterfly():
    """Body + 4 wings + 4 wing-spots + 4 wing-pattern dots. 13 regions, 6 colors."""
    body = _ellipse(0.50, 0.50, 0.04, 0.22)
    ulw = [(0.46, 0.30), (0.10, 0.18), (0.05, 0.40), (0.30, 0.48), (0.46, 0.45)]
    llw = [(0.46, 0.55), (0.30, 0.55), (0.15, 0.78), (0.38, 0.82), (0.46, 0.70)]
    urw = _mirror_x(ulw)
    lrw = _mirror_x(llw)
    s1  = _circle(0.22, 0.30, 0.045)
    s2  = _circle(0.78, 0.30, 0.045)
    s3  = _circle(0.26, 0.68, 0.035)
    s4  = _circle(0.74, 0.68, 0.035)
    # 4 smaller pattern dots, one per wing
    d1 = _circle(0.35, 0.40, 0.022)
    d2 = _circle(0.65, 0.40, 0.022)
    d3 = _circle(0.38, 0.62, 0.020)
    d4 = _circle(0.62, 0.62, 0.020)
    return [
        Region(body, 6),
        Region(ulw, 2), Region(urw, 2),
        Region(llw, 5), Region(lrw, 5),
        Region(s1, 3), Region(s2, 3),
        Region(s3, 7), Region(s4, 7),
        Region(d1, 4), Region(d2, 4),
        Region(d3, 4), Region(d4, 4),
    ]


def tpl_fish():
    """Body + tail + 2 fins + eye + pupil + 3 stripes + 3 scales.
    12 regions, 6 colors. (No bubbles — would look like stray circles in corner.)"""
    body    = _ellipse(0.43, 0.50, 0.24, 0.18)
    tail    = [(0.65, 0.50), (0.92, 0.28), (0.85, 0.50), (0.92, 0.72)]
    top_fin = [(0.30, 0.34), (0.50, 0.18), (0.55, 0.34)]
    bot_fin = [(0.50, 0.66), (0.55, 0.66), (0.35, 0.80)]
    eye     = _circle(0.26, 0.45, 0.030)
    pupil   = _circle(0.26, 0.45, 0.012)
    s1 = _ellipse(0.32, 0.50, 0.025, 0.15)
    s2 = _ellipse(0.44, 0.50, 0.025, 0.17)
    s3 = _ellipse(0.56, 0.50, 0.025, 0.13)
    sc1 = _circle(0.38, 0.40, 0.022)
    sc2 = _circle(0.50, 0.40, 0.022)
    sc3 = _circle(0.38, 0.60, 0.022)
    return [
        Region(body, 2),
        Region(tail, 5),
        Region(top_fin, 5),
        Region(bot_fin, 5),
        Region(eye, 8),
        Region(pupil, 0, preset=True),
        Region(s1, 3), Region(s2, 7), Region(s3, 3),
        Region(sc1, 7), Region(sc2, 7), Region(sc3, 7),
    ]


def tpl_house():
    """Wall, roof, chimney, door + handle, left window (4 panes), right window,
    sun, cloud, ground. 13 regions, 6 colors."""
    wall     = [(0.22, 0.45), (0.78, 0.45), (0.78, 0.88), (0.22, 0.88)]
    roof     = [(0.16, 0.45), (0.50, 0.20), (0.84, 0.45)]
    chimney  = [(0.62, 0.28), (0.70, 0.28), (0.70, 0.40), (0.62, 0.40)]
    door     = [(0.44, 0.66), (0.56, 0.66), (0.56, 0.88), (0.44, 0.88)]
    handle   = _circle(0.535, 0.78, 0.022)
    # Left window split into 4 panes
    pane_tl  = [(0.28, 0.55),  (0.34, 0.55),  (0.34, 0.605), (0.28, 0.605)]
    pane_tr  = [(0.34, 0.55),  (0.40, 0.55),  (0.40, 0.605), (0.34, 0.605)]
    pane_bl  = [(0.28, 0.605), (0.34, 0.605), (0.34, 0.66),  (0.28, 0.66)]
    pane_br  = [(0.34, 0.605), (0.40, 0.605), (0.40, 0.66),  (0.34, 0.66)]
    window_r = [(0.60, 0.55), (0.72, 0.55), (0.72, 0.66), (0.60, 0.66)]
    sun      = _sun(0.12, 0.12, 0.06)
    cloud    = _cloud(0.83, 0.16, 0.22, 0.12)
    ground   = [(0.05, 0.88), (0.95, 0.88), (0.95, 0.95), (0.05, 0.95)]
    return [
        Region(wall, 6),
        Region(roof, 1), Region(chimney, 1),
        Region(door, 5), Region(handle, 3),
        Region(pane_tl, 2), Region(pane_tr, 3),
        Region(pane_bl, 4), Region(pane_br, 5),
        Region(window_r, 3),
        Region(sun, 3),
        Region(cloud, 2),
        Region(ground, 4),
    ]


# --- HARD templates (13-22 regions, 7-8 colors) ------------------------

def tpl_cat():
    """Side-profile sitting cat: oval body + head on the right, S-curve tail on the
    left, 2 visible legs with paws, 3 side stripes, collar, bow, mouth.
    22 regions (4 preset-black: pupil + 3 whiskers), 8 colors."""
    # Body — horizontal ellipse
    body = _ellipse(0.46, 0.66, 0.22, 0.13)
    # Head — circle on the right, slightly higher than body center
    head = _ellipse(0.74, 0.46, 0.13, 0.12)
    # Ears (2 triangles on top of head)
    ear_l = [(0.65, 0.39), (0.68, 0.26), (0.74, 0.38)]
    ear_r = [(0.74, 0.38), (0.80, 0.26), (0.83, 0.39)]
    inner_ear_l = [(0.67, 0.37), (0.69, 0.30), (0.73, 0.38)]
    inner_ear_r = [(0.75, 0.38), (0.79, 0.30), (0.81, 0.37)]
    # Eye + pupil (single, side view)
    eye = _circle(0.72, 0.44, 0.030)
    pupil = _circle(0.725, 0.44, 0.013)
    # Nose at front of head
    nose = [(0.85, 0.49), (0.88, 0.48), (0.86, 0.52)]
    # Mouth — small triangle below nose
    mouth = [(0.84, 0.53), (0.87, 0.53), (0.855, 0.56)]
    # 2 visible legs (front + back), each as a vertical-ish triangle
    leg_front = [(0.58, 0.74), (0.66, 0.74), (0.62, 0.86)]
    leg_back  = [(0.30, 0.74), (0.38, 0.74), (0.34, 0.86)]
    # Paws — small ellipses at the bottom of each leg
    paw_front = _ellipse(0.62, 0.89, 0.05, 0.025)
    paw_back  = _ellipse(0.34, 0.89, 0.05, 0.025)
    # Tail — S-curve polygon stretching left and up from body
    tail = [
        (0.27, 0.62),
        (0.20, 0.50),
        (0.10, 0.40),
        (0.06, 0.34),
        (0.10, 0.30),
        (0.16, 0.38),
        (0.24, 0.52),
        (0.30, 0.62),
    ]
    # 3 short curved stripes on the upper-back of body (oriented along body curve)
    stripe_1 = _ellipse_rot(0.40, 0.57, 0.05, 0.011, -math.pi * 0.06)
    stripe_2 = _ellipse_rot(0.48, 0.55, 0.05, 0.011, 0)
    stripe_3 = _ellipse_rot(0.56, 0.57, 0.05, 0.011, math.pi * 0.06)
    # Collar — small band at the neck (between body and head)
    collar = [(0.60, 0.56), (0.70, 0.56), (0.70, 0.60), (0.60, 0.60)]
    # Bow on top of head between ears
    bow = [(0.71, 0.30), (0.74, 0.27), (0.77, 0.30), (0.74, 0.33)]
    # 3 whiskers from cheek (preset black, no number)
    whisker_1 = [(0.84, 0.50), (0.96, 0.49), (0.84, 0.508)]
    whisker_2 = [(0.84, 0.515), (0.96, 0.515), (0.84, 0.522)]
    whisker_3 = [(0.84, 0.53), (0.96, 0.54), (0.84, 0.538)]
    return [
        Region(body, 6),
        Region(head, 6),
        Region(ear_l, 6), Region(ear_r, 6),
        Region(inner_ear_l, 7), Region(inner_ear_r, 7),
        Region(eye, 4),
        Region(pupil, 0, preset=True),
        Region(nose, 1),
        Region(mouth, 1),
        Region(leg_front, 6), Region(leg_back, 6),
        Region(paw_front, 3), Region(paw_back, 3),
        Region(tail, 6),
        Region(stripe_1, 5), Region(stripe_2, 5), Region(stripe_3, 5),
        Region(collar, 2),
        Region(bow, 8),
        Region(whisker_1, 0, preset=True),
        Region(whisker_2, 0, preset=True),
        Region(whisker_3, 0, preset=True),
    ]


def tpl_garden_scene():
    """Sun (star-shape, rays integrated into outline) + 2 clouds + 2 ellipse-petal
    flowers (stem+leaf each) + larger butterfly + ground line.
    ~21 regions, 8 colors."""
    regions = []
    # Sun (8 rays, sharp points)
    regions.append(Region(_sun(0.14, 0.13, 0.07), 3))
    # Clouds (bumpy silhouette)
    regions.append(Region(_cloud(0.78, 0.13, 0.30, 0.12), 2))
    # Flower 1 (left, pink ellipse petals with yellow center)
    fc1 = (0.28, 0.55)
    for i in range(5):
        ang = -math.pi / 2 + i * 2 * math.pi / 5
        px = fc1[0] + 0.10 * math.cos(ang)
        py = fc1[1] + 0.10 * math.sin(ang)
        regions.append(Region(_ellipse_rot(px, py, 0.08, 0.04, ang), 7))
    regions.append(Region(_circle(*fc1, 0.05), 3))
    regions.append(Region([(0.27, 0.58), (0.29, 0.58), (0.29, 0.93), (0.27, 0.93)], 4))
    regions.append(Region(_ellipse_rot(0.22, 0.76, 0.07, 0.03, math.pi * 0.20), 4))
    # Flower 2 (right, red ellipse petals with yellow center)
    fc2 = (0.72, 0.48)
    for i in range(5):
        ang = -math.pi / 2 + i * 2 * math.pi / 5
        px = fc2[0] + 0.11 * math.cos(ang)
        py = fc2[1] + 0.11 * math.sin(ang)
        regions.append(Region(_ellipse_rot(px, py, 0.09, 0.045, ang), 1))
    regions.append(Region(_circle(*fc2, 0.05), 3))
    regions.append(Region([(0.71, 0.51), (0.73, 0.51), (0.73, 0.93), (0.71, 0.93)], 4))
    regions.append(Region(_ellipse_rot(0.78, 0.72, 0.07, 0.03, -math.pi * 0.20), 4))
    # Butterfly — bigger, between/below flowers
    bx, by = 0.50, 0.30
    regions.append(Region(_ellipse(bx, by, 0.02, 0.06), 6))
    regions.append(Region([(bx - 0.01, by - 0.04), (bx - 0.13, by - 0.07),
                           (bx - 0.05, by + 0.02)], 8))
    regions.append(Region([(bx + 0.01, by - 0.04), (bx + 0.13, by - 0.07),
                           (bx + 0.05, by + 0.02)], 8))
    regions.append(Region([(bx - 0.01, by + 0.04), (bx - 0.11, by + 0.10),
                           (bx - 0.05, by + 0.02)], 8))
    regions.append(Region([(bx + 0.01, by + 0.04), (bx + 0.11, by + 0.10),
                           (bx + 0.05, by + 0.02)], 8))
    # Ground line
    regions.append(Region([(0.0, 0.93), (1.0, 0.93), (1.0, 0.99), (0.0, 0.99)], 4))
    return regions


def tpl_rocket():
    """Rocket: nose cone + body + 3 windows + 2 fins + 3 flames + 3 background stars.
    13 regions, 5 colors."""
    body  = [(0.42, 0.30), (0.58, 0.30), (0.60, 0.78), (0.40, 0.78)]
    nose  = [(0.42, 0.30), (0.50, 0.08), (0.58, 0.30)]
    win_1 = _circle(0.50, 0.40, 0.045)
    win_2 = _circle(0.50, 0.54, 0.045)
    win_3 = _circle(0.50, 0.68, 0.045)
    fin_l = [(0.40, 0.62), (0.28, 0.82), (0.40, 0.82)]
    fin_r = [(0.60, 0.62), (0.72, 0.82), (0.60, 0.82)]
    flame_c = [(0.46, 0.78), (0.50, 0.94), (0.54, 0.78)]
    flame_l = [(0.42, 0.78), (0.44, 0.90), (0.48, 0.78)]
    flame_r = [(0.52, 0.78), (0.56, 0.90), (0.58, 0.78)]
    star_1 = _star_pts(0.16, 0.20, 0.040)
    star_2 = _star_pts(0.84, 0.22, 0.038)
    star_3 = _star_pts(0.14, 0.50, 0.034)
    return [
        Region(body, 6),
        Region(nose, 1),
        Region(win_1, 2), Region(win_2, 2), Region(win_3, 2),
        Region(fin_l, 5), Region(fin_r, 5),
        Region(flame_c, 1), Region(flame_l, 3), Region(flame_r, 3),
        Region(star_1, 3), Region(star_2, 3), Region(star_3, 3),
    ]


def tpl_cupcake():
    """Cupcake: 4-stripe wrapper + 3-band mushroom-dome frosting + cherry with stem
    + 4 floating sprinkles around the cupcake (in the air, not on frosting).
    13 regions, 6 colors."""
    # Wrapper (4 vertical stripes)
    s1 = [(0.34, 0.55), (0.42, 0.55), (0.45, 0.92), (0.40, 0.92)]
    s2 = [(0.42, 0.55), (0.50, 0.55), (0.50, 0.92), (0.45, 0.92)]
    s3 = [(0.50, 0.55), (0.58, 0.55), (0.55, 0.92), (0.50, 0.92)]
    s4 = [(0.58, 0.55), (0.66, 0.55), (0.60, 0.92), (0.55, 0.92)]
    # Frosting — 3 overlapping ellipses forming a mushroom dome with a taller middle bump
    fr_l = _ellipse(0.40, 0.42, 0.11, 0.11)
    fr_c = _ellipse(0.50, 0.37, 0.11, 0.14)
    fr_r = _ellipse(0.60, 0.42, 0.11, 0.11)
    # Cherry on top of the middle bump + stem
    cherry = _circle(0.50, 0.18, 0.045)
    stem   = [(0.49, 0.10), (0.51, 0.10), (0.51, 0.15), (0.49, 0.15)]
    # 4 sprinkles — floating around the cupcake (not on frosting)
    sp1 = _ellipse_rot(0.18, 0.40, 0.04, 0.018,  math.pi * 0.25)
    sp2 = _ellipse_rot(0.82, 0.42, 0.04, 0.018, -math.pi * 0.30)
    sp3 = _ellipse_rot(0.16, 0.62, 0.04, 0.018,  math.pi * 0.35)
    sp4 = _ellipse_rot(0.84, 0.60, 0.04, 0.018, -math.pi * 0.25)
    return [
        Region(s1, 7), Region(s2, 2), Region(s3, 7), Region(s4, 2),
        Region(fr_l, 3), Region(fr_c, 3), Region(fr_r, 3),
        Region(cherry, 1), Region(stem, 4),
        Region(sp1, 5), Region(sp2, 8), Region(sp3, 5), Region(sp4, 8),
    ]


def tpl_birthday_cake():
    """3-tier cake: 3 tiers + plate + 4 frosting dollops between tiers + 3 candles
    + 3 flames + 6 decoration dots. 20 regions, 8 colors."""
    tier_top = [(0.40, 0.30), (0.60, 0.30), (0.60, 0.45), (0.40, 0.45)]
    tier_mid = [(0.32, 0.45), (0.68, 0.45), (0.68, 0.62), (0.32, 0.62)]
    tier_bot = [(0.24, 0.62), (0.76, 0.62), (0.76, 0.80), (0.24, 0.80)]
    plate    = _ellipse(0.50, 0.83, 0.34, 0.04)
    fd1 = _circle(0.30, 0.62, 0.028)
    fd2 = _circle(0.42, 0.62, 0.028)
    fd3 = _circle(0.58, 0.62, 0.028)
    fd4 = _circle(0.70, 0.62, 0.028)
    candle_l = [(0.41, 0.18), (0.45, 0.18), (0.45, 0.30), (0.41, 0.30)]
    candle_c = [(0.48, 0.15), (0.52, 0.15), (0.52, 0.30), (0.48, 0.30)]
    candle_r = [(0.55, 0.18), (0.59, 0.18), (0.59, 0.30), (0.55, 0.30)]
    flame_l = _ellipse(0.43, 0.14, 0.022, 0.038)
    flame_c = _ellipse(0.50, 0.10, 0.024, 0.045)
    flame_r = _ellipse(0.57, 0.14, 0.022, 0.038)
    dec_top_1 = _circle(0.46, 0.38, 0.024)
    dec_top_2 = _circle(0.54, 0.38, 0.024)
    dec_mid_1 = _circle(0.40, 0.53, 0.026)
    dec_mid_2 = _circle(0.60, 0.53, 0.026)
    dec_bot_1 = _circle(0.34, 0.71, 0.026)
    dec_bot_2 = _circle(0.66, 0.71, 0.026)
    return [
        Region(tier_top, 7),
        Region(tier_mid, 8),
        Region(tier_bot, 7),
        Region(plate, 6),
        Region(fd1, 3), Region(fd2, 3), Region(fd3, 3), Region(fd4, 3),
        Region(candle_l, 4), Region(candle_c, 4), Region(candle_r, 4),
        Region(flame_l, 5), Region(flame_c, 5), Region(flame_r, 5),
        Region(dec_top_1, 1), Region(dec_top_2, 1),
        Region(dec_mid_1, 2), Region(dec_mid_2, 2),
        Region(dec_bot_1, 8), Region(dec_bot_2, 8),
    ]


def tpl_beach_scene():
    """Beach: sun + cloud + palm (trunk + 4 leaves + 2 coconuts) + umbrella
    (4 panels + pole) + beach ball (+2 stripes) + sand + 2 starfish + 2 shells.
    22 regions, 8 colors."""
    regions = []
    regions.append(Region(_sun(0.14, 0.13, 0.07), 3))
    regions.append(Region(_cloud(0.78, 0.13, 0.28, 0.10), 2))
    # Palm trunk
    regions.append(Region([(0.18, 0.42), (0.24, 0.42), (0.26, 0.85), (0.20, 0.85)], 6))
    # 4 leaves radiating from top of trunk
    regions.append(Region(_ellipse_rot(0.10, 0.40, 0.10, 0.045,  math.pi * 0.20), 4))
    regions.append(Region(_ellipse_rot(0.32, 0.38, 0.10, 0.045, -math.pi * 0.15), 4))
    regions.append(Region(_ellipse_rot(0.06, 0.30, 0.10, 0.045,  math.pi * 0.40), 4))
    regions.append(Region(_ellipse_rot(0.36, 0.28, 0.10, 0.045, -math.pi * 0.35), 4))
    # 2 coconuts
    regions.append(Region(_circle(0.20, 0.43, 0.025), 6))
    regions.append(Region(_circle(0.24, 0.43, 0.025), 6))
    # Umbrella canopy: 4 triangular panels meeting at apex
    apex_x, apex_y, base_y = 0.70, 0.40, 0.55
    regions.append(Region([(apex_x, apex_y), (0.50, base_y), (0.60, base_y)], 1))
    regions.append(Region([(apex_x, apex_y), (0.60, base_y), (0.70, base_y)], 3))
    regions.append(Region([(apex_x, apex_y), (0.70, base_y), (0.80, base_y)], 1))
    regions.append(Region([(apex_x, apex_y), (0.80, base_y), (0.90, base_y)], 3))
    # Pole
    regions.append(Region([(0.69, 0.40), (0.71, 0.40), (0.71, 0.83), (0.69, 0.83)], 6))
    # Beach ball + 2 stripes
    regions.append(Region(_circle(0.50, 0.78, 0.08), 7))
    regions.append(Region([(0.42, 0.765), (0.58, 0.765), (0.58, 0.795), (0.42, 0.795)], 2))
    regions.append(Region([(0.485, 0.70), (0.515, 0.70), (0.515, 0.86), (0.485, 0.86)], 5))
    # Sand
    regions.append(Region([(0.0, 0.88), (1.0, 0.88), (1.0, 0.95), (0.0, 0.95)], 5))
    # 2 starfish + 2 shells on sand
    regions.append(Region(_star_pts(0.18, 0.95, 0.030), 1))
    regions.append(Region(_star_pts(0.82, 0.95, 0.030), 1))
    regions.append(Region(_ellipse(0.40, 0.95, 0.035, 0.022), 8))
    regions.append(Region(_ellipse(0.60, 0.95, 0.035, 0.022), 8))
    return regions


# DISABLED: needs rework — kept as code (still defined above) but excluded from pools.
#   tpl_cat         — proportions broke after stripes; profile view never settled
#   tpl_fish        — pupil + stripe + scale numbers stacked unfixably
#   tpl_beach_scene — composition read as "floating objects over a sand strip", not a beach
#   tpl_heart       — outline (2 circles + tapering bands + point) reads as an
#                     ice-cream cone, not a heart, so "Color the heart!" looked
#                     wrong against the picture. Excluded until reshaped.
TEMPLATES = {
    'easy':   [tpl_star, tpl_flower_simple, tpl_ice_cream, tpl_car, tpl_balloon],
    'medium': [tpl_butterfly, tpl_house, tpl_rocket],
    'hard':   [tpl_garden_scene, tpl_birthday_cake, tpl_cupcake],
}

# Instruction subtitle shown under the "Color by Number N" title (same style
# as the Drawing Grid prompts, e.g. "Draw a sun!"). Keyed by template
# function name. Leave a template OUT of this map (-> '') rather than guess.
CBN_SUBTITLES = {
    'tpl_star':          'Color the star!',
    'tpl_flower_simple': 'Color the flower!',
    'tpl_ice_cream':     'Color the ice cream!',
    'tpl_car':           'Color the car!',
    'tpl_balloon':       'Color the balloon!',
    'tpl_heart':         'Color the heart!',
    'tpl_butterfly':     'Color the butterfly!',
    'tpl_house':         'Color the house!',
    'tpl_rocket':        'Color the rocket!',
    'tpl_garden_scene':  'Color the garden!',
    'tpl_birthday_cake': 'Color the birthday cake!',
    'tpl_cupcake':       'Color the cupcake!',
    'tpl_fish':          'Color the fish!',
    'tpl_cat':           'Color the cat!',
    'tpl_beach_scene':   'Color the beach!',
}


# --- rendering ---------------------------------------------------------

def render_color_by_number(canvas_size, title, regions, subtitle=''):
    cw, ch = canvas_size

    # Reserve extra vertical space for the instruction subtitle when present.
    title_band  = 330 if subtitle else 200
    legend_band = 500
    margin_h    = 200
    margin_v    = 200
    line_w      = 8

    pic_area_w = cw - 2 * margin_h
    pic_area_h = ch - 2 * margin_v - title_band - legend_band
    side = min(pic_area_w, pic_area_h)
    pic_left = (cw - side) // 2
    pic_top  = margin_v + title_band + (pic_area_h - side) // 2

    img  = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    # Title + optional instruction subtitle (same style as Drawing Grid prompts)
    title_font = get_title_font(130)
    draw.text((cw // 2, margin_v + 100),
              title, anchor='mm', fill='black', font=title_font)
    if subtitle:
        draw.text((cw // 2, margin_v + 230),
                  subtitle, anchor='mm', fill='black',
                  font=get_body_font(80))

    # Pass 1: outlines (preset = solid black fill)
    for reg in regions:
        px = [(pic_left + x * side, pic_top + y * side) for (x, y) in reg.polygon]
        if reg.preset:
            draw.polygon(px, fill='black', outline='black', width=line_w)
        else:
            draw.polygon(px, outline='black', width=line_w)

    # Per-region metrics (centroid in pixels + inscribed-circle diameter in pixels)
    metrics = []
    for reg in regions:
        if reg.preset:
            continue
        cx_n, cy_n = _centroid(reg.polygon)
        r_n = _inscribed_radius(reg.polygon)
        metrics.append({
            'reg':  reg,
            'cx':   pic_left + cx_n * side,
            'cy':   pic_top  + cy_n * side,
            'diam': 2 * r_n * side,
        })

    # Place numbers in order of largest first (greedy)
    metrics.sort(key=lambda m: -m['diam'])

    # Occupied = polygon bboxes + already-placed labels (used by leader-line search)
    occupied = []
    for reg in regions:
        if reg.preset:
            continue
        pxs = [pic_left + x * side for (x, y) in reg.polygon]
        pys = [pic_top + y * side for (x, y) in reg.polygon]
        occupied.append((min(pxs), min(pys), max(pxs), max(pys)))

    pic_bounds = (pic_left, pic_top, pic_left + side, pic_top + side)

    # Pass 2: draw numbers
    for m in metrics:
        reg, cx, cy, diam = m['reg'], m['cx'], m['cy'], m['diam']
        txt = str(reg.color_id)
        if diam >= 80:
            fs = int(max(54, min(78, diam * 0.55)))
            font = get_label_font(fs)
            draw.text((cx, cy), txt, anchor='mm', fill='black', font=font)
        elif diam >= 40:
            fs = int(max(26, min(52, diam * 0.55)))
            font = get_label_font(fs)
            draw.text((cx, cy), txt, anchor='mm', fill='black', font=font)
        else:
            fs = 32
            tgt = _find_leader_target(cx, cy, fs, occupied, pic_bounds)
            if tgt is None:
                # Fallback: just put it at centroid in a smaller font
                font = get_label_font(24)
                draw.text((cx, cy), txt, anchor='mm', fill='black', font=font)
                continue
            tx, ty = tgt
            draw.line([(cx, cy), (tx, ty)], fill='black', width=2)
            draw.ellipse([(cx - 4, cy - 4), (cx + 4, cy + 4)], fill='black')
            font = get_label_font(fs)
            draw.text((tx, ty), txt, anchor='mm', fill='black', font=font)
            occupied.append((tx - fs * 0.45, ty - fs * 0.55,
                             tx + fs * 0.45, ty + fs * 0.55))

    # Legend at the bottom
    used = sorted({r.color_id for r in regions if not r.preset})
    has_preset = any(r.preset for r in regions)
    legend_top = ch - margin_v - legend_band + 40
    swatch     = 80
    n_items    = len(used) + (1 if has_preset else 0)
    cols       = 4 if n_items > 3 else max(2, n_items)
    cell_w     = (cw - 2 * margin_h) // cols
    row_h      = 120
    name_font  = get_body_font(64)
    num_font_l = get_label_font(56)
    for i, cid in enumerate(used):
        col = i % cols
        row = i // cols
        x0 = margin_h + col * cell_w + 20
        y0 = legend_top + row * row_h
        name, rgb = COLORS[cid]
        draw.rectangle([(x0, y0), (x0 + swatch, y0 + swatch)],
                       outline='black', width=4, fill=rgb)
        draw.text((x0 + swatch // 2, y0 + swatch // 2),
                  str(cid), anchor='mm', fill='white', font=num_font_l)
        draw.text((x0 + swatch + 20, y0 + swatch // 2),
                  f'= {name}', anchor='lm', fill='black', font=name_font)
    if has_preset:
        i = len(used)
        col = i % cols
        row = i // cols
        x0 = margin_h + col * cell_w + 20
        y0 = legend_top + row * row_h
        draw.rectangle([(x0, y0), (x0 + swatch, y0 + swatch)],
                       outline='black', width=4, fill='black')
        draw.text((x0 + swatch + 20, y0 + swatch // 2),
                  '= already filled', anchor='lm', fill='black', font=name_font)

    return img


def _build_color_perm(rng, used_ids):
    """Random bijection within the used color ids. Excludes identity if possible."""
    used = sorted(used_ids)
    if len(used) <= 1:
        return {c: c for c in used}
    shuffled = used[:]
    for _ in range(10):
        rng.shuffle(shuffled)
        if shuffled != used:
            break
    return dict(zip(used, shuffled))


def _build_transform(rng):
    """Geometric transform around (0.5, 0.5):
       identity 50%, h-flip 25%, ±5° rotation 15%, h-flip + rotation 10%."""
    r = rng.random()
    if r < 0.50:
        return lambda x, y: (x, y)
    if r < 0.75:
        return lambda x, y: (1.0 - x, y)
    angle = rng.uniform(-5, 5) * math.pi / 180
    cos_t, sin_t = math.cos(angle), math.sin(angle)
    if r < 0.90:
        def rot(x, y):
            dx, dy = x - 0.5, y - 0.5
            return (dx * cos_t - dy * sin_t + 0.5,
                    dx * sin_t + dy * cos_t + 0.5)
        return rot
    def flip_rot(x, y):
        dx, dy = (1.0 - x) - 0.5, y - 0.5
        return (dx * cos_t - dy * sin_t + 0.5,
                dx * sin_t + dy * cos_t + 0.5)
    return flip_rot


def generate_color_by_number_image(difficulty: str, seed: int, title: str,
                                   canvas_size=(2625, 3375)):
    pool = TEMPLATES.get(difficulty, TEMPLATES['medium'])
    rng = random.Random(seed)
    # Deterministic rotation through the pool → consecutive CbN pages get
    # DIFFERENT base templates (color perm + transform still randomized below).
    fn = pool[seed % len(pool)]
    subtitle = CBN_SUBTITLES.get(fn.__name__, '')
    base_regions = fn()
    used = {r.color_id for r in base_regions if not r.preset}
    perm = _build_color_perm(rng, used)
    transform = _build_transform(rng)
    regions = [Region(
        polygon=[transform(x, y) for (x, y) in r.polygon],
        color_id=r.color_id if r.preset else perm[r.color_id],
        preset=r.preset,
    ) for r in base_regions]
    return render_color_by_number(canvas_size, title, regions,
                                  subtitle=subtitle)
