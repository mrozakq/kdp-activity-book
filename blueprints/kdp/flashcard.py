import csv
import io
import os
import threading
import uuid
import zipfile

from flask import Blueprint, jsonify, render_template, request

from config import BG_COLORS, BG_NAMES, FLASHCARD_DIR, RESULTS_DIR, UPLOAD_DIR
from extensions import db_last, db_save, db_update
from jobs import create_job, jdone, jerror, jlog

bp = Blueprint('flashcard', __name__)


@bp.route('/flashcard')
def flashcard():
    return render_template('flashcard.html',
                           colors=list(zip(BG_COLORS, BG_NAMES)),
                           last=db_last('flashcard'))


@bp.route('/flashcard/run', methods=['POST'])
def flashcard_run():
    csv_file = request.files.get('csv_file')
    images = request.files.getlist('images')
    active_colors = request.form.getlist('colors') or BG_COLORS
    random_colors = request.form.get('random_colors', 'true') == 'true'

    if not csv_file or not csv_file.filename:
        return jsonify({'error': 'Prześlij plik CSV z danymi kart'}), 400

    content = csv_file.read().decode('utf-8-sig')
    up_dir = UPLOAD_DIR / str(uuid.uuid4())
    up_dir.mkdir(parents=True)
    img_map = {}
    for img in images:
        if img.filename:
            p = up_dir / os.path.basename(img.filename)
            img.save(str(p))
            img_map[os.path.basename(img.filename)] = str(p)

    jid = create_job()
    rid = db_save('flashcard', {'random_colors': random_colors, 'colors': len(active_colors)})

    def run():
        try:
            from PIL import Image, ImageDraw, ImageFont as PILFont, ImageChops
            from random import randint

            fp = FLASHCARD_DIR / 'data' / 'fonts' / 'GentySans-Regular' / 'GentySans-Regular.ttf'
            pw, ph = 1500, 2100
            cr = 50

            delim = ',' if ',' in content.split('\n')[0] else ';'
            rdr = csv.DictReader(io.StringIO(content), delimiter=delim)
            rows = list(rdr)

            res_dir = RESULTS_DIR / jid
            res_dir.mkdir(exist_ok=True)

            def rc(im, rad=50):
                bs = (im.size[0] * 3, im.size[1] * 3)
                mask = Image.new('L', bs, 0)
                ImageDraw.Draw(mask).rounded_rectangle((0, 0) + bs, fill=255, radius=rad)
                mask = mask.resize(im.size, Image.LANCZOS)
                mask = ImageChops.darker(mask, im.split()[-1])
                im.putalpha(mask)
                return im

            generated = []
            for cnt, row in enumerate(rows, 1):
                vals = list(row.values())
                text_top = (row.get('text_top') or row.get('Text 1') or
                            (vals[0] if vals else '')).strip()
                text_bot = (row.get('text_bottom') or row.get('Text 2') or
                            (vals[1] if len(vals) > 1 else '')).strip()
                img_col = (row.get('image_path') or row.get('image') or
                           (vals[2] if len(vals) > 2 else '')).strip()

                jlog(jid, f'📚 [{cnt}/{len(rows)}] "{text_top[:40]}"')

                if random_colors:
                    color = active_colors[randint(0, len(active_colors) - 1)]
                else:
                    color = active_colors[cnt % len(active_colors)]

                im = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
                draw = ImageDraw.Draw(im)
                draw.rounded_rectangle((0, 0, pw, ph), fill=color, radius=cr)

                ip = img_map.get(os.path.basename(img_col)) or (img_col if os.path.exists(img_col) else None)
                if ip:
                    try:
                        pi = Image.open(ip).convert('RGBA')
                        tw = pw - 500
                        wp = tw / float(pi.size[0])
                        pi = pi.resize((tw, int(pi.size[1] * wp)), Image.LANCZOS)
                        ox = (pw - pi.size[0]) // 2
                        oy = (ph - pi.size[1]) // 2
                        im.alpha_composite(pi, (ox, oy))
                    except Exception:
                        pass

                if text_top:
                    font_t = PILFont.truetype(str(fp), 250)
                    draw.text((pw // 2, 350), text_top, anchor='ms', align='center',
                              font=font_t, fill='#272B35', spacing=4)
                if text_bot:
                    font_b = PILFont.truetype(str(fp), 200)
                    draw.text((pw // 2, ph - 200), text_bot, anchor='ms', align='center',
                              font=font_b, fill='#272B35', spacing=4)

                rc(im, cr * 3.05)
                out = res_dir / f'{cnt}.png'
                im.save(str(out), dpi=(300, 300))
                generated.append(str(out))
                jlog(jid, f'   ✅ {cnt}.png')

            zip_path = RESULTS_DIR / f'{jid}_flashcards.zip'
            with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
                for p in generated:
                    zf.write(p, os.path.basename(p))
            jlog(jid, f'📦 ZIP: {len(generated)} kart')
            jdone(jid, str(zip_path), len(generated))
            db_update(rid, 'done', len(generated))
        except Exception as e:
            import traceback
            jlog(jid, traceback.format_exc())
            jerror(jid, str(e))
            db_update(rid, 'error')

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': jid})
