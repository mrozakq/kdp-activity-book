"""
KDP cover builder — assembles back cover + spine + front cover into a
single PDF file at 300 DPI.

Usage:
    python cover_builder.py --title "Mindful Moments" \
        --subtitle "24 Calming Designs for Stress Relief" \
        --author "Your Name" --pages 48 \
        --bullets "Premium 8.5x11 size" "Single-sided printing" \
                  "Bold lines for easy coloring" "Perfect gift for women" \
        --output output/cover_final.pdf
"""

import argparse
import sys
import os
from pathlib import Path

# Allow imports from this package regardless of cwd
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
from cover_config import calculate_cover_dimensions, CoverDimensions
from components.art import generate_background, generate_spine_bg, PALETTES
from components.kids_art import generate_kids_background
from components.front_cover import render_front_cover
from components.back_cover import render_back_cover
from components.spine import render_spine


def build_cover(
    title: str,
    subtitle: str,
    author: str,
    description_bullets: list,
    page_count: int = 48,
    background_image_path: str = None,
    output_pdf: str = "output/cover_final.pdf",
    palette_name: str = "lavender",
    hook: str = None,
    tagline: str = None,
    author_bio: str = None,
    paper: str = "white",
    decorative_image_path: str = None,
    seed: int = 42,
    log=None,
    # kids-mode params (gated; ignored when cover_mode != "kids")
    cover_mode: str = "adult",        # "adult" | "kids"
    bg_theme: str = "city",           # used when cover_mode == "kids"
    badge_text: str = "",             # e.g. "AGES 3-5"
    cta_text: str = "",               # call-to-action above barcode zone
    mascot_image_path: str = None,    # PIL-loadable sticker for front cover
) -> dict:
    """
    Build a KDP-compliant full cover PDF.
    Returns validation results dict.
    """
    def _log(msg):
        if log:
            log(msg)
        else:
            print(msg)

    # ── 1. Calculate dimensions ───────────────────────────────────────────────
    _log(f"📐 Obliczam wymiary KDP dla {page_count} stron ({paper} paper)...")
    dim = calculate_cover_dimensions(page_count, paper=paper)
    _log(dim.summary())

    # ── 2. Create canvas ──────────────────────────────────────────────────────
    _log(f"\n🖼️  Tworzę canvas {dim.total_w_px}×{dim.total_h_px}px...")
    canvas = Image.new("RGB", (dim.total_w_px, dim.total_h_px), (255, 255, 255))

    # ── 3. Background ─────────────────────────────────────────────────────────
    if background_image_path and Path(background_image_path).exists():
        _log(f"🎨 Ładuję tło: {background_image_path}")
        bg = Image.open(background_image_path).convert("RGB")
        bg = bg.resize((dim.total_w_px, dim.total_h_px), Image.LANCZOS)
    elif cover_mode == "kids":
        _log(f"🎨 Generuję tło kids '{bg_theme}' z paletą '{palette_name}'...")
        bg = generate_kids_background(
            (dim.total_w_px, dim.total_h_px),
            theme=bg_theme,
            palette_name=palette_name,
            seed=seed,
        )
    else:
        _log("🎨 Generuję proceduralne tło floralne...")
        bg = generate_background(
            (dim.total_w_px, dim.total_h_px),
            palette_name=palette_name,
            seed=seed,
        )
    canvas.paste(bg, (0, 0))

    # ── 4. Convert to RGBA for compositing ───────────────────────────────────
    canvas = canvas.convert("RGBA")

    # ── 5. Spine ──────────────────────────────────────────────────────────────
    _log("📕 Rysuję grzbiet...")
    canvas = render_spine(canvas, dim, title, palette_name)

    # ── 6. Front cover content ────────────────────────────────────────────────
    _log("🖊️  Rysuję przednią okładkę...")
    decorative_img = None
    if decorative_image_path and Path(decorative_image_path).exists():
        decorative_img = Image.open(decorative_image_path).convert("RGBA")
    mascot_img = None
    if mascot_image_path and Path(mascot_image_path).exists():
        mascot_img = Image.open(mascot_image_path).convert("RGBA")
    canvas = render_front_cover(
        canvas, dim,
        title=title,
        subtitle=subtitle,
        author=author,
        palette_name=palette_name,
        decorative_image=decorative_img,
        cover_mode=cover_mode,
        mascot_image=mascot_img,
        badge_text=badge_text,
    )

    # ── 7. Back cover content ─────────────────────────────────────────────────
    _log("🖊️  Rysuję tylnią okładkę...")
    canvas = render_back_cover(
        canvas, dim,
        hook=hook or ("Fun-Filled Adventures Inside!" if cover_mode == "kids"
                       else "Color Your Way to Calm"),
        bullets=description_bullets,
        author_bio=author_bio or "",
        tagline=tagline or f"{page_count} Pages · 8.5 × 11 inches",
        palette_name=palette_name,
        cover_mode=cover_mode,
        badge_text=badge_text,
        cta_text=cta_text,
    )

    # ── 8. Flatten to RGB ─────────────────────────────────────────────────────
    final = Image.new("RGB", (dim.total_w_px, dim.total_h_px), (255, 255, 255))
    final.paste(canvas.convert("RGB"), (0, 0))
    if canvas.mode == "RGBA":
        final.paste(canvas.convert("RGB"), (0, 0),
                    mask=canvas.split()[3] if len(canvas.split()) == 4 else None)

    # ── 9. Save PDF ───────────────────────────────────────────────────────────
    output_path = Path(output_pdf)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save intermediate PNG (for debugging)
    png_path = output_path.with_suffix(".png")
    final.save(str(png_path), dpi=(300, 300))
    _log(f"💾 PNG saved: {png_path}")

    # Save PDF via reportlab for exact dimension control
    _log("📄 Generuję PDF...")
    _save_pdf(final, dim, str(output_path))
    _log(f"✅ PDF saved: {output_path}")

    # ── 10. Validate ──────────────────────────────────────────────────────────
    _log("\n🔍 Walidacja...")
    results = validate_cover(str(output_path), dim, _log)

    size_mb = output_path.stat().st_size / 1024 / 1024
    _log(f"\n📦 Rozmiar pliku: {size_mb:.1f} MB")
    return results


