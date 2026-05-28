"""
Assemble a publishable activity book PDF from generated activity pages.

Book structure (in order):
  1. Half-title page (title only — the real cover is a separate KDP upload)
  2. Copyright page
  3. How to Use This Book (intro)
  4. Table of Contents (auto, sorted by first-appearance page)
  5. ... activity pages in the supplied order ...
  Last. "Great Job!" certificate-style closing page

KDP layout (no bleed — nothing in this book bleeds off the trim edge):
  - Page size: exactly 8.5" x 11"  ->  612 x 792 pt  ->  2550 x 3300 px @300DPI
  - Mirrored margins by PHYSICAL page side:
        gutter (inside) 0.5",  outside 0.4",  top 0.4",  bottom band 0.8"
        odd physical page  = right-hand = gutter on LEFT
        even physical page = left-hand  = gutter on RIGHT
  - Page numbers sit 0.5" above the bottom trim edge (>= KDP min 0.375").
  - Content is generated directly at the live-area size, then placed with the
    parity offset — the page is NOT stretched/resized.

Page numbering (printed bottom-center, Andika 16pt, embedded subset):
  - half-title, copyright, closing -> unnumbered
  - intro -> roman "i", TOC -> roman "ii"
  - activity pages -> arabic 1, 2, 3, ...

NOTE: no answer key — preschool activities (age 3-5) don't need one.
"""
import math
import os
import re
import shutil
import tempfile
from collections import OrderedDict
from pathlib import Path
from typing import List

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font, get_label_font


# --- page geometry (no bleed) ----------------------------------------
KDP_DPI    = 300
PAGE_W_IN  = 8.5
PAGE_H_IN  = 11.0
PAGE_W_PX  = int(PAGE_W_IN * KDP_DPI)   # 2550
PAGE_H_PX  = int(PAGE_H_IN * KDP_DPI)   # 3300
PAGE_W_PT  = PAGE_W_IN * 72             # 612
PAGE_H_PT  = PAGE_H_IN * 72             # 792

# Mirrored margins (px @300). Use values comfortably above the KDP minimums
# (gutter min 0.375", others min 0.25") so validation passes with margin.
GUTTER_PX  = int(0.50 * KDP_DPI)   # 150  inside / gutter
OUTSIDE_PX = int(0.40 * KDP_DPI)   # 120  outside edge
TOP_PX     = int(0.40 * KDP_DPI)   # 120  top
BOTTOM_PX  = int(0.80 * KDP_DPI)   # 240  bottom band (incl. page-number zone)

# Live content area the generators draw into.
CONTENT_W  = PAGE_W_PX - GUTTER_PX - OUTSIDE_PX   # 2280
CONTENT_H  = PAGE_H_PX - TOP_PX - BOTTOM_PX       # 2940

# Page number baseline: 0.5" above bottom trim (>= 0.375" KDP min).
PAGENUM_FROM_BOTTOM_PT = 0.5 * 72   # 36 pt

KDP_MAX_MB = 650


def _draw_filled_star(draw, cx, cy, r, color='black'):
    """5-point filled star polygon — font-independent."""
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang),
                    cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=color, outline=color)


# Filename pattern emitted by activity.py: e.g. "001_maze_3.png"
_FILENAME_RE = re.compile(r'^(\d+)_([a-z]+)(?:_.*)?\.png$', re.IGNORECASE)

SECTION_NAMES = {
    'maze':       'Prompt Paths',
    'sudoku':     'Constraints',
    'wordsearch': 'Find the Keywords',
    'magic':      'Balance the Grid',
    'dotgrid':    'Draw the Output',
    'counting':   'Count the Tokens',
    'pattern':    'Loop It',
    'symmetry':   'Mirror Functions',
    'pathsum':    'Accumulators',
    'mathmaze':   'Decision Trees',
}

# Honest-TOC: fixed display order + friendly labels. Counts are computed
# dynamically from the actual generated pages; 0-count types are skipped,
# so the TOC adapts to whatever mix/quantities the user picks.
TOC_ORDER = ['maze', 'pattern', 'symmetry', 'mathmaze', 'pathsum',
             'sudoku', 'magic', 'counting', 'wordsearch', 'dotgrid']
TOC_LABELS = {
    'maze':       'Prompt Paths',
    'pattern':    'Loop It',
    'symmetry':   'Mirror Functions',
    'mathmaze':   'Decision Trees',
    'pathsum':    'Accumulators',
    'sudoku':     'Constraints',
    'magic':      'Balance the Grid',
    'counting':   'Count the Tokens',
    'wordsearch': 'Find the Keywords',
    'dotgrid':    'Draw the Output',
}


# --- helpers ----------------------------------------------------------

