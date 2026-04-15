import os
from flask import Flask, render_template, g
from app.routes import register_routes


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "it-admin-panel-secret-key-2024")

    # Init SQLite DB (creates tables + seeds users on first run)
    from app.models import init_db
    init_db()

    # Cache DB reads once per request using Flask's g object
    from app.models import load_users, load_profile

    def _cached_load_users():
        if not hasattr(g, "_users"):
            g._users = load_users()
        return g._users

    def _cached_load_profile():
        if not hasattr(g, "_profile"):
            g._profile = load_profile()
        return g._profile

    @app.context_processor
    def inject_globals():
        return {"load_users": _cached_load_users, "load_profile": _cached_load_profile}

    register_routes(app)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("404.html", code=500, message="Internal server error"), 500

    return app
