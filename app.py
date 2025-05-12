from flask import Flask, send_from_directory
from models import db
import os


def create_app():
    app = Flask(__name__, static_folder='static')
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///fitwear.sqlite3"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-123'
    app.config['IMAGES_FOLDER'] = os.path.join(os.path.dirname(__file__), 'images')
    app.config['MAJOR_IMAGES_FOLDER'] = os.path.join(os.path.dirname(__file__), 'major_images')  # Ensure this matches
    app.debug = True

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # Serve project root images (silhouettes)
    @app.route('/images/<path:filename>')
    def serve_root_images(filename):
        try:
            return send_from_directory(app.config['IMAGES_FOLDER'], filename)
        except FileNotFoundError:
            print(f"Root image not found: {os.path.join(app.config['IMAGES_FOLDER'], filename)}")
            return "", 404

    # Serve major images (clothing)
    @app.route('/major_images/<path:filename>')
    def serve_major_images(filename):
        try:
            return send_from_directory(app.config['MAJOR_IMAGES_FOLDER'], filename)
        except FileNotFoundError:
            print(f"Major image not found: {os.path.join(app.config['MAJOR_IMAGES_FOLDER'], filename)}")  # Add debug print
            return "", 404

    # Register routes
    from login_controllers import init_login_routes
    from user_controllers import init_user_routes
    from main_controllers import init_main_routes
    init_login_routes(app)
    init_user_routes(app)
    init_main_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=8080)