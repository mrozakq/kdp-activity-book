import os

from dotenv import load_dotenv
from flask import Flask

from blueprints import register_blueprints
from extensions import init_db

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-only-change-me')
    init_db()
    register_blueprints(app)
    return app


app = create_app()


if __name__ == '__main__':
    print('\n🚀 KDP Builder (standalone)')
    print('   Adres: http://localhost:5001\n')
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
