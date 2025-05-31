from flask import Flask
from src.routes import setup_routes
from src.utils import ensure_templates

def create_app():
    app = Flask(__name__, template_folder='templates')
    setup_routes(app)
    ensure_templates()
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
