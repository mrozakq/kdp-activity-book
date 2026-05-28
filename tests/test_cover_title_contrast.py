"""Guard: every cover text drawn on a light/white surface must stay legible.

Covers (kids covers) draw these texts on light backgrounds:
  - title + subtitle  → on the semi-transparent white title banner
  - "What's Inside?"  → on the opaque white marketing panel (back cover)
  - author byline     → on the opaque white pill (front cover)

Each final colour (after the shared text_on_light / _banner_text_color
fallback) must clear WCAG AA contrast (>= 4.5) against a pessimistic light
surface. This catches a future palette that ships a light 'text' colour for
ANY of these roles, not just the title (the earlier title-only guard missed
the header and author cases on space_blue).
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'cover_generator'))

from components.front_cover import _banner_text_color   # noqa: E402
from components.art import PALETTES, text_on_light       # noqa: E402

KIDS_PALETTES = ['rainbow_pop', 'city_bright', 'space_blue',
                 'jungle_green', 'unicorn_pink']

# Pessimistic light surface: darker than opaque white (255) and matches the
# composited (255,255,255, alpha=90) banner — one value for every role.
LIGHT_BG = (240, 240, 240)
AA_NORMAL = 4.5

# role -> function producing the final drawn colour for that text
ROLE_COLOR = {
    'title':    lambda p: _banner_text_color(p),
    'subtitle': lambda p: _banner_text_color(p),
    'header':   lambda p: text_on_light(p),   # "What's Inside?" on white panel
    'author':   lambda p: text_on_light(p),   # byline on white pill
}


def _rel_lum(rgb):
    def lin(c):
        cs = c / 255.0
        return cs / 12.92 if cs <= 0.03928 else ((cs + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(rgb[0]) + 0.7152 * lin(rgb[1]) + 0.0722 * lin(rgb[2])


def _contrast(c1, c2):
    l1, l2 = _rel_lum(c1), _rel_lum(c2)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize('name', KIDS_PALETTES)
@pytest.mark.parametrize('role', sorted(ROLE_COLOR))
def test_text_contrast_on_light(role, name):
    col = ROLE_COLOR[role](PALETTES[name])
    ratio = _contrast(col, LIGHT_BG)
    assert ratio >= AA_NORMAL, (
        f'{name}/{role}: colour {col} contrast {ratio:.2f} < {AA_NORMAL} '
        f'on light surface {LIGHT_BG}')
