# KDP Cover Generator

Generates a KDP-ready paperback book cover as a single PDF: back cover + spine + front cover.

## Setup

```bash
pip install pillow reportlab pypdf
```

No other dependencies required — backgrounds are generated procedurally.

## Quick start

```bash
cd dashboard/tools/cover_generator

python cover_builder.py \
  --title "Mindful Moments" \
  --subtitle "24 Calming Designs for Stress Relief" \
  --author "Your Name" \
  --pages 48 \
  --hook "Find Your Peace, One Page at a Time" \
  --bullets "Premium 8.5x11 format" "Single-sided printing" \
            "Bold lines for easy coloring" "Perfect gift for women" \
  --palette lavender \
  --output output/cover_final.pdf
```

Output: `output/cover_final.pdf` + `output/cover_final.png` (preview).

## Recalculating for a different page count

KDP spine width formula (white paper):

```
spine_width_inches = page_count × 0.002252
```

| Pages | Spine (in) | Total width (px @ 300 DPI) |
|-------|-----------|---------------------------|
| 24    | 0.054"    | 5191 px                   |
| 48    | 0.108"    | 5207 px                   |
| 100   | 0.225"    | 5243 px                   |
| 200   | 0.450"    | 5310 px                   |

Change `--pages` and the calculator handles everything automatically.

For cream paper use `--paper cream` (0.0025" per page instead of 0.002252").

## CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `--title` | required | Book title |
| `--subtitle` | required | Subtitle shown on front cover |
| `--author` | required | Author name |
| `--pages` | 48 | Interior page count (affects spine width) |
| `--bullets` | default set | Back cover bullet points (space-separated) |
| `--hook` | auto | Catch-phrase headline on back cover |
| `--tagline` | auto | Footer line under barcode zone |
| `--author-bio` | "" | Short author bio on back cover |
| `--background` | procedural | Path to custom background image (PNG/JPG) |
| `--decorative` | none | Path to decorative image shown on front cover |
| `--palette` | lavender | Color palette: `lavender`, `sage`, `peach` |
| `--paper` | white | Paper type: `white` or `cream` |
| `--output` | output/cover_final.pdf | Output PDF path |
| `--seed` | 42 | Random seed for procedural background |

## Color palettes

- **lavender** — purple/pink/cream — mindfulness, women's wellness
- **sage** — green/peach/cream — nature, botanical
- **peach** — peach/orange/cream — warmth, motivational

## KDP upload checklist

- [ ] PDF is a single page (back + spine + front combined)
- [ ] Dimensions: match your page count (check with `python cover_config.py`)
- [ ] Color mode: RGB (not CMYK)
- [ ] Resolution: 300 DPI
- [ ] Barcode zone (lower-right of back cover): white rectangle, no artwork
- [ ] All text inside safe zones (0.25" from each trim edge)
- [ ] File size: typically 1–5 MB is fine for KDP
- [ ] Upload as PDF to KDP → Cover section → "Upload cover file"

## Architecture

```
cover_generator/
├── cover_builder.py     # Main assembly + CLI + validation
├── cover_config.py      # KDP dimension calculator (dataclass)
├── components/
│   ├── art.py           # Procedural floral/mandala background generator
│   ├── front_cover.py   # Title, subtitle, author, border, flourishes
│   ├── back_cover.py    # Hook, bullets, barcode reserve, tagline
│   └── spine.py         # Spine fill + ornament (text only if ≥80px wide)
├── assets/
│   ├── fonts/           # Drop custom .ttf fonts here (optional)
│   ├── backgrounds/     # Drop custom background images here (optional)
│   └── decorative/      # Drop decorative PNG overlays here (optional)
└── output/              # Generated files go here
```

## Using a custom background

Drop any PNG/JPG into `assets/backgrounds/` and pass the path:

```bash
python cover_builder.py --title "..." --background assets/backgrounds/myfloral.jpg ...
```

The image is stretched to fill the full canvas (bleed included), so use a high-res image (at least 5200×3375 px ideally, or it will be upscaled).
