def register_blueprints(app):
    from .main import bp as main_bp
    from .kdp import (
        activity_bp,
        builder_bp,
        coloring_bp,
        cover_bp,
        flashcard_bp,
        hub_bp,
        quotes_bp,
    )

    app.register_blueprint(main_bp)

    # KDP hub + sub-tools mounted under /kdp
    app.register_blueprint(hub_bp,       url_prefix='/kdp')
    app.register_blueprint(coloring_bp,  url_prefix='/kdp')
    app.register_blueprint(flashcard_bp, url_prefix='/kdp')
    app.register_blueprint(cover_bp,     url_prefix='/kdp')
    app.register_blueprint(builder_bp,   url_prefix='/kdp')
    app.register_blueprint(quotes_bp,    url_prefix='/kdp')
    app.register_blueprint(activity_bp,  url_prefix='/kdp')