def _save_pdf(image: Image.Image, dim: CoverDimensions, output_path: str):
    """Save PIL image as a single-page PDF at correct KDP dimensions."""
    from reportlab.pdfgen import canvas as rl_canvas
    import tempfile, os

    # Save to temp PNG first
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
    image.save(tmp_path, dpi=(300, 300))

    try:
        w_pt = dim.total_w_px / dim.dpi * 72
        h_pt = dim.total_h_px / dim.dpi * 72

        c = rl_canvas.Canvas(output_path, pagesize=(w_pt, h_pt))
        c.setAuthor("Python Money Tools — KDP Cover Generator")
        c.setTitle("KDP Book Cover")
        c.drawImage(tmp_path, 0, 0, width=w_pt, height=h_pt,
                    preserveAspectRatio=False)
        c.showPage()
        c.save()

        # Post-process: add TrimBox / BleedBox via pypdf
        try:
            import pypdf
            bleed_pt = dim.bleed * 72
            trim_w_pt = dim.trim_w * 72
            trim_h_pt = dim.trim_h * 72
            spine_w_pt = dim.spine_w * 72

            reader = pypdf.PdfReader(output_path)
            writer = pypdf.PdfWriter()
            for page in reader.pages:
                page.mediabox.lower_left  = (0, 0)
                page.mediabox.upper_right = (w_pt, h_pt)
                page.bleedbox = page.mediabox
                # TrimBox covers the combined back+spine+front (without bleed)
                page.trimbox.lower_left  = (bleed_pt, bleed_pt)
                page.trimbox.upper_right = (w_pt - bleed_pt, h_pt - bleed_pt)
                writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
        except ImportError:
            pass  # pypdf optional — PDF still valid without trim boxes

    finally:
        os.unlink(tmp_path)


