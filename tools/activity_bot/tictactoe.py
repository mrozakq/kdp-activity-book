"""
Tic-Tac-Toe printable sheets for KDP Activity Book.

Each page holds a grid of empty 3x3 boards (default 6 boards: 2 cols x 3 rows).
Kids play with a friend by filling in X / O.
"""
from PIL import Image, ImageDraw

from .fonts import get_title_font
from .layout import compute_activity_box, title_position


# (boards_per_page, cols, rows)
DIFFICULTY_PRESETS = {
    'easy':   (4, 2, 2),   # 4 large boards (more room to write)
    'medium': (6, 2, 3),   # 6 medium boards
    'hard':   (9, 3, 3),   # 9 small boards
}


def render_tictactoe(canvas_size=(2625, 3375),
                     title='Tic-Tac-Toe',
                     boards=6, cols=2, rows=3):
    cw, ch = canvas_size

    x1, y1, x2, y2 = compute_activity_box(canvas_size)
    gap = 100

    avail_w = x2 - x1
    avail_h = y2 - y1
    board_w_max = (avail_w - (cols - 1) * gap) / cols
    board_h_max = (avail_h - (rows - 1) * gap) / rows
    board_size = int(min(board_w_max, board_h_max))
    cell = board_size // 3

    total_w = cols * board_size + (cols - 1) * gap
    total_h = rows * board_size + (rows - 1) * gap
    grid_left = (cw - total_w) // 2
    grid_top = y1 + (avail_h - total_h) // 2

    img = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    title_font = get_title_font(130)
    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black', font=title_font)

    # Draw N boards
    for idx in range(boards):
        col = idx % cols
        row = idx // cols
        if row >= rows:
            break
        x0 = grid_left + col * (board_size + gap)
        y0 = grid_top  + row * (board_size + gap)
        x1 = x0 + cell * 3
        y1 = y0 + cell * 3
        # Two internal vertical + horizontal lines (no outer box — looks cleaner)
        lw = 10
        for k in (1, 2):
            draw.line([(x0 + k * cell, y0), (x0 + k * cell, y1)],
                      fill='black', width=lw)
            draw.line([(x0, y0 + k * cell), (x1, y0 + k * cell)],
                      fill='black', width=lw)

    return img


def generate_tictactoe_image(difficulty: str, title: str,
                             canvas_size=(2625, 3375)):
    n, cols, rows = DIFFICULTY_PRESETS.get(difficulty, DIFFICULTY_PRESETS['medium'])
    return render_tictactoe(canvas_size=canvas_size, title=title,
                            boards=n, cols=cols, rows=rows)
