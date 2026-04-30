import os
from flask import Flask, send_from_directory
from app.extensions import db
from app.config import config_map


def create_app(config_name: str = None) -> Flask:
    """
    Factory function untuk membuat instance aplikasi Flask.
    Pola ini disebut Application Factory Pattern.
    """
    app = Flask(__name__, static_folder="../static")

    # Tentukan konfigurasi yang digunakan
    env = config_name or os.getenv("FLASK_ENV", "development")
    cfg = config_map.get(env, config_map["default"])
    app.config.from_object(cfg)

    # Inisialisasi ekstensi
    db.init_app(app)

    # Registrasi blueprint / routes
    from app.routes.question_routes import question_bp
    app.register_blueprint(question_bp)

    # Buat tabel database jika belum ada
    with app.app_context():
        _ensure_db_dir()
        db.create_all()

    # Serve frontend SPA dari static/index.html
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        static_dir = os.path.join(app.root_path, "..", "static")
        if path and os.path.exists(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
        return send_from_directory(static_dir, "index.html")

    return app


def _ensure_db_dir():
    """Membuat folder db/ jika belum ada."""
    db_dir = os.path.join(os.path.dirname(__file__), "..", "db")
    os.makedirs(db_dir, exist_ok=True)
