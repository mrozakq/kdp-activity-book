from pathlib import Path

# ── KDP constants ─────────────────────────────────────────────────────────────
KDP_DPI        = 300
KDP_BLEED_IN   = 0.125          # 1/8 inch bleed on each side
KDP_TRIM_W_IN  = 8.5
KDP_TRIM_H_IN  = 11.0
KDP_PAGE_W_IN  = KDP_TRIM_W_IN + 2 * KDP_BLEED_IN   # 8.75"
KDP_PAGE_H_IN  = KDP_TRIM_H_IN + 2 * KDP_BLEED_IN   # 11.25"
KDP_PAGE_W_PX  = int(KDP_PAGE_W_IN * KDP_DPI)        # 2625 px
KDP_PAGE_H_PX  = int(KDP_PAGE_H_IN * KDP_DPI)        # 3375 px
KDP_BLEED_PX   = int(KDP_BLEED_IN  * KDP_DPI)        # 37 px
KDP_TRIM_W_PX  = int(KDP_TRIM_W_IN * KDP_DPI)        # 2550 px
KDP_TRIM_H_PX  = int(KDP_TRIM_H_IN * KDP_DPI)        # 3300 px
KDP_MIN_PAGES  = 24
# PDF points (1 pt = 1/72 inch)
KDP_PAGE_W_PT  = KDP_PAGE_W_IN * 72   # 630 pt
KDP_PAGE_H_PT  = KDP_PAGE_H_IN * 72   # 810 pt
KDP_BLEED_PT   = KDP_BLEED_IN  * 72   # 9 pt
KDP_TRIM_W_PT  = KDP_TRIM_W_IN * 72   # 612 pt
KDP_TRIM_H_PT  = KDP_TRIM_H_IN * 72   # 792 pt

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
UPLOAD_DIR  = BASE_DIR / 'uploads'
RESULTS_DIR = BASE_DIR / 'results'
DATA_DIR    = BASE_DIR / 'data'
TOOLS_DIR   = BASE_DIR / 'tools'
DB_PATH     = DATA_DIR / 'runs.db'

COLORING_DIR   = TOOLS_DIR / 'coloring_bot'
FLASHCARD_DIR  = TOOLS_DIR / 'flashcard_bot'
COMPARISON_DIR = TOOLS_DIR / 'comparison_bot'
KEYWORD_DIR    = TOOLS_DIR / 'keyword_parser'
TIKTOK_DIR     = TOOLS_DIR / 'tiktok_bot'
COVER_DIR      = TOOLS_DIR / 'cover_generator'

for d in [UPLOAD_DIR, RESULTS_DIR, DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Coloring / KDP Builder fonts ──────────────────────────────────────────────
FONT_MAP = {
    'Shrikhand':   'Shrikhand/Shrikhand-Regular.ttf',
    'Lobster':     'Lobster/Lobster-Regular.ttf',
    'PassionOne':  'Passion_One/PassionOne-Regular.ttf',
    'FugazOne':    'Fugaz_One/FugazOne-Regular.ttf',
    'CarterOne':   'Carter_One/CarterOne-Regular.ttf',
    'Pattaya':     'Pattaya/Pattaya-Regular.ttf',
    'Harlow':      'Harlow Solid Regular/Harlow Solid Regular.ttf',
    'Courgette':   'Courgette/Courgette-Regular.ttf',
    'Calistoga':   'Calistoga/Calistoga-Regular.ttf',
    'OleoScript':  'Oleo_Script_Swash_Caps/OleoScriptSwashCaps-Regular.ttf',
    'Lemon':       'Lemon/Lemon-Regular.ttf',
    'MochiyPop':   'Mochiy_Pop_One/MochiyPopOne-Regular.ttf',
    'SpicyRice':   'Spicy_Rice/SpicyRice-Regular.ttf',
    'MochiyPopP':  'Mochiy_Pop_P_One/MochiyPopPOne-Regular.ttf',
    'Kavoon':      'Kavoon/Kavoon-Regular.ttf',
}

# ── Flashcard palette ─────────────────────────────────────────────────────────
BG_COLORS = ['#e2d3fe', '#739de0', '#f4667b', '#92d6ad',
             '#fecd60', '#fea48e', '#6ccbbf', '#78d08a']
BG_NAMES  = ['Fioletowy', 'Niebieski', 'Różowy', 'Zielony',
             'Żółty', 'Łososiowy', 'Turkusowy', 'Jasnozielony']

# ── Cover palettes ────────────────────────────────────────────────────────────
COVER_PALETTES = ['lavender', 'sage', 'peach']
COVER_KIDS_PALETTES = ['rainbow_pop', 'city_bright', 'space_blue', 'jungle_green', 'unicorn_pink']
COVER_KIDS_THEMES   = ['city', 'space', 'jungle', 'ocean', 'generic_stars']
