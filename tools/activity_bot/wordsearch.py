"""
Word-search ("wykreślanka") for KDP Activity Book.

Place N words on a grid in 8 directions, fill empty cells with random letters,
print the word list below. Kid-friendly themes shipped in PL and EN.
"""
import random
import string
import unicodedata

from PIL import Image, ImageDraw

from .fonts import get_title_font, get_body_font, get_letter_font
from .layout import compute_activity_box, title_position, SAFE_MARGIN_PX


THEMES = {
    'animals_pl':  ['PIES', 'KOT', 'RYBA', 'PTAK', 'LEW', 'KROWA', 'KOŃ', 'ZAJĄC'],
    'animals_en':  ['DOG', 'CAT', 'FISH', 'BIRD', 'LION', 'BEAR', 'HORSE', 'COW'],
    'fruits_pl':   ['JABŁKO', 'GRUSZKA', 'ŚLIWKA', 'BANAN', 'CYTRYNA', 'WIŚNIA', 'MELON'],
    'fruits_en':   ['APPLE', 'PEAR', 'PLUM', 'BANANA', 'LEMON', 'CHERRY', 'PEACH', 'GRAPE'],
    'colors_pl':   ['CZERWONY', 'NIEBIESKI', 'ZIELONY', 'ŻÓŁTY', 'BIAŁY', 'CZARNY'],
    'colors_en':   ['RED', 'BLUE', 'GREEN', 'YELLOW', 'WHITE', 'BLACK', 'PURPLE', 'ORANGE'],
    'family_pl':   ['MAMA', 'TATA', 'BRAT', 'SIOSTRA', 'BABCIA', 'DZIADEK', 'CIOCIA'],
    'family_en':   ['MOM', 'DAD', 'BROTHER', 'SISTER', 'GRANDMA', 'GRANDPA', 'BABY'],
    'school_pl':   ['KSIĄŻKA', 'ZESZYT', 'OŁÓWEK', 'ŁAWKA', 'GUMKA', 'TORNISTER'],
    'school_en':   ['BOOK', 'PEN', 'DESK', 'CHAIR', 'BAG', 'RULER', 'PENCIL', 'ERASER'],
}

# (rows, cols)
GRID_PRESETS = {
    'easy':   (10, 10),
    'medium': (12, 12),
    'hard':   (15, 15),
}

# 8 directions: (dr, dc)
DIRS = [
    (0, 1),   # right
    (1, 0),   # down
    (1, 1),   # down-right
    (-1, 1),  # up-right
    (0, -1),  # left (reversed)
    (-1, 0),  # up (reversed)
    (-1, -1), # up-left
    (1, -1),  # down-left
]


def _strip_diacritics(word: str) -> str:
    """Convert ŚŁĄ → SLA for grid placement (Polish chars normalized).
    Some kids find diacritics confusing in puzzles — render plain ASCII upper."""
    nfkd = unicodedata.normalize('NFKD', word)
    out = ''.join(c for c in nfkd if not unicodedata.combining(c))
    # Manual map for Ł which doesn't decompose
    out = out.replace('Ł', 'L').replace('ł', 'l')
    return out.upper()


def _place_words(words, rows: int, cols: int, rng: random.Random,
                 max_attempts: int = 200):
    """Try to place each word in the grid. Returns (grid, placements, skipped)."""
    grid = [['' for _ in range(cols)] for _ in range(rows)]
    placements = []  # list of (word, r, c, dr, dc)
    skipped = []

    for word in sorted(words, key=len, reverse=True):
        placed = False
        for _ in range(max_attempts):
            dr, dc = rng.choice(DIRS)
            n = len(word)
            # Valid start positions given direction
            r = rng.randrange(rows)
            c = rng.randrange(cols)
            er = r + dr * (n - 1)
            ec = c + dc * (n - 1)
            if not (0 <= er < rows and 0 <= ec < cols):
                continue
            # Check fit (allow overlap if same letter)
            ok = True
            for i, ch in enumerate(word):
                rr, cc = r + dr * i, c + dc * i
                if grid[rr][cc] not in ('', ch):
                    ok = False
                    break
            if not ok:
                continue
            for i, ch in enumerate(word):
                grid[r + dr * i][c + dc * i] = ch
            placements.append((word, r, c, dr, dc))
            placed = True
            break
        if not placed:
            skipped.append(word)

    return grid, placements, skipped


