import os
import logging
import traceback
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate, upgrade
from db import db, init_db

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # List the *exact* origins you expect, matching protocol + domain
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "https://aoe2-betting.vercel.app",
        "https://aoe2hd-frontend.onrender.com"
    ]

    # Let Flask-CORS handle everything, including OPTIONS preflight
    CORS(
        app,
        supports_credentials=True,
        origins=allowed_origins,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "OPTIONS"]
    )

    # Build DB connection string
    raw_db_url = os.getenv("DATABASE_URL")
    if not raw_db_url:
        user = os.getenv("PGUSER", "aoe2user")
        pw = os.getenv("PGPASSWORD", "secretpassword")
        host = os.getenv("PGHOST", "db")
        port = os.getenv("PGPORT", "5432")
        dbname = os.getenv("PGDATABASE", "aoe2db")
        raw_db_url = f"postgresql://{user}:{pw}@{host}:{port}/{dbname}"

    # Convert "postgres://" -> "postgresql://" if needed
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # If on Render or "render.com" is in the DB URL, require SSL
    if "RENDER" in os.environ or "render.com" in raw_db_url:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"sslmode": "require"}
        }

    # Initialize and migrate DB
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

    # Example user route
    @app.route("/me", methods=["GET", "POST"])
    def me_alias():
        from routes.user_routes import get_user_by_uid
        return get_user_by_uid()

    # Optional healthcheck route to confirm the app is running
    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok"}, 200

    # Global error handler to catch *unhandled* exceptions
    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error("Unhandled exception occurred", exc_info=e)
        # Return a JSON response so you can see the error in the logs
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500

    return app

app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, host="0.0.0.0", port=8002)
