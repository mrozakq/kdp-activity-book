import os

from config import (
    KDP_BLEED_PX, KDP_BLEED_PT,
    KDP_MIN_PAGES,
    KDP_PAGE_H_PT, KDP_PAGE_H_PX,
    KDP_PAGE_W_PT, KDP_PAGE_W_PX,
    KDP_TRIM_H_PT, KDP_TRIM_W_PT,
)


def kdp_convert_grayscale(im, bw_mode: str = 'L'):
    """Convert PIL image to grayscale ('L') or pure B&W ('1')."""
    if bw_mode == '1':
        return im.convert('L').convert('1')
    return im.convert('L')


def kdp_add_bleed(im):
    """
    Extend canvas from 2550×3300 (trim) to 2625×3375 (trim + bleed).
    Background fills with white; original image is centred inside.
    Returns new image in same mode as input.
    """
    from PIL import Image
    mode = im.mode
    bg_color = 255 if mode == 'L' else (255, 255, 255, 255) if mode == 'RGBA' else (255, 255, 255)
    new_im = Image.new(mode, (KDP_PAGE_W_PX, KDP_PAGE_H_PX), bg_color)
    new_im.paste(im, (KDP_BLEED_PX, KDP_BLEED_PX))
    return new_im


def kdp_validate(images: list) -> dict:
    """
    Check KDP compliance for a list of image paths.
    Returns {'ok': bool, 'issues': [str]}.
    """
    from PIL import Image
    issues = []
    if len(images) < KDP_MIN_PAGES:
        issues.append(f'Za mało stron: {len(images)} (minimum KDP: {KDP_MIN_PAGES})')
    sizes = set()
    for p in images:
        try:
            with Image.open(p) as img:
                sizes.add(img.size)
                if img.mode not in ('L', '1'):
                    issues.append(f'{os.path.basename(p)}: tryb {img.mode} zamiast L/1 (grayscale)')
        except Exception as e:
            issues.append(f'{os.path.basename(p)}: błąd odczytu — {e}')
    if len(sizes) > 1:
        issues.append(f'Niezgodne rozmiary stron: {sizes}')
    return {'ok': len(issues) == 0, 'issues': issues}


def kdp_create_pdf(images: list, output_path: str, jlog_fn=None) -> dict:
    """
    Build KDP-compliant PDF:
    - Page size: 8.75" × 11.25" (with 0.125" bleed)
    - Each design page followed by blank page
    - Even total page count, minimum 24
    - TrimBox / BleedBox set via pypdf post-processing
    Returns {'ok': bool, 'pages': int, 'issues': [str]}
    """
    from reportlab.pdfgen import canvas as rl_canvas

    issues = []
    pages_written = 0

    # Pad to min 24 design pages
    design_pages = list(images)
    while len(design_pages) < (KDP_MIN_PAGES // 2):
        design_pages += images   # repeat until enough
    design_pages = design_pages[: max(len(design_pages), KDP_MIN_PAGES // 2)]

    if jlog_fn:
        jlog_fn(f'📄 Projektów stron: {len(design_pages)} → łącznie stron w PDF: {len(design_pages)*2}')

    c = rl_canvas.Canvas(str(output_path), pagesize=(KDP_PAGE_W_PT, KDP_PAGE_H_PT))
    c.setAuthor('Python Money Tools')
    c.setTitle('Coloring Book — KDP Edition')

    for i, img_path in enumerate(design_pages, 1):
        # ── Design page ──────────────────────────────
        try:
            c.drawImage(str(img_path), 0, 0,
                        width=KDP_PAGE_W_PT, height=KDP_PAGE_H_PT,
                        preserveAspectRatio=False)
        except Exception as e:
            issues.append(f'Strona {i}: {e}')
            c.setFillColorRGB(1, 1, 1)
            c.rect(0, 0, KDP_PAGE_W_PT, KDP_PAGE_H_PT, fill=1, stroke=0)
        c.showPage()
        pages_written += 1

        # ── Blank page (prevents ink bleed-through) ──
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, KDP_PAGE_W_PT, KDP_PAGE_H_PT, fill=1, stroke=0)
        c.showPage()
        pages_written += 1

        if jlog_fn and i % 5 == 0:
            jlog_fn(f'   → Zapisano {i}/{len(design_pages)} stron...')

    c.save()

    # ── Add TrimBox / BleedBox via pypdf ─────────────
    try:
        import pypdf
        reader = pypdf.PdfReader(str(output_path))
        writer = pypdf.PdfWriter()
        for page in reader.pages:
            page.mediabox.lower_left  = (0, 0)
            page.mediabox.upper_right = (KDP_PAGE_W_PT, KDP_PAGE_H_PT)
            page.bleedbox = page.mediabox
            # TrimBox is inset by bleed on all sides
            page.trimbox.lower_left  = (KDP_BLEED_PT, KDP_BLEED_PT)
            page.trimbox.upper_right = (KDP_BLEED_PT + KDP_TRIM_W_PT,
                                        KDP_BLEED_PT + KDP_TRIM_H_PT)
            writer.add_page(page)
        with open(str(output_path), 'wb') as f:
            writer.write(f)
        if jlog_fn:
            jlog_fn('✅ TrimBox / BleedBox ustawione (pypdf)')
    except ImportError:
        issues.append('pypdf nie zainstalowany — TrimBox pominięty (pip install pypdf)')
        if jlog_fn:
            jlog_fn('⚠️  pypdf niedostępny — TrimBox pominięty')
    except Exception as e:
        issues.append(f'pypdf błąd: {e}')
        if jlog_fn:
            jlog_fn(f'⚠️  TrimBox błąd: {e}')

    return {'ok': len(issues) == 0, 'pages': pages_written, 'issues': issues}