def _fill_empty(grid, rng: random.Random):
    rows, cols = len(grid), len(grid[0])
    letters = string.ascii_uppercase
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '':
                grid[r][c] = rng.choice(letters)
    return grid


def render_wordsearch(grid, words_display, canvas_size=(2550, 3300),
                      title='Word Search'):
    rows, cols = len(grid), len(grid[0])
    cw, ch = canvas_size

    # Reserve room at the bottom for the word list
    word_list_h = 480
    x1, y1, x2, y2 = compute_activity_box(canvas_size,
                                          footer_reserve_px=word_list_h + 50)
    avail_w = x2 - x1
    avail_h = y2 - y1
    cell = min(avail_w // cols, avail_h // rows)
    grid_w = cell * cols
    grid_h = cell * rows

    off_x = (cw - grid_w) // 2
    off_y = y1 + (avail_h - grid_h) // 2

    img = Image.new('RGB', (cw, ch), 'white')
    draw = ImageDraw.Draw(img)

    title_font = get_title_font(130)
    letter_font = get_letter_font(int(cell * 0.69))
    word_font = get_body_font(67)

    tx, ty = title_position(canvas_size)
    draw.text((tx, ty), title, anchor='mt', fill='black', font=title_font)

    # Grid lines (thin)
    for i in range(rows + 1):
        y = off_y + i * cell
        draw.line([(off_x, y), (off_x + grid_w, y)], fill='black', width=2)
    for j in range(cols + 1):
        x = off_x + j * cell
        draw.line([(x, off_y), (x, off_y + grid_h)], fill='black', width=2)
    # Thick outer border
    draw.rectangle([(off_x, off_y), (off_x + grid_w, off_y + grid_h)],
                   outline='black', width=6)

    # Letters
    for r in range(rows):
        for c in range(cols):
            x = off_x + c * cell + cell // 2
            y = off_y + r * cell + cell // 2
            draw.text((x, y), grid[r][c], anchor='mm',
                      fill='black', font=letter_font)

    # Word list — 3 columns near the bottom of the page
    list_top = ch - SAFE_MARGIN_PX - word_list_h
    col_count = 3
    per_col = (len(words_display) + col_count - 1) // col_count
    col_w = (cw - 2 * SAFE_MARGIN_PX) // col_count
    for i, w in enumerate(words_display):
        col = i // per_col
        row = i % per_col
        wx = SAFE_MARGIN_PX + col * col_w + 30
        wy = list_top + row * 80
        draw.text((wx, wy), '• ' + w, anchor='lt', fill='black', font=word_font)

    return img


def generate_wordsearch_image(theme: str, difficulty: str, seed: int, title: str,
                              canvas_size=(2550, 3300)):
    if theme not in THEMES:
        theme = 'animals_en'
    rows, cols = GRID_PRESETS.get(difficulty, GRID_PRESETS['medium'])

    rng = random.Random(seed)
    original_words = THEMES[theme]
    # Map of original → ASCII-upper placement form
    grid_form = [_strip_diacritics(w) for w in original_words]

    grid, _, skipped = _place_words(grid_form, rows, cols, rng)
    _fill_empty(grid, rng)

    # Display original (with PL diacritics) in the legend so kids see correct spelling
    placed_display = [orig for orig, gf in zip(original_words, grid_form)
                      if gf not in skipped]

    return render_wordsearch(grid, placed_display,
                             canvas_size=canvas_size, title=title)
