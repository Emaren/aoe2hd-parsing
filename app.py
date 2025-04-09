import os
import logging
from flask import Flask, request
from flask_cors import CORS
from flask_migrate import Migrate, upgrade
from db import db, init_db

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "https://aoe2-betting.vercel.app",
        "https://aoe2hd-frontend.onrender.com"
    ]

    # ✅ Configure CORS with full support for preflight (OPTIONS)
    CORS(app,
         supports_credentials=True,
         origins=allowed_origins,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "OPTIONS"])

    # Build DB connection string
    raw_db_url = os.getenv("DATABASE_URL")
    if not raw_db_url:
        user = os.getenv("PGUSER", "aoe2user")
        pw = os.getenv("PGPASSWORD", "secretpassword")
        host = os.getenv("PGHOST", "db")
        port = os.getenv("PGPORT", "5432")
        dbname = os.getenv("PGDATABASE", "aoe2db")
        raw_db_url = f"postgresql://{user}:{pw}@{host}:{port}/{dbname}"

    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if "RENDER" in os.environ or "render.com" in raw_db_url:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"sslmode": "require"}
        }

    init_db(app)
    migrate.init_app(app, db)

    with app.app_context():
        try:
            upgrade()
        except Exception as e:
            logging.warning(f"Auto-migrate failed: {e}")

    # Register blueprints
    from routes.replay_routes import replay_bp
    from routes.user_routes import user_bp
    from routes.debug_routes import debug_bp
    from routes.admin_routes import admin_bp

    app.register_blueprint(replay_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(debug_bp)
    app.register_blueprint(admin_bp)

    @app.route("/me", methods=["GET", "POST"])
    def me_alias():
        from routes.user_routes import get_user_by_uid
        return get_user_by_uid()

    # 🔒 Add CORS headers manually for non-api routes if needed
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

    return app

app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, host="0.0.0.0", port=8002)
