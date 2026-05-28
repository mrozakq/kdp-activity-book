"""Procedural back-cover blurb assembled from the volume's real activity types.

No randomness, no preset 'blurb' field — the blurb is derived from the types
actually present (same ids the TOC / 'How to Use' use). These tests pin the
list grammar, determinism, the 6-phrase cap, the empty fallback, and verify
each of the 5 series presets yields a real, non-'busy little town' blurb.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'cover_generator'))

from components.back_cover import build_blurb, _BLURB_PHRASES   # noqa: E402
from tools.activity_bot.series_presets import (list_preset_keys,  # noqa: E402
                                               get_preset)
from blueprints.kdp.cover import _types_from_mix                 # noqa: E402

PHRASES = set(_BLURB_PHRASES.values())


def test_blurb_basic_grammar():
    b = build_blurb(['maze', 'pattern', 'symmetry', 'math_maze',
                     'path_sums', 'wordsearch'])
    assert 'mazes' in b
    assert 'word searches' in b
    assert ' and ' in b                 # natural list conjunction
    assert ', and ' not in b            # no Oxford comma
    assert 'busy little town' not in b
    assert b.startswith('Packed with ')


def test_blurb_deterministic():
    t = ['maze', 'pattern', 'counting']
    assert build_blurb(t) == build_blurb(t)


def test_blurb_dedupe_alias_keeps_order():
    # alias 'mazes' -> 'maze' (same phrase) must not duplicate
    b = build_blurb(['maze', 'mazes', 'pattern'])
    assert b.count('mazes') == 1
    assert b.index('mazes') < b.index('pattern puzzles')


def test_blurb_caps_at_six():
    allt = ['maze', 'pattern', 'symmetry', 'counting', 'wordsearch',
            'dot_grid', 'math_maze', 'path_sums', 'sudoku', 'magic_square']
    b = build_blurb(allt)
    seg = b.split('Packed with ', 1)[1].split(' — perfect', 1)[0]
    parts = seg.replace(' and ', ', ').split(', ')
    assert len(parts) == 6


def test_blurb_empty_fallback():
    for empty in ([], None):
        b = build_blurb(empty)
        assert 'Packed with' not in b
        assert b.startswith('Hours of screen-free puzzle fun')


@pytest.mark.parametrize('key', list_preset_keys())
def test_blurb_per_preset_is_real(key):
    p = get_preset(key)
    types = _types_from_mix(p['mix'])
    b = build_blurb(types)
    assert 'busy little town' not in b
    assert any(ph in b for ph in PHRASES), f'{key}: no activity phrase in blurb'
