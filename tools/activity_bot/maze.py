"""
Maze generation for KDP Activity Book.
Recursive backtracking algorithm + PIL rendering.
"""
import random

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_label_font
from .layout import compute_activity_box, title_position

# (rows, cols, line_width_px)
DIFFICULTY_PRESETS = {
    'easy':   (10, 15, 12),
    'medium': (16, 22, 9),
    'hard':   (22, 32, 6),
}

# Walls per cell: 0=N, 1=E, 2=S, 3=W
_OPPOSITE = (2, 3, 0, 1)


def generate_maze(rows: int, cols: int, seed: int = 0):
    """Recursive-backtracking maze. Returns walls[r][c] = [N, E, S, W] booleans."""
    walls = [[[True, True, True, True] for _ in range(cols)] for _ in range(rows)]
    visited = [[False] * cols for _ in range(rows)]
    rng = random.Random(seed)

    def neighbors(r, c):
        out = []
        if r > 0:        out.append((r - 1, c, 0))  # N
        if c < cols - 1: out.append((r, c + 1, 1))  # E
        if r < rows - 1: out.append((r + 1, c, 2))  # S
        if c > 0:        out.append((r, c - 1, 3))  # W
        return out

    stack = [(0, 0)]
    visited[0][0] = True

    while stack:
        r, c = stack[-1]
        unv = [n for n in neighbors(r, c) if not visited[n[0]][n[1]]]
        if unv:
            nr, nc, side = rng.choice(unv)
            walls[r][c][side] = False
            walls[nr][nc][_OPPOSITE[side]] = False
            visited[nr][nc] = True
            stack.append((nr, nc))
        else:
            stack.pop()

    # Punch entrance (west of 0,0) and exit (east of last cell)
    walls[0][0][3] = False
    walls[rows - 1][cols - 1][1] = False
    return walls


def render_maze(walls, canvas_size=(2550, 3300), title='Maze', line_width=8):
    """
    Render a maze to a PIL image.
    canvas_size: (width, height) px (default 8.5x11 @ 300 DPI)
    """
    rows = len(walls)
    cols = len(walls[0])
    cw, ch = canvas_size

    # Reserve a bit of vertical space for START/FINISH labels inside activity_box
    label_reserve = 80
    x1, y1, x2, y2 = compute_activity_box(canvas_size, footer_reserve_px=160)
    avail_w = x2 - x1
    avail_h = (y2 - y1) - 2 * label_reserve
    cell = min(avail_w / cols, avail_h / rows)
    maze_w = int(cell * cols)
    maze_h = int(cell * rows)

    off_x = (cw - maze_w) // 2
    off_y = y1 + label_reserve + ((y2 - y1) - 2 * label_reserve - maze_h) // 2

    img = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    title_font = get_title_font(130)
    label_font = get_label_font(69)
    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black', font=title_font)

    for r in range(rows):
        for c in range(cols):
            x = off_x + int(c * cell)
            y = off_y + int(r * cell)
            x2 = off_x + int((c + 1) * cell)
            y2 = off_y + int((r + 1) * cell)
            w = walls[r][c]
            if w[0]:
                draw.line([(x, y), (x2, y)], fill='black', width=line_width)
            if w[1]:
                draw.line([(x2, y), (x2, y2)], fill='black', width=line_width)
            if w[2]:
                draw.line([(x, y2), (x2, y2)], fill='black', width=line_width)
            if w[3]:
                draw.line([(x, y), (x, y2)], fill='black', width=line_width)

    # START / FINISH labels — centered ABOVE / BELOW the maze (avoid edge clipping)
    draw.text((off_x + int(cell / 2), off_y - 40),
              'START', anchor='mb', fill='black', font=label_font)
    draw.text((off_x + maze_w - int(cell / 2), off_y + maze_h + 40),
              'FINISH', anchor='mt', fill='black', font=label_font)

    return img


def generate_maze_image(difficulty: str, seed: int, title: str,
                        canvas_size=(2550, 3300)):
    """Convenience: difficulty preset -> finished PIL image."""
    if difficulty not in DIFFICULTY_PRESETS:
        difficulty = 'medium'
    rows, cols, lw = DIFFICULTY_PRESETS[difficulty]
    walls = generate_maze(rows, cols, seed=seed)
    return render_maze(walls, canvas_size=canvas_size, title=title, line_width=lw)
