import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.activity_bot.book_builder import (render_answer_key_pages,  # noqa: E402
                                             _wordsearch_cells, _KEY_RENDERABLE)


def test_hard_types_in_renderable():
    for t in ('maze', 'pathsum', 'mathmaze', 'wordsearch'):
        assert t in _KEY_RENDERABLE


def test_wordsearch_cells_count():
    # word 'CAT' placed right from (2,3): cells (2,3),(2,4),(2,5)
    cells = _wordsearch_cells([['CAT', 2, 3, 0, 1]])
    assert cells == {(2, 3), (2, 4), (2, 5)}
    # diagonal down-right 'DOG' from (0,0)
    cells = _wordsearch_cells([['DOG', 0, 0, 1, 1]])
    assert cells == {(0, 0), (1, 1), (2, 2)}


def test_renders_all_types_no_crash():
    sols = [
        {'type': 'maze', 'n': 1, 'title': 'Prompt Path 1',
         'data': {'path': [[0, 0], [0, 1], [1, 1]], 'rows': 2, 'cols': 2,
                  'walls': [[[1, 0, 1, 0], [1, 1, 0, 0]], [[1, 0, 1, 1], [0, 1, 1, 0]]]}},
        {'type': 'pathsum', 'n': 1, 'title': 'Accumulator 1',
         'data': {'path': [[0, 0], [1, 0], [1, 1]], 'target': 9,
                  'grid': [[3, 2], [4, 5]]}},
        {'type': 'mathmaze', 'n': 1, 'title': 'Decision Tree 1',
         'data': {'path': [[0, 0], [0, 1]], 'rule': 'multiple', 'param': 3,
                  'grid': [[3, 6], [4, 5]]}},
        {'type': 'wordsearch', 'n': 1, 'title': 'Find the Keywords 1',
         'data': {'placements': [['CAT', 0, 0, 0, 1]],
                  'grid': [['C', 'A', 'T'], ['X', 'Y', 'Z'], ['Q', 'W', 'E']]}},
    ]
    pages = render_answer_key_pages(sols)
    assert len(pages) >= 1
    for p in pages:
        assert p.size[0] > 0 and p.size[1] > 0