def validate_cover(pdf_path: str, dim: CoverDimensions, log=print) -> dict:
    """
    Validate generated PDF against KDP requirements.
    Returns dict with 'passed', 'failed', 'warnings' lists.
    """
    passed, failed, warnings = [], [], []

    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)

        # ✅ Single page
        if len(reader.pages) == 1:
            passed.append("✅ PDF ma dokładnie 1 stronę")
        else:
            failed.append(f"❌ PDF ma {len(reader.pages)} stron (oczekiwano 1)")

        # ✅ Page dimensions (within 2pt tolerance = ~0.007")
        page = reader.pages[0]
        mb = page.mediabox
        got_w = float(mb.width)
        got_h = float(mb.height)
        exp_w = dim.total_w_px / dim.dpi * 72
        exp_h = dim.total_h_px / dim.dpi * 72
        tol   = 2.0

        if abs(got_w - exp_w) <= tol and abs(got_h - exp_h) <= tol:
            passed.append(f"✅ Wymiary PDF: {got_w:.1f}×{got_h:.1f} pt (oczekiwano {exp_w:.1f}×{exp_h:.1f} pt)")
        else:
            failed.append(f"❌ Wymiary PDF: {got_w:.1f}×{got_h:.1f} pt (oczekiwano {exp_w:.1f}×{exp_h:.1f} pt)")

        # ✅ TrimBox exists
        if page.trimbox:
            passed.append("✅ TrimBox ustawiony")
        else:
            warnings.append("⚠️  TrimBox brak (pypdf niedostępny lub błąd)")

    except ImportError:
        warnings.append("⚠️  pypdf niedostępny — pominięto walidację struktury PDF")
    except Exception as e:
        failed.append(f"❌ Błąd walidacji PDF: {e}")

    # ✅ PNG validation (sample pixel check)
    png_path = Path(pdf_path).with_suffix(".png")
    if png_path.exists():
        from PIL import Image as _Image
        img = _Image.open(str(png_path))

        # Mode check
        if img.mode == "RGB":
            passed.append("✅ Tryb koloru: RGB")
        else:
            failed.append(f"❌ Tryb koloru: {img.mode} (oczekiwano RGB)")

        # Dimensions check (1px tolerance)
        if abs(img.size[0] - dim.total_w_px) <= 1 and abs(img.size[1] - dim.total_h_px) <= 1:
            passed.append(f"✅ Wymiary PNG: {img.size[0]}×{img.size[1]} px")
        else:
            failed.append(f"❌ Wymiary PNG: {img.size[0]}×{img.size[1]} px (oczekiwano {dim.total_w_px}×{dim.total_h_px})")

        # DPI check
        info = img.info
        dpi = info.get("dpi", (0, 0))
        if dpi[0] >= 299:
            passed.append(f"✅ DPI: {dpi[0]:.0f}")
        else:
            warnings.append(f"⚠️  DPI w metadanych: {dpi} (PIL może nie zapisywać dokładnie 300)")

        # Barcode zone — check that it is white
        bz = dim.barcode_zone
        sample_x = (bz["x1"] + bz["x2"]) // 2
        sample_y = (bz["y1"] + bz["y2"]) // 2
        try:
            pixel = img.getpixel((sample_x, sample_y))
            if all(c >= 250 for c in pixel[:3]):
                passed.append(f"✅ Strefa kodu kreskowego: biała (RGB {pixel[:3]})")
            else:
                failed.append(f"❌ Strefa kodu kreskowego nie jest biała: {pixel[:3]}")
        except Exception as e:
            warnings.append(f"⚠️  Nie można sprawdzić piksela kodu kreskowego: {e}")

    # Print summary
    log(f"\n{'='*50}")
    log(f"WALIDACJA KDP: {len(passed)} passed, {len(failed)} failed, {len(warnings)} warnings")
    for m in passed + warnings + failed:
        log(f"  {m}")
    log('='*50)

    return {"passed": passed, "failed": failed, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(
        description="Generuje okładkę KDP dla książki do kolorowania"
    )
    parser.add_argument("--title",    required=True,  help="Tytuł książki")
    parser.add_argument("--subtitle", required=True,  help="Podtytuł")
    parser.add_argument("--author",   required=True,  help="Imię i nazwisko autora")
    parser.add_argument("--pages",    type=int, default=48, help="Liczba stron wnętrza")
    parser.add_argument("--bullets",  nargs="+", default=[], help="Punkty na tylnej okładce")
    parser.add_argument("--hook",     default="",     help="Tekst catch-phrase na tylnej okładce")
    parser.add_argument("--tagline",  default="",     help="Stopka pod strefą kodu kreskowego")
    parser.add_argument("--author-bio", default="",  help="Krótki bio autora")
    parser.add_argument("--background", default=None, help="Ścieżka do obrazu tła (opcjonalne)")
    parser.add_argument("--decorative", default=None, help="Ścieżka do dekoracyjnego obrazu (opcjonalne)")
    parser.add_argument("--palette",  default="lavender",
                        choices=list(PALETTES.keys()), help="Paleta kolorów")
    parser.add_argument("--paper",    default="white", choices=["white","cream"],
                        help="Typ papieru (wpływa na szerokość grzbietu)")
    parser.add_argument("--output",   default="output/cover_final.pdf", help="Ścieżka wyjściowa PDF")
    parser.add_argument("--seed",     type=int, default=42, help="Seed dla generatora tła")
    args = parser.parse_args()

    default_bullets = [
        "Premium format 8.5×11 cali",
        "Jeden projekt na stronie",
        "Grube linie — idealne do kolorowania",
        "Doskonały prezent dla kobiet",
    ]
    bullets = args.bullets if args.bullets else default_bullets

    result = build_cover(
        title=args.title,
        subtitle=args.subtitle,
        author=args.author,
        description_bullets=bullets,
        page_count=args.pages,
        background_image_path=args.background,
        output_pdf=args.output,
        palette_name=args.palette,
        hook=args.hook,
        tagline=args.tagline,
        author_bio=args.author_bio,
        decorative_image_path=args.decorative,
        paper=args.paper,
        seed=args.seed,
    )

    failed = result.get("failed", [])
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
