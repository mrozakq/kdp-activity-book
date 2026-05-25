"""
Centralny font manager dla generatorów Activity Book.

Cztery role:
  - get_title_font(size)   → Fredoka Bold      (tytuły stron)
  - get_body_font(size)    → Andika Regular    (instrukcje, opisy, cyfry w siatce)
  - get_label_font(size)   → Quicksand SemiBold (krótkie etykiety: START, FINISH, ?)
  - get_letter_font(size)  → Andika Bold       (litery w wordsearch — czytelne, sans)

Quicksand i Fredoka są pobrane jako variable fonts; konkretną wagę dobieramy
przez set_variation_by_name. Wszystko cachowane po (font_key, size).
"""
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

FONTS_DIR = Path(__file__).resolve().parent / 'data' / 'fonts'

# (plik, opcjonalna nazwana wariacja dla variable fonts)
_FONT_SPEC = {
    'title':  ('Fredoka-VF.ttf',     'Bold'),
    'body':   ('Andika-Regular.ttf', None),
    'label':  ('Quicksand-VF.ttf',   'SemiBold'),
    'letter': ('Andika-Bold.ttf',    None),
}


@lru_cache(maxsize=256)
def _load(role: str, size: int):
    filename, variation = _FONT_SPEC.get(role, _FONT_SPEC['body'])
    path = FONTS_DIR / filename
    if not path.exists():
        return ImageFont.load_default()
    try:
        font = ImageFont.truetype(str(path), size)
        if variation:
            try:
                font.set_variation_by_name(variation)
            except Exception:
                pass
        return font
    except Exception:
        return ImageFont.load_default()


def get_title_font(size: int):
    return _load('title', int(size))


def get_body_font(size: int):
    return _load('body', int(size))


def get_label_font(size: int):
    return _load('label', int(size))


def get_letter_font(size: int):
    return _load('letter', int(size))
