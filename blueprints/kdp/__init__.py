# KDP hub sub-blueprints.
# Note on DB: extensions.db_save uses tool_name strings 'coloring',
# 'flashcard', 'cover' — kept as-is so historical 'runs' rows stay readable.
from .activity import bp as activity_bp
from .builder import bp as builder_bp
from .coloring import bp as coloring_bp
from .cover import bp as cover_bp
from .flashcard import bp as flashcard_bp
from .hub import bp as hub_bp
from .quotes import bp as quotes_bp
