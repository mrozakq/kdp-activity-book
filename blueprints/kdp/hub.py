from flask import Blueprint, render_template

bp = Blueprint('kdp_hub', __name__)


@bp.route('/', strict_slashes=False)
def hub():
    return render_template('kdp.html')
