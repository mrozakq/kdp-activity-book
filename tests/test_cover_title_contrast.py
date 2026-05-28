"""Guard: the front-cover title must stay legible on the light title banner.

The banner is white at ~35% alpha; pessimistically we treat it as a light
(240,240,240) surface. The final title colour (after front_cover's
_banner_text_color fallback) must clear WCAG AA contrast (>= 4.5) against it.
Catches a future palette that ships a light 'text' colour without a fallback.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'cover_generator'))

from components.front_cover import _banner_text_color   # noqa: E402
from components.art import PALETTES                      # noqa: E402

KIDS_PALETTES = ['rainbow_pop', 'city_bright', 'space_blue',
                 'jungle_green', 'unicorn_pink']

# Pessimistic light approximation of the (255,255,255, alpha=90) banner.
BANNER = (240, 240, 240)
AA_NORMAL = 4.5


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
def test_title_contrast_on_light_banner(name):
    title_col = _banner_text_color(PALETTES[name])
    ratio = _contrast(title_col, BANNER)
    assert ratio >= AA_NORMAL, (
        f'{name}: title {title_col} contrast {ratio:.2f} < {AA_NORMAL} '
        f'on banner {BANNER}')
