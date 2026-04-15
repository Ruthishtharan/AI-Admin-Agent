import json
import queue
import threading
import os
import base64
from functools import wraps
from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, session, Response, stream_with_context,
)
from app.models import (
    load_profile, save_profile,
    save_feedback, load_feedback,
    save_pin, verify_pin, has_pin,
    _audit,
)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# ── Auth decorator ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def register_routes(app):

    # ── Login / Logout ──────────────────────────────────────────────────────
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("authenticated"):
            return redirect(url_for("chat"))
        if request.method == "POST":
            if request.form.get("password") == ADMIN_PASSWORD:
                session["authenticated"] = True
                _audit("login", details="Vexa admin logged in", actor="admin")
                return redirect(url_for("chat"))
            flash("Incorrect password.", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    # ── Home → Chat ─────────────────────────────────────────────────────────
    @app.route("/")
    @login_required
    def home():
        return redirect(url_for("chat"))

    # ── Vexa Chat UI ─────────────────────────────────────────────────────────
    @app.route("/chat")
    @login_required
    def chat():
        return render_template("chat.html")

    # ── SSE streaming chat API ────────────────────────────────────────────────
    @app.route("/api/chat", methods=["POST"])
    @login_required
    def chat_api():
        from agent.agent import run_agent

        data = request.get_json()
        if not data or not data.get("task"):
            return jsonify({"error": "No task provided"}), 400

        task         = data["task"]
        show_browser = bool(data.get("show_browser", True))  # default: show browser

        q = queue.Queue()

        def progress_callback(step: str, message: str):
            q.put({"type": "step", "step": step, "message": str(message)})

        def run():
            try:
                result = run_agent(
                    task,
                    progress_callback=progress_callback,
                    show_browser=show_browser,
                )
                _audit("ai_task", details=task[:200], actor="Vexa")
                q.put({"type": "done", "result": result})
            except Exception as e:
                q.put({"type": "error", "error": str(e)})
            finally:
                q.put(None)  # sentinel

        threading.Thread(target=run, daemon=True).start()

        @stream_with_context
        def generate():
            while True:
                item = q.get()
                if item is None:
                    break
                yield f"data: {json.dumps(item)}\n\n"

        return Response(
            generate(),
            content_type="text/event-stream",
            headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
        )

    # ── Profile ───────────────────────────────────────────────────────────────
    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            photo = ""
            if "photo" in request.files:
                f = request.files["photo"]
                if f and f.filename:
                    data = f.read()
                    mime = f.content_type or "image/jpeg"
                    photo = f"data:{mime};base64,{base64.b64encode(data).decode()}"
            current = load_profile()
            save_profile({
                "name":  request.form.get("name",  current.get("name", "Admin")),
                "title": request.form.get("title", current.get("title", "")),
                "email": request.form.get("email", current.get("email", "")),
                "phone": request.form.get("phone", current.get("phone", "")),
                "photo": photo or current.get("photo", ""),
            })
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))
        return render_template("profile.html", profile=load_profile())

    # ── Feedback ──────────────────────────────────────────────────────────────
    @app.route("/api/feedback", methods=["POST"])
    @login_required
    def api_feedback():
        data    = request.get_json() or {}
        rating  = int(data.get("rating", 0))
        comment = data.get("comment", "")[:500]
        task    = data.get("task", "")[:300]
        if 1 <= rating <= 5:
            save_feedback(rating, comment, task)
        return jsonify({"ok": True})

    @app.route("/feedback")
    @login_required
    def feedback_page():
        return render_template("feedback.html", entries=load_feedback())

    # ── PIN auth ──────────────────────────────────────────────────────────────
    @app.route("/api/pin/set", methods=["POST"])
    def pin_set():
        data     = request.get_json() or {}
        pin_hash = data.get("hash", "")
        if pin_hash and len(pin_hash) == 64:
            save_pin(pin_hash)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Invalid PIN hash"}), 400

    @app.route("/api/pin/auth", methods=["POST"])
    def pin_auth():
        data     = request.get_json() or {}
        pin_hash = data.get("hash", "")
        if verify_pin(pin_hash):
            session["authenticated"] = True
            _audit("login", details="PIN sign-in", actor="admin")
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Incorrect PIN"}), 401

    @app.route("/api/pin/exists")
    def pin_exists():
        return jsonify({"exists": has_pin()})
