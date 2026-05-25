"""KDP cover dimension calculator — all values derived from KDP spec formulas."""

from dataclasses import dataclass, field
from typing import Dict


SPINE_PER_PAGE = {
    "white": 0.002252,
    "cream": 0.0025,
}

BLEED = 0.125  # inches, all sides


@dataclass
class CoverDimensions:
    # ── Inches ───────────────────────────────────────────────────────────────
    trim_w: float
    trim_h: float
    spine_w: float
    bleed: float

    total_w: float = field(init=False)
    total_h: float = field(init=False)

    # ── Pixels at 300 DPI ────────────────────────────────────────────────────
    dpi: int = 300
    total_w_px: int = field(init=False)
    total_h_px: int = field(init=False)

    # Zone x-boundaries (px, measured from left edge of full canvas)
    left_bleed_px: int = field(init=False)       # 0
    back_trim_start_px: int = field(init=False)  # = left_bleed_px
    back_trim_end_px: int = field(init=False)    # = bleed + trim_w
    spine_start_px: int = field(init=False)      # = bleed + trim_w
    spine_end_px: int = field(init=False)        # = bleed + trim_w + spine_w
    front_trim_start_px: int = field(init=False) # = spine_end_px
    front_trim_end_px: int = field(init=False)   # = bleed + 2*trim_w + spine_w
    right_bleed_px: int = field(init=False)      # = front_trim_end_px

    # Safe zones (px) — 0.25" inside each trim edge
    front_safe: Dict = field(init=False)
    back_safe: Dict = field(init=False)
    spine_safe: Dict = field(init=False)
    barcode_zone: Dict = field(init=False)

    def __post_init__(self):
        b = self.bleed
        tw = self.trim_w
        th = self.trim_h
        sw = self.spine_w
        d = self.dpi

        self.total_w = b * 2 + tw * 2 + sw
        self.total_h = b * 2 + th

        def px(inches):
            return round(inches * d)

        self.total_w_px = px(self.total_w)
        self.total_h_px = px(self.total_h)

        self.left_bleed_px      = 0
        self.back_trim_start_px = px(b)
        self.back_trim_end_px   = px(b + tw)
        self.spine_start_px     = px(b + tw)
        self.spine_end_px       = px(b + tw + sw)
        self.front_trim_start_px = px(b + tw + sw)
        self.front_trim_end_px  = px(b + 2 * tw + sw)
        self.right_bleed_px     = self.total_w_px

        margin = 0.25

        self.front_safe = {
            "x1": px(b + tw + sw + margin),
            "x2": px(b + 2 * tw + sw - margin),
            "y1": px(b + margin),
            "y2": px(b + th - margin),
        }
        self.back_safe = {
            "x1": px(b + margin),
            "x2": px(b + tw - margin),
            "y1": px(b + margin),
            "y2": px(b + th - margin),
        }
        # Spine safe: 0.0625" inset from each spine edge
        spine_margin = 0.0625
        self.spine_safe = {
            "x1": self.spine_start_px + px(spine_margin),
            "x2": self.spine_end_px   - px(spine_margin),
            "y1": px(b + spine_margin),
            "y2": px(b + th - spine_margin),
            "usable_w_px": max(0, (self.spine_end_px - self.spine_start_px) - px(spine_margin * 2)),
        }
        # Barcode reserve — 2"×1.2" at lower-right of back cover
        # Right edge: 0.25" from back cover trim right edge
        # Bottom edge: 0.5" from trim bottom
        self.barcode_zone = {
            "x1": px(b + tw - 2.25),
            "y1": px(b + th - 1.7),
            "x2": px(b + tw - 0.25),
            "y2": px(b + th - 0.5),
            "w":  px(2.0),
            "h":  px(1.2),
        }

    def summary(self) -> str:
        lines = [
            f"Trim:        {self.trim_w}\" × {self.trim_h}\"",
            f"Spine:       {self.spine_w:.4f}\" ({self.spine_end_px - self.spine_start_px}px)",
            f"Total (in):  {self.total_w:.4f}\" × {self.total_h:.4f}\"",
            f"Total (px):  {self.total_w_px} × {self.total_h_px} @ {self.dpi} DPI",
            f"Spine px:    x {self.spine_start_px} → {self.spine_end_px}",
            f"Front trim:  x {self.front_trim_start_px} → {self.front_trim_end_px}",
            f"Back trim:   x {self.back_trim_start_px} → {self.back_trim_end_px}",
            f"Front safe:  x {self.front_safe['x1']}–{self.front_safe['x2']},"
            f" y {self.front_safe['y1']}–{self.front_safe['y2']}",
            f"Back safe:   x {self.back_safe['x1']}–{self.back_safe['x2']},"
            f" y {self.back_safe['y1']}–{self.back_safe['y2']}",
            f"Barcode:     x {self.barcode_zone['x1']}–{self.barcode_zone['x2']},"
            f" y {self.barcode_zone['y1']}–{self.barcode_zone['y2']}",
        ]
        return "\n".join(lines)


def calculate_cover_dimensions(
    page_count: int,
    trim_w: float = 8.5,
    trim_h: float = 11.0,
    paper: str = "white",
    dpi: int = 300,
) -> CoverDimensions:
    spine_w = page_count * SPINE_PER_PAGE.get(paper, 0.002252)
    return CoverDimensions(
        trim_w=trim_w,
        trim_h=trim_h,
        spine_w=spine_w,
        bleed=BLEED,
        dpi=dpi,
    )


if __name__ == "__main__":
    for pages in [24, 48, 100, 200]:
        dim = calculate_cover_dimensions(pages)
        print(f"\n{'='*50}")
        print(f"Pages: {pages}")
        print(dim.summary())
