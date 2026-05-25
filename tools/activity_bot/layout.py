"""
Shared layout constants and helpers for activity book generators.

Goal: every activity page fills 75-90% of canvas area with content, not 50%
with empty whitespace. Titles sit near the top safe margin; activities fill
the rest of the page down to a small bottom reserve.

All values in pixels at 300 DPI on an 8.5" × 11" page (2550 × 3300 standard
or 2625 × 3375 with KDP bleed). 0.5" = 150 px.
"""

SAFE_MARGIN_PX        = int(0.5 * 300)   # 150 px — distance from page trim
TITLE_Y_PX            = SAFE_MARGIN_PX + 30   # 180 — top y-coord of title (anchor='mt')
TITLE_HEIGHT_PX       = 140              # Fredoka Bold @ 130 px renders ~140 px tall
TITLE_BOTTOM_GAP_PX   = 80               # gap between title bottom and next element
INSTRUCTION_HEIGHT_PX = 100              # Andika @ 80-92 px renders ~100 px per line
INSTRUCTION_GAP_PX    = 50               # gap between instruction(s) and activity
FOOTER_RESERVE_PX     = 120              # space reserved at page bottom (under activity)


def compute_activity_box(canvas_size, has_instruction=False,
                         instruction_lines=1,
                         footer_reserve_px=None):
    """Rectangle (x1, y1, x2, y2) where the activity content should be drawn.

    has_instruction:    True if there is text below the title and above the activity.
    instruction_lines:  number of lines of instruction text (default 1).
    footer_reserve_px:  override for the bottom reserved area (e.g., counting page
                        needs more room for the question + answer box).
    """
    cw, ch = canvas_size
    if footer_reserve_px is None:
        footer_reserve_px = FOOTER_RESERVE_PX

    x1 = SAFE_MARGIN_PX
    x2 = cw - SAFE_MARGIN_PX

    y1 = TITLE_Y_PX + TITLE_HEIGHT_PX + TITLE_BOTTOM_GAP_PX
    if has_instruction:
        y1 += instruction_lines * INSTRUCTION_HEIGHT_PX + INSTRUCTION_GAP_PX

    y2 = ch - SAFE_MARGIN_PX - footer_reserve_px
    return (x1, y1, x2, y2)


def title_position(canvas_size):
    """(x, y) for the title — center horizontal, top of title block.
    Use anchor='mt' when calling draw.text."""
    cw, _ = canvas_size
    return (cw // 2, TITLE_Y_PX)


def instruction_position(canvas_size, line_index=0):
    """(x, y) for an instruction line below the title.
    line_index=0 is the first line, =1 is the second, etc.
    Use anchor='mt' when calling draw.text."""
    cw, _ = canvas_size
    base_y = TITLE_Y_PX + TITLE_HEIGHT_PX + TITLE_BOTTOM_GAP_PX
    return (cw // 2, base_y + line_index * INSTRUCTION_HEIGHT_PX)
