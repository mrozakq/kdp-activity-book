#!/usr/bin/env python3
"""One-off: build a SMALL verification PDF with one or two examples of each
key-bearing activity type plus the auto-generated 'Answers' section.

It reuses an existing results/<job_id>/ directory that already has PNGs +
sidecar .json files (produced by /activity/run). We select up to 2 PNGs of
each kind, hand them to build_activity_book (which loads the matching sidecars
itself), and write verify_key.pdf for visual review of Etap 2B-2 (path/word
highlights) and the magic-square variety fix.

Usage:
    python scripts/make_verify_pdf.py [results_dir] [out.pdf]
If no results_dir is given, the newest results/<id>/ that contains .json
sidecars is used.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.activity_bot.book_builder import build_activity_book  # noqa: E402
from tools.activity_bot.series_presets import get_preset          # noqa: E402

KEY_KINDS = ['maze', 'pathsum', 'mathmaze', 'wordsearch',
             'sudoku', 'magic', 'counting', 'pattern']
CONTEXT_KINDS = ['symmetry', 'dotgrid']   # no key, included once for context
_FN = re.compile(r'^(\d+)_([a-z]+)', re.IGNORECASE)


def newest_results_with_sidecars():
    dirs = glob.glob(os.path.join(ROOT, 'results', '*/'))
    dirs = [d for d in dirs if glob.glob(os.path.join(d, '*.json'))]
    if not dirs:
        return None
    return max(dirs, key=os.path.getmtime)


def kind_of(path):
    m = _FN.match(os.path.basename(path))
    return m.group(2).lower() if m else None


def main():
    res_dir = sys.argv[1] if len(sys.argv) > 1 else newest_results_with_sidecars()
    out_pdf = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'verify_key.pdf')
    if not res_dir or not os.path.isdir(res_dir):
        sys.exit('No results dir with sidecars found — run /activity/run first.')

    print(f'Using results dir: {res_dir}')
    pngs = sorted(glob.glob(os.path.join(res_dir, '*.png')))

    # pick up to 2 of each key kind, 1 of each context kind
    picked, taken = [], {}
    for p in pngs:
        k = kind_of(p)
        if k in KEY_KINDS and taken.get(k, 0) < 2:
            picked.append(p); taken[k] = taken.get(k, 0) + 1
        elif k in CONTEXT_KINDS and taken.get(k, 0) < 1:
            picked.append(p); taken[k] = taken.get(k, 0) + 1
    # deterministic order: by kind, then filename
    picked.sort(key=lambda p: (kind_of(p), os.path.basename(p)))

    print('Selected examples:')
    for k in KEY_KINDS + CONTEXT_KINDS:
        if taken.get(k):
            print(f'   {k}: {taken[k]}')

    preset = get_preset('vibe_v5_ai_director') or {}
    metadata = {
        'title': 'Little Vibe Coders — KEY VERIFY',
        'subtitle': 'Sampler for answer-key review',
        'author': 'Mr Felix Mrozak',
        'age_range': '6-7',
        'year': 2026,
        'chapter_intros': preset.get('chapter_intros', {}),
    }

    res = build_activity_book(picked, metadata, out_pdf, jlog_fn=print)
    print(f'\nWROTE: {out_pdf}')
    print(f'total_pages: {res["total_pages"]}')
    print(f'sections: {res["sections"]}')


if __name__ == '__main__':
    main()
