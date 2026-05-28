"""Guard: the interior page count for each volume must equal the value baked
into its cover preset ('cover'.'pages'). If someone changes a mix/difficulty,
this fails BEFORE a wrong spine width ships to print.

It rebuilds each interior the same way blueprints/kdp/activity.py does
(same per-type seed offsets, titles, sidecar JSON, full content canvas) at
seed_base=42, then assembles the book via build_activity_book and counts pages.
"""
import json
import os
import sys
import tempfile

import pypdf
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.activity_bot.book_builder import (build_activity_book,      # noqa: E402
                                             CONTENT_W, CONTENT_H)
from tools.activity_bot.series_presets import (list_preset_keys,       # noqa: E402
                                               get_preset)
from tools.activity_bot.maze import generate_maze_image                # noqa: E402
from tools.activity_bot.sudoku import generate_sudoku_image            # noqa: E402
from tools.activity_bot.wordsearch import generate_wordsearch_image    # noqa: E402
from tools.activity_bot.magic_square import generate_magic_square_image  # noqa: E402
from tools.activity_bot.dot_grid import generate_dot_grid_image        # noqa: E402
from tools.activity_bot.counting import generate_counting_image        # noqa: E402
from tools.activity_bot.pattern import generate_pattern_image          # noqa: E402
from tools.activity_bot.symmetry import generate_symmetry_image        # noqa: E402
from tools.activity_bot.path_sums import generate_path_sums_image      # noqa: E402
from tools.activity_bot.math_maze import generate_math_maze_image      # noqa: E402

SEED_BASE = 42
CANVAS = (CONTENT_W, CONTENT_H)


def _save_sidecar(out_path, sol, n, title):
    if sol is None:
        return
    sol = dict(sol)
    sol['n'] = n
    sol['title'] = title
    side = str(out_path).rsplit('.', 1)[0] + '.json'
    with open(side, 'w', encoding='utf-8') as f:
        json.dump(sol, f, ensure_ascii=False)


def _gen(kind, n, mix_n, diff, theme, tmpdir, idx):
    """Generate one activity PNG (+ sidecar) mirroring activity.py. Returns path."""
    out = os.path.join(tmpdir, f'{idx:03d}_{kind}.png')
    sol = None
    if kind == 'maze':
        img, sol = generate_maze_image(difficulty=diff['difficulty'],
                                       seed=SEED_BASE + n, title=f'Prompt Path {n}',
                                       canvas_size=CANVAS, return_solution=True)
        title = f'Prompt Path {n}'
    elif kind == 'sudoku':
        img, sol = generate_sudoku_image(size_key=diff['sudoku_size'],
                                         difficulty=diff['sudoku_difficulty'],
                                         seed=SEED_BASE + 2000 + n, title=f'Constraints {n}',
                                         canvas_size=CANVAS, return_solution=True)
        title = f'Constraints {n}'
    elif kind == 'wordsearch':
        img, sol = generate_wordsearch_image(theme=theme,
                                             difficulty=diff['wordsearch_difficulty'],
                                             seed=SEED_BASE + 3000 + n,
                                             title=f'Find the Keywords {n}',
                                             canvas_size=CANVAS, return_solution=True)
        title = f'Find the Keywords {n}'
    elif kind == 'magic':
        img, sol = generate_magic_square_image(difficulty=diff['magic_difficulty'],
                                               seed=SEED_BASE + 4000 + n,
                                               title=f'Balance the Grid {n}',
                                               canvas_size=CANVAS, return_solution=True)
        title = f'Balance the Grid {n}'
    elif kind == 'dotgrid':
        img = generate_dot_grid_image(difficulty=diff['dotgrid_difficulty'],
                                      seed=SEED_BASE + 4000 + n, title=f'Draw the Output {n}',
                                      canvas_size=CANVAS)
        title = f'Draw the Output {n}'
    elif kind == 'counting':
        img, sol = generate_counting_image(difficulty=diff['counting_difficulty'],
                                           seed=SEED_BASE + 5000 + n,
                                           title=f'Count the Tokens {n}',
                                           canvas_size=CANVAS, return_solution=True)
        title = f'Count the Tokens {n}'
    elif kind == 'pattern':
        img, sol = generate_pattern_image(difficulty=diff['pattern_difficulty'],
                                          seed=SEED_BASE + 6000 + n, title=f'Loop It {n}',
                                          canvas_size=CANVAS, return_solution=True)
        title = f'Loop It {n}'
    elif kind == 'symmetry':
        img = generate_symmetry_image(difficulty=diff['symmetry_difficulty'],
                                      seed=SEED_BASE + 7000 + n, title=f'Mirror Function {n}',
                                      canvas_size=CANVAS)
        title = f'Mirror Function {n}'
    elif kind == 'pathsum':
        img, sol = generate_path_sums_image(difficulty=diff['pathsum_difficulty'],
                                            seed=SEED_BASE + 9000 + n, title=f'Accumulator {n}',
                                            canvas_size=CANVAS, return_solution=True)
        title = f'Accumulator {n}'
    elif kind == 'mathmaze':
        img, sol = generate_math_maze_image(difficulty=diff['mathmaze_difficulty'],
                                            seed=SEED_BASE + 10000 + n, title=f'Decision Tree {n}',
                                            canvas_size=CANVAS, return_solution=True)
        title = f'Decision Tree {n}'
    else:
        raise ValueError(kind)
    img.save(out)
    _save_sidecar(out, sol, n, title)
    return out


# (mix key, kind) — mix uses 'n_mazes' but the file/section key is 'maze'.
_KINDS = [
    ('n_mazes', 'maze'), ('n_sudoku', 'sudoku'), ('n_wordsearch', 'wordsearch'),
    ('n_magic', 'magic'), ('n_dotgrid', 'dotgrid'), ('n_counting', 'counting'),
    ('n_pattern', 'pattern'), ('n_symmetry', 'symmetry'), ('n_pathsum', 'pathsum'),
    ('n_mathmaze', 'mathmaze'),
]


def _build_interior(preset, tmpdir):
    mix, diff, theme = preset['mix'], preset['difficulty'], preset['wordsearch_theme']
    pages, idx = [], 0
    for mix_key, kind in _KINDS:
        for n in range(1, mix.get(mix_key, 0) + 1):
            idx += 1
            pages.append(_gen(kind, n, mix.get(mix_key, 0), diff, theme, tmpdir, idx))
    metadata = {
        'title': preset['title'], 'subtitle': preset['subtitle'],
        'author': preset['author'], 'age_range': preset['age_range'], 'year': 2026,
        'chapter_intros': preset.get('chapter_intros', {}),
    }
    out_pdf = os.path.join(tmpdir, 'book.pdf')
    build_activity_book(pages, metadata, out_pdf)
    return out_pdf


@pytest.mark.parametrize('key', list_preset_keys())
def test_interior_matches_cover_pages(key):
    preset = get_preset(key)
    expected = preset['cover']['pages']
    with tempfile.TemporaryDirectory() as td:
        pdf = _build_interior(preset, td)
        got = len(pypdf.PdfReader(pdf).pages)
    assert got == expected, f'{key}: interior has {got} pages, cover expects {expected}'
    assert got % 2 == 0, f'{key}: page count {got} is odd (KDP requires even)'
