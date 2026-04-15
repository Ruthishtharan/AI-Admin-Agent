import os
from flask import Flask, render_template
from app.routes import register_routes


def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "it-admin-panel-secret-key-2024")

    # Init SQLite DB (creates tables + seeds users on first run)
    from app.models import init_db
    init_db()

    # Make helpers available in all templates
    from app.models import load_users, load_profile
    @app.context_processor
    def inject_globals():
        return {"load_users": load_users, "load_profile": load_profile}

    register_routes(app)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("404.html", code=500, message="Internal server error"), 500

    return app
