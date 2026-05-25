# Background images for 50-Design Book Mode

Each subfolder corresponds to one of the 5 KDP Book Builder categories
(strona 1–10 = floral_mandala, 11–20 = geometric_mandala, 21–30 = botanical,
31–40 = zentangle, 41–50 = floral_bouquet).

## How it works

`pattern_gen.generate_background(category, size, seed)` looks for
`*.png`, `*.jpg`, or `*.jpeg` in the matching subfolder (sorted alphabetically),
picks one by `seed % len(files)`, fits it to the requested page size
(aspect-preserving, white padding) and returns a PIL image.

**If the folder is empty**, the function falls back to the legacy procedural
generator in `pattern_gen.py` so the app keeps working.

## Recommended specs

- Format: PNG (transparent or white background) or JPG
- Aspect ratio: 7 : 9 (matches 2625×3375 px KDP page — minimal padding)
- Resolution: ≥ 2625 px on the long side at 300 DPI (anything smaller will scale up)
- Mode: grayscale or B&W line art recommended (quotes overlay in white/black)

## Naming

Files are sorted alphabetically, so use `01_*.png`, `02_*.png`, … if you care
about the order. Otherwise the seed-based picker still gives deterministic results.

## Where to find good source files

- Public domain mandala SVGs: <https://commons.wikimedia.org> (search "mandala")
- Creative Market / Etsy: paid mandala packs ($5–$20 for 50+ PNGs)
- Procedural via SVG: convert with `cairosvg --output-png …`
