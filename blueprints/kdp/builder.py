from flask import Blueprint, render_template

from config import COVER_PALETTES, FONT_MAP

bp = Blueprint('kdp_builder', __name__)


@bp.route('/builder')
def kdp_book():
    return render_template('kdp_book.html',
                           palettes=COVER_PALETTES,
                           fonts=list(FONT_MAP.keys()))