def _content_page():
    """Blank image at the live-area size (what generators draw onto)."""
    return Image.new('RGB', (CONTENT_W, CONTENT_H), 'white')


def _wrap(text, font, max_w, draw):
    words = text.split()
    lines, cur = [], ''
    for w in words:
        candidate = (cur + ' ' + w).strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    return lines


def _section_key(filename: str) -> str:
    m = _FILENAME_RE.match(os.path.basename(filename))
    if m:
        return m.group(2).lower()
    return 'coloring'


def _roman(n: int) -> str:
    vals = [(1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'),
            (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'),
            (10, 'x'), (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')]
    out = ''
    for v, s in vals:
        while n >= v:
            out += s
            n -= v
    return out


# --- front/back matter (rendered at CONTENT_W x CONTENT_H) ------------

def render_dedication_page(metadata: dict) -> Image.Image:
    """Dedication / ownership page (replaces the redundant cover-repeat).
    All labels centered, three identical 4-inch writing lines, the group
    centered in the upper-middle of the page."""
    img = _content_page()
    draw = ImageDraw.Draw(img)
    cx = CONTENT_W // 2
    f = get_body_font(86)
    line_w = 4 * KDP_DPI                 # exactly 4 inches at 300 DPI
    labels = ['This book belongs to:', 'Age:', 'Started on:']
    LBL_TO_LINE = 150                    # label top -> writing line
    BLOCK_GAP = 250                      # writing line -> next label (uniform)
    total = 3 * LBL_TO_LINE + 2 * BLOCK_GAP
    y = int(CONTENT_H * 0.40) - total // 2
    for lbl in labels:
        draw.text((cx, y), lbl, anchor='mt', fill='black', font=f)
        y += LBL_TO_LINE
        draw.line([(cx - line_w // 2, y), (cx + line_w // 2, y)],
                  fill='black', width=5)
        y += BLOCK_GAP
    return img


def render_copyright_page(metadata: dict) -> Image.Image:
    img = _content_page()
    draw = ImageDraw.Draw(img)
    cx = CONTENT_W // 2
    body = get_body_font(70)
    small = get_body_font(52)
    year = metadata.get('year', 2026)
    author = (metadata.get('author') or '').strip() or '[Your Name]'
    draw.text((cx, CONTENT_H // 2 - 90),
              f'© {year} {author}. All rights reserved.',
              anchor='mm', fill='black', font=body)
    draw.text((cx, CONTENT_H // 2 + 50), 'For personal use only.',
              anchor='mm', fill=(80, 80, 80), font=small)
    age = (metadata.get('age_range') or '').strip()
    # Only show the "under 5" note for books that actually target under-5s.
    young = age.startswith('3') or age.startswith('4') or age in ('0-5', '2-4')
    if young:
        draw.text((cx, CONTENT_H // 2 + 130),
                  'Adult supervision recommended for children under 5.',
                  anchor='mm', fill=(80, 80, 80), font=small)
    return img


def render_intro_page(metadata: dict, toc_rows: list) -> Image.Image:
    """How to Use This Book — series-aware, single-page adaptive.

    If metadata carries 'chapter_intros' (from a series preset), list the
    activity TYPES actually present in this volume (derived from toc_rows),
    each with its one-line intro. Font sizes and spacing scale DOWN as the
    number of types grows, so every type always fits on one page (no silent
    truncation). Otherwise fall back to a neutral, honest blurb.
    """
    img = _content_page()
    draw = ImageDraw.Draw(img)
    cx = CONTENT_W // 2
    tfont = get_title_font(150)

    draw.text((cx, 200), 'How to Use This Book',
              anchor='mt', fill='black', font=tfont)

    intros = metadata.get('chapter_intros') or {}

    # Map a TOC label back to its activity key so we can fetch the right intro.
    label_to_key = {}
    for k, lbl in TOC_LABELS.items():
        label_to_key.setdefault(lbl, k)
    for k, lbl in SECTION_NAMES.items():
        label_to_key.setdefault(lbl, k)

    if not intros:
        # Neutral fallback (manual mode) — NO mention of specific activity
        # types or of children under 5. Honest and generic.
        bfont = get_body_font(60)
        description = (
            "This book is full of puzzles that build focus, problem-solving, "
            "and fine-motor skills. Pages can be done in any order.\n\n"
            "Sit with your child for the first few — show them where to start "
            "and praise effort over perfection.\n\n"
            "Use a soft pencil so mistakes are easy to fix. Have fun!"
        )
        y = 560
        for para in description.split('\n\n'):
            for line in _wrap(para, bfont, CONTENT_W - 200, draw):
                draw.text((cx, y), line, anchor='mt', fill='black', font=bfont)
                y += 100
            y += 60
        return img

    # --- series mode: pre-measure, then scale to fit one page -------------
    # Vertical budget for the body (between header and bottom margin).
    body_top = 470
    body_bottom = CONTENT_H - 200          # leave room for the closing tip
    avail = body_bottom - body_top

    rows = [(label, label_to_key.get(label),
             intros.get(label_to_key.get(label), '')) for label, _c in toc_rows]
    n = max(1, len(rows))

    # Scale factor by type-count. 6 types -> full size; shrink as n grows.
    # Tuned so 10 types fit comfortably with the tip still on-page.
    scale = 1.0
    if n >= 7:
        scale = 0.92
    if n >= 8:
        scale = 0.82
    if n >= 9:
        scale = 0.74
    if n >= 10:
        scale = 0.68

    def S(v):  # scaled int, with a sane floor
        return max(34, int(round(v * scale)))

    lead_font = get_body_font(S(64))
    name_font = get_body_font(S(66))     # type name
    blurb_font = get_body_font(S(58))    # intro sentence
    tip_font = get_body_font(S(60))

    # Spacing, also scaled.
    lead_lh = S(88)
    name_lh = S(92)
    blurb_lh = S(76)
    gap_after_lead = S(50)
    gap_after_blurb = S(46)

    # Helper: measure total body height for the current sizes.
    def measure():
        h = 0
        lead = ("Each kind of puzzle teaches one way of thinking. "
                "Here's what's inside and why it matters:")
        h += len(_wrap(lead, lead_font, CONTENT_W - 220, draw)) * lead_lh
        h += gap_after_lead
        for label, key, blurb in rows:
            h += name_lh
            if blurb:
                h += len(_wrap(blurb, blurb_font, CONTENT_W - 340, draw)) * blurb_lh
            h += gap_after_blurb
        return h

    # If still too tall after the count-based scale, shrink iteratively.
    guard = 0
    while measure() > avail and guard < 12:
        scale *= 0.94
        lead_font = get_body_font(S(64))
        name_font = get_body_font(S(66))
        blurb_font = get_body_font(S(58))
        tip_font = get_body_font(S(60))
        lead_lh = S(88); name_lh = S(92); blurb_lh = S(76)
        gap_after_lead = S(50); gap_after_blurb = S(46)
        guard += 1

    # --- draw ---------------------------------------------------------------
    y = body_top
    lead = ("Each kind of puzzle teaches one way of thinking. "
            "Here's what's inside and why it matters:")
    for line in _wrap(lead, lead_font, CONTENT_W - 220, draw):
        draw.text((cx, y), line, anchor='mt', fill='black', font=lead_font)
        y += lead_lh
    y += gap_after_lead

    for label, key, blurb in rows:
        draw.text((150, y), label, anchor='lt', fill='black', font=name_font)
        y += name_lh
        if blurb:
            for line in _wrap(blurb, blurb_font, CONTENT_W - 340, draw):
                draw.text((230, y), line, anchor='lt',
                          fill=(70, 70, 70), font=blurb_font)
                y += blurb_lh
        y += gap_after_blurb

    # Closing tip — always on-page.
    tip = "Use a soft pencil so mistakes are easy to fix. Have fun!"
    y = min(y + S(20), CONTENT_H - 150)
    for line in _wrap(tip, tip_font, CONTENT_W - 220, draw):
        draw.text((cx, y), line, anchor='mt', fill='black', font=tip_font)
        y += S(88)
    return img


def render_toc_page(toc_rows: list) -> Image.Image:
    """Honest TOC: activities are interleaved, so we list TYPES with their
    real counts (no misleading per-section page numbers).

    toc_rows: ordered list of (label, count) for types with count > 0.
    """
    img = _content_page()
    draw = ImageDraw.Draw(img)
    cx = CONTENT_W // 2
    draw.text((cx, 220), 'Table of Contents',
              anchor='mt', fill='black', font=get_title_font(150))

    draw.text((120, 540), 'Activities in this book:', anchor='lt',
              fill='black', font=get_body_font(64))

    y_start = 720
    y_end_max = CONTENT_H - 360       # leave room for the closing note
    n = max(1, len(toc_rows))
    entry_size, line_h = 74, 150
    while n * line_h > (y_end_max - y_start) and entry_size > 40:
        entry_size = max(40, int(entry_size * 0.9))
        line_h = max(86, int(line_h * 0.9))

    entry_font = get_body_font(entry_size)
    left_x = 120
    right_x = CONTENT_W - 120
    y = y_start
    for label, count in toc_rows:
        draw.text((left_x, y), label, anchor='lt',
                  fill='black', font=entry_font)
        amount = f'{count} activit{"y" if count == 1 else "ies"}'
        draw.text((right_x, y), amount, anchor='rt',
                  fill='black', font=entry_font)
        name_w = draw.textbbox((0, 0), label, font=entry_font)[2]
        amt_w = draw.textbbox((0, 0), amount, font=entry_font)[2]
        dots_start = left_x + name_w + 40
        dots_end = right_x - amt_w - 40
        dy = y + int(entry_size * 0.85)
        if dots_end > dots_start + 50:
            for dx in range(dots_start, dots_end, 30):
                draw.ellipse([(dx, dy - 4), (dx + 8, dy + 2)],
                             fill=(140, 140, 140))
        y += line_h

    y += 70
    for ln in ('Activities are mixed throughout the book —',
               'flip to any page and have fun!'):
        draw.text((cx, y), ln, anchor='mt', fill=(90, 90, 90),
                  font=get_body_font(58))
        y += 90
    return img


def render_great_job_page() -> Image.Image:
    img = _content_page()
    draw = ImageDraw.Draw(img)
    cx = CONTENT_W // 2
    cy = CONTENT_H // 2
    draw.text((cx, cy - 620), 'Great Job!',
              anchor='mm', fill='black', font=get_title_font(330))
    bx0, by0 = 120, cy - 320
    bx1, by1 = CONTENT_W - 120, cy + 520
    draw.rectangle([(bx0, by0), (bx1, by1)], outline='black', width=10)
    draw.rectangle([(bx0 + 30, by0 + 30), (bx1 - 30, by1 - 30)],
                   outline='black', width=4)
    draw.text((cx, cy - 180), 'This book was completed by:',
              anchor='mm', fill='black', font=get_body_font(100))
    line_w = bx1 - bx0 - 300
    name_y = cy - 20
    draw.line([(cx - line_w // 2, name_y), (cx + line_w // 2, name_y)],
              fill='black', width=6)
    draw.text((cx, name_y + 80), '(your name)',
              anchor='mm', fill=(150, 150, 150), font=get_body_font(72))
    star_r = 60
    spacing = int(star_r * 3.2)
    star_y = by1 - 170
    for i in range(5):
        _draw_filled_star(draw, cx + (i - 2) * spacing, star_y, star_r)
    return img


# --- answer key (Etap 2B) ---------------------------------------------

# Types whose solution we can render in the answer key. Easy types print a
# value/text/filled-grid; hard types (maze, pathsum, mathmaze, wordsearch) shade
# the solution cells gray under the grid/letters/walls.
_KEY_RENDERABLE = {'counting', 'pattern', 'sudoku', 'magic',
                   'pathsum', 'mathmaze', 'wordsearch', 'maze'}

_PATH_FILL = (210, 210, 210)  # light gray highlight for solution cells


def _load_solutions(pages):
    """Dla listy ścieżek PNG zwróć listę solution-dictów (z tych, które mają .json).
    Zachowuje kolejność stron. Pomija strony bez sidecar."""
    import json
    sols = []
    for p in pages:
        side = str(p).rsplit('.', 1)[0] + '.json'
        if os.path.exists(side):
            try:
                with open(side, encoding='utf-8') as f:
                    sols.append(json.load(f))
            except Exception:
                pass
    return sols


def _draw_mini_grid(draw, grid, left, top, cell, font, line_w=4):
    """Draw a filled N×M grid with digits centred in each cell."""
    n_rows = len(grid)
    n_cols = len(grid[0])
    for i in range(n_rows + 1):
        y = top + i * cell
        draw.line([(left, y), (left + n_cols * cell, y)], fill='black', width=line_w)
    for j in range(n_cols + 1):
        x = left + j * cell
        draw.line([(x, top), (x, top + n_rows * cell)], fill='black', width=line_w)
    for r in range(n_rows):
        for c in range(n_cols):
            draw.text((left + c * cell + cell // 2, top + r * cell + cell // 2),
                      str(grid[r][c]), anchor='mm', fill='black', font=font)


def _draw_grid_with_path(draw, grid, path_cells, left, top, cell,
                         font, line_w=3):
    """Mini number/letter grid with solution cells shaded gray. path_cells: set of (r,c)."""
    n_rows, n_cols = len(grid), len(grid[0])
    # 1) gray fill on path cells first
    for (r, c) in path_cells:
        x0 = left + c * cell; y0 = top + r * cell
        draw.rectangle([(x0, y0), (x0 + cell, y0 + cell)], fill=_PATH_FILL)
    # 2) grid lines
    for i in range(n_rows + 1):
        y = top + i * cell
        draw.line([(left, y), (left + n_cols * cell, y)], fill='black', width=line_w)
    for j in range(n_cols + 1):
        x = left + j * cell
        draw.line([(x, top), (x, top + n_rows * cell)], fill='black', width=line_w)
    # 3) digits / letters
    for r in range(n_rows):
        for c in range(n_cols):
            draw.text((left + c * cell + cell // 2, top + r * cell + cell // 2),
                      str(grid[r][c]), anchor='mm', fill='black', font=font)


def _draw_mini_maze(draw, walls, path_cells, left, top, cell, line_w=2):
    """Mini maze: shade solution cells gray, then draw walls on top."""
    rows, cols = len(walls), len(walls[0])
    for (r, c) in path_cells:
        x0 = left + c * cell; y0 = top + r * cell
        draw.rectangle([(x0, y0), (x0 + cell, y0 + cell)], fill=_PATH_FILL)
    for r in range(rows):
        for c in range(cols):
            x0 = left + c * cell; y0 = top + r * cell
            x1 = x0 + cell; y1 = y0 + cell
            w = walls[r][c]
            if w[0]: draw.line([(x0, y0), (x1, y0)], fill='black', width=line_w)
            if w[1]: draw.line([(x1, y0), (x1, y1)], fill='black', width=line_w)
            if w[2]: draw.line([(x0, y1), (x1, y1)], fill='black', width=line_w)
            if w[3]: draw.line([(x0, y0), (x0, y1)], fill='black', width=line_w)


def _wordsearch_cells(placements):
    """Set of (r,c) cells covered by placed words (for highlighting)."""
    cells = set()
    for p in placements:
        word, r, c, dr, dc = p[0], p[1], p[2], p[3], p[4]
        for i in range(len(word)):
            cells.add((r + dr * i, c + dc * i))
    return cells


def render_answer_key_pages(solutions):
    """Return a list of CONTENT-sized 'Answers' pages for all renderable types
    (counting, pattern, sudoku, magic, pathsum, mathmaze, wordsearch, maze).
    Number/letter/maze grids shade the solution cells gray. Overflows onto extra
    pages as needed. Types without a sidecar are simply absent from `solutions`."""
    order_idx = {k: i for i, k in enumerate(TOC_ORDER)}
    items = [s for s in solutions if s.get('type') in _KEY_RENDERABLE]
    items.sort(key=lambda s: (order_idx.get(s.get('type'), 99), s.get('n', 0)))
    if not items:
        return []

    title_font = get_title_font(150)
    head_font  = get_body_font(80)
    label_font = get_body_font(60)
    cap_font   = get_body_font(48)
    grid_font  = get_body_font(46)

    margin = 150
    bottom = CONTENT_H - 160

    pages = []
    state = {}

    def start_page(first):
        img = _content_page()
        d = ImageDraw.Draw(img)
        if first:
            d.text((CONTENT_W // 2, 200), 'Answers',
                   anchor='mt', fill='black', font=title_font)
            state['y'] = 470
        else:
            d.text((CONTENT_W // 2, 170), 'Answers (continued)',
                   anchor='mt', fill='black', font=head_font)
            state['y'] = 360
        state['img'] = img
        state['draw'] = d

    def ensure(h):
        if state['y'] + h > bottom:
            pages.append(state['img'])
            start_page(False)

    start_page(True)

    from itertools import groupby
    for t, grp in groupby(items, key=lambda s: s['type']):
        grp = list(grp)
        if t == 'counting':
            for s in grp:
                ensure(80)
                state['draw'].text(
                    (margin, state['y']),
                    f"{s.get('title')}: {s['data'].get('count')}",
                    anchor='lt', fill='black', font=label_font)
                state['y'] += 80
        elif t == 'pattern':
            for s in grp:
                line = f"{s.get('title')}: " + ', '.join(s['data'].get('answers', []))
                lines = _wrap(line, label_font, CONTENT_W - 2 * margin, state['draw'])
                ensure(len(lines) * 72 + 16)
                for ln in lines:
                    state['draw'].text((margin, state['y']), ln,
                                       anchor='lt', fill='black', font=label_font)
                    state['y'] += 72
                state['y'] += 16
        elif t in ('pathsum', 'mathmaze'):  # number grids, 3 per row, path shaded
            cols = 3
            col_w = (CONTENT_W - 2 * margin) // cols
            for i in range(0, len(grp), cols):
                row = grp[i:i + cols]
                prep, row_h = [], 0
                for s in row:
                    grid = s['data']['grid']
                    gsize = len(grid)
                    cell = min((col_w - 40) // gsize, 70)
                    pcells = {tuple(rc) for rc in s['data'].get('path', [])}
                    prep.append((grid, cell, pcells, s))
                    row_h = max(row_h, 60 + gsize * cell + 50)
                ensure(row_h)
                ytop = state['y']
                for j, (grid, cell, pcells, s) in enumerate(prep):
                    x = margin + j * col_w
                    cap = s.get('title')
                    if t == 'mathmaze':
                        rule, param = s['data'].get('rule'), s['data'].get('param')
                        if rule == 'multiple' and param:
                            cap = f"{cap} (×{param})"
                        elif rule in ('even', 'odd'):
                            cap = f"{cap} ({rule})"
                    state['draw'].text((x, ytop), cap, anchor='lt',
                                       fill='black', font=cap_font)
                    _draw_grid_with_path(state['draw'], grid, pcells,
                                         x, ytop + 60, cell, grid_font)
                state['y'] = ytop + row_h
        elif t == 'wordsearch':  # letter grids, 2 per row, words shaded
            cols = 2
            col_w = (CONTENT_W - 2 * margin) // cols
            for i in range(0, len(grp), cols):
                row = grp[i:i + cols]
                prep, row_h = [], 0
                for s in row:
                    grid = s['data']['grid']
                    gsize = len(grid)
                    cell = (col_w - 40) // gsize
                    wcells = _wordsearch_cells(s['data'].get('placements', []))
                    wsfont = get_body_font(max(28, min(int(cell * 0.6), 56)))
                    prep.append((grid, cell, wcells, wsfont, s))
                    row_h = max(row_h, 60 + gsize * cell + 50)
                ensure(row_h)
                ytop = state['y']
                for j, (grid, cell, wcells, wsfont, s) in enumerate(prep):
                    x = margin + j * col_w
                    state['draw'].text((x, ytop), s.get('title'), anchor='lt',
                                       fill='black', font=cap_font)
                    _draw_grid_with_path(state['draw'], grid, wcells,
                                         x, ytop + 60, cell, wsfont)
                state['y'] = ytop + row_h
        elif t == 'maze':  # maze walls, 2 per row, path shaded
            cols = 2
            col_w = (CONTENT_W - 2 * margin) // cols
            for i in range(0, len(grp), cols):
                row = grp[i:i + cols]
                prep, row_h = [], 0
                for s in row:
                    walls = s['data']['walls']
                    mrows, mcols = s['data']['rows'], s['data']['cols']
                    cell = (col_w - 40) // mcols
                    pcells = {tuple(rc) for rc in s['data'].get('path', [])}
                    prep.append((walls, cell, mrows, pcells, s))
                    row_h = max(row_h, 60 + mrows * cell + 50)
                ensure(row_h)
                ytop = state['y']
                for j, (walls, cell, mrows, pcells, s) in enumerate(prep):
                    x = margin + j * col_w
                    state['draw'].text((x, ytop), s.get('title'), anchor='lt',
                                       fill='black', font=cap_font)
                    _draw_mini_maze(state['draw'], walls, pcells,
                                    x, ytop + 60, cell)
                state['y'] = ytop + row_h
        else:  # sudoku / magic — pack grids 3 per row
            cols = 3
            col_w = (CONTENT_W - 2 * margin) // cols
            for i in range(0, len(grp), cols):
                row = grp[i:i + cols]
                cells, row_h = [], 0
                for s in row:
                    grid = s['data']['solved'] if t == 'sudoku' else s['data']['full']
                    gsize = len(grid)
                    cell = min((col_w - 40) // gsize, 70)
                    cells.append((grid, cell))
                    row_h = max(row_h, 60 + gsize * cell + 50)
                ensure(row_h)
                ytop = state['y']
                for j, s in enumerate(row):
                    grid, cell = cells[j]
                    x = margin + j * col_w
                    if t == 'sudoku':
                        cap = s.get('title')
                    else:
                        cap = f"{s.get('title')} (= {s['data'].get('magic_sum')})"
                    state['draw'].text((x, ytop), cap, anchor='lt',
                                       fill='black', font=cap_font)
                    _draw_mini_grid(state['draw'], grid, x, ytop + 60,
                                    cell, grid_font)
                state['y'] = ytop + row_h

    pages.append(state['img'])
    return pages


# --- TOC computation (sorted by first-appearance page) ----------------

def _compute_toc(activity_entries):
    """Count activity pages per type and return ordered (label, count) rows.

    activity_entries: ordered list of (png_path, visible_label_str).

    Counts are dynamic (whatever quantities the user generated). Rows follow
    the fixed TOC_ORDER; any type with 0 pages is skipped. Unknown types are
    appended (alphabetically) using SECTION_NAMES.
    """
    counts = {}
    for path, _label in activity_entries:
        key = _section_key(path)
        counts[key] = counts.get(key, 0) + 1
    ordered = [k for k in TOC_ORDER if counts.get(k)]
    extra = sorted(k for k in counts if k not in TOC_ORDER)
    rows = []
    for key in ordered + extra:
        label = TOC_LABELS.get(key) or SECTION_NAMES.get(key, key.title())
        rows.append((label, counts[key]))
    return rows


# --- composition ------------------------------------------------------

def _fit_to_content(im: Image.Image) -> Image.Image:
    """Return an RGB image exactly CONTENT_W x CONTENT_H. If the source is a
    different size, fit it (preserve aspect) centered on white — no distortion.
    """
    im = im.convert('RGB')
    if im.size == (CONTENT_W, CONTENT_H):
        return im
    canvas = Image.new('RGB', (CONTENT_W, CONTENT_H), 'white')
    s = min(CONTENT_W / im.width, CONTENT_H / im.height)
    new = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))),
                    Image.LANCZOS)
    canvas.paste(new, ((CONTENT_W - new.width) // 2,
                       (CONTENT_H - new.height) // 2))
    return canvas


def _compose_page(content_img: Image.Image, phys_index: int) -> Image.Image:
    """Place the live-area content onto a full 2550x3300 page with the
    correct mirrored-margin offset for this physical page.
    phys_index is 1-based; odd = right-hand (gutter LEFT)."""
    page = Image.new('RGB', (PAGE_W_PX, PAGE_H_PX), 'white')
    x_off = GUTTER_PX if (phys_index % 2 == 1) else OUTSIDE_PX
    page.paste(_fit_to_content(content_img), (x_off, TOP_PX))
    return page


# --- main entry point -------------------------------------------------

def build_activity_book(pages: List[str], metadata: dict,
                        output_pdf_path: str,
                        jlog_fn=None) -> dict:
    """Assemble the full activity book PDF (8.5x11, no bleed)."""
    from reportlab.pdfgen import canvas as rl_canvas

    issues = []

    def log(m):
        if jlog_fn:
            jlog_fn(m)

    log(f'Source: {len(pages)} activity pages')

    tmpdir = Path(tempfile.mkdtemp(prefix='book_'))

    def save_tmp(name, im):
        p = tmpdir / f'{name}.png'
        im.convert('RGB').save(str(p), dpi=(KDP_DPI, KDP_DPI))
        return str(p)

    # Assign the real visible labels to activity pages first.
    activity_entries = []          # (path, visible_label_str)
    for i, p in enumerate(pages, 1):
        activity_entries.append((p, str(i)))

    toc_rows = _compute_toc(activity_entries)
    log(f'   Sections: {[(lbl, f"x{cnt}") for lbl, cnt in toc_rows]}')

    half_p  = save_tmp('00_dedication', render_dedication_page(metadata))
    copy_p  = save_tmp('01_copyright',  render_copyright_page(metadata))
    intro_p = save_tmp('02_intro',      render_intro_page(metadata, toc_rows))
    toc_p   = save_tmp('03_toc',        render_toc_page(toc_rows))
    great_p = save_tmp('99_greatjob',   render_great_job_page())

    # (path, page_label_or_none).  None = unnumbered.
    all_pages = [
        (half_p,  None),
        (copy_p,  None),
        (intro_p, _roman(1)),   # 'i'
        (toc_p,   _roman(2)),   # 'ii'
    ]
    all_pages.extend(activity_entries)

    # Answer key (solutions collected from sidecar JSON next to the PNGs).
    solutions = _load_solutions(pages)
    if solutions:
        key_imgs = render_answer_key_pages(solutions)
        for i, kimg in enumerate(key_imgs):
            kp = save_tmp(f'90_answers_{i:02d}', kimg)
            all_pages.append((kp, None))   # klucz: strony nienumerowane (jak oprawa)

    all_pages.append((great_p, None))

    # No blank padding — the caller supplies enough activities. Guarantee an
    # even page count by appending ONE extra blank only if unavoidable.
    if len(all_pages) % 2 == 1:
        blank = save_tmp('zz_blank', _content_page())
        all_pages.insert(len(all_pages) - 1, (blank, None))
        issues.append('odd page count — appended 1 blank to make it even')

    log(f'Total pages: {len(all_pages)}')

    # --- PDF assembly: 612x792 pt, page numbers, embedded Andika ------
    c = rl_canvas.Canvas(str(output_pdf_path), pagesize=(PAGE_W_PT, PAGE_H_PT))
    c.setAuthor((metadata.get('author') or '').strip() or '[Your Name]')
    c.setTitle(metadata.get('title', 'Activity Book'))

    font_path = Path(__file__).resolve().parent / 'data' / 'fonts' / 'Andika-Regular.ttf'
    page_font_name = 'Helvetica'
    if font_path.exists():
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            pdfmetrics.registerFont(TTFont('Andika', str(font_path)))
            page_font_name = 'Andika'
        except Exception:
            pass

    for phys_index, (path, label) in enumerate(all_pages, 1):
        try:
            composed = _compose_page(Image.open(path), phys_index)
            comp_path = tmpdir / f'_pg_{phys_index:03d}.png'
            composed.save(str(comp_path), dpi=(KDP_DPI, KDP_DPI))
            c.drawImage(str(comp_path), 0, 0,
                        width=PAGE_W_PT, height=PAGE_H_PT,
                        preserveAspectRatio=False)
        except Exception as e:
            issues.append(f'compose/draw failed p{phys_index}: {e}')
            c.setFillColorRGB(1, 1, 1)
            c.rect(0, 0, PAGE_W_PT, PAGE_H_PT, fill=1, stroke=0)
        if label is not None:
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.setFont(page_font_name, 16)
            c.drawCentredString(PAGE_W_PT / 2, PAGENUM_FROM_BOTTOM_PT, label)
        c.showPage()
    c.save()
    log('PDF written')

    # --- MediaBox (no bleed) + Helvetica->Andika subset via pypdf -----
    try:
        import pypdf
        from pypdf.generic import NameObject
        reader = pypdf.PdfReader(str(output_pdf_path))
        writer = pypdf.PdfWriter()
        for src_page in reader.pages:
            writer.add_page(src_page)
            page = writer.pages[-1]
            page.mediabox.lower_left = (0, 0)
            page.mediabox.upper_right = (PAGE_W_PT, PAGE_H_PT)
            # No bleed: drop TrimBox/BleedBox so they default to MediaBox.
            for box in ('/TrimBox', '/BleedBox', '/CropBox', '/ArtBox'):
                if box in page:
                    del page[NameObject(box)]

        STANDARD = {
            '/Helvetica', '/Helvetica-Bold', '/Helvetica-Oblique',
            '/Helvetica-BoldOblique', '/Times-Roman', '/Times-Bold',
            '/Times-Italic', '/Times-BoldItalic', '/Courier',
            '/Courier-Bold', '/Courier-Oblique', '/Courier-BoldOblique',
            '/Symbol', '/ZapfDingbats',
        }
        andika_font_obj = None
        for page in writer.pages:
            res = page.get('/Resources')
            if hasattr(res, 'get_object'):
                res = res.get_object()
            fd = res.get('/Font') if res else None
            if hasattr(fd, 'get_object'):
                fd = fd.get_object()
            if not fd:
                continue
            for _, v in fd.items():
                v_r = v.get_object() if hasattr(v, 'get_object') else v
                bf = str(v_r.get('/BaseFont', ''))
                if bf and bf not in STANDARD:
                    andika_font_obj = v
                    break
            if andika_font_obj is not None:
                break
        if andika_font_obj is not None:
            for page in writer.pages:
                res = page.get('/Resources')
                if hasattr(res, 'get_object'):
                    res = res.get_object()
                fd = res.get('/Font') if res else None
                if hasattr(fd, 'get_object'):
                    fd = fd.get_object()
                if not fd:
                    continue
                for key in list(fd.keys()):
                    v = fd[key]
                    v_r = v.get_object() if hasattr(v, 'get_object') else v
                    if str(v_r.get('/BaseFont', '')) in STANDARD:
                        fd[NameObject(key)] = andika_font_obj

        # PDF version >= 1.4
        try:
            writer.pdf_header = b'%PDF-1.7'
        except Exception:
            try:
                writer._header = b'%PDF-1.7'
            except Exception:
                pass

        with open(str(output_pdf_path), 'wb') as f:
            writer.write(f)
        log('MediaBox set (no bleed), fonts embedded (Andika subset), PDF 1.7')
    except Exception as e:
        issues.append(f'pypdf: {e}')

    try:
        shutil.rmtree(str(tmpdir))
    except Exception:
        pass

    file_size_mb = os.path.getsize(str(output_pdf_path)) / 1024 / 1024
    validation_issues = list(issues)
    if file_size_mb > KDP_MAX_MB:
        validation_issues.append(
            f'file size {file_size_mb:.1f} MB exceeds KDP max {KDP_MAX_MB} MB')
    try:
        import pypdf
        reader = pypdf.PdfReader(str(output_pdf_path))
        for i, page in enumerate(reader.pages, 1):
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            if abs(w - PAGE_W_PT) > 1 or abs(h - PAGE_H_PT) > 1:
                validation_issues.append(
                    f'page {i} size {w:.0f}x{h:.0f} pt != {PAGE_W_PT:.0f}x{PAGE_H_PT:.0f}')
                break
    except Exception:
        pass

    return {
        'pdf_path':     str(output_pdf_path),
        'total_pages':  len(all_pages),
        'file_size_mb': round(file_size_mb, 2),
        'validation': {
            'ok':     len(validation_issues) == 0,
            'issues': validation_issues,
        },
        'sections': [(lbl, cnt) for (lbl, cnt) in toc_rows],
    }
