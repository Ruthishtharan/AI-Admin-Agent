import io
import csv
import json
import queue
import threading
import os
from functools import wraps
from flask import (
    render_template, request, redirect, url_for,
    flash, jsonify, session, Response, stream_with_context,
)
from app.models import (
    load_users, find_user, create_user as model_create_user,
    reset_password, disable_user, enable_user, delete_user,
    assign_license, assign_role, user_exists,
    bulk_disable, bulk_delete, load_audit_log, _audit,
)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Marketing", "Sales",
    "HR", "Finance", "Legal", "IT", "Operations",
    "Customer Support", "Management",
]


# ── Auth decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def register_routes(app):

    # ── Login / Logout ────────────────────────────────────────────────────────
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("authenticated"):
            return redirect(url_for("home"))
        if request.method == "POST":
            if request.form.get("password") == ADMIN_PASSWORD:
                session["authenticated"] = True
                _audit("login", details="Admin logged in", actor="admin")
                return redirect(url_for("home"))
            flash("Incorrect password.", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    # ── Dashboard ─────────────────────────────────────────────────────────────
    @app.route("/")
    @login_required
    def home():
        users = load_users()
        stats = {
            "total":    len(users),
            "active":   sum(1 for u in users if u.get("status") == "active"),
            "inactive": sum(1 for u in users if u.get("status") == "inactive"),
            "admins":   sum(1 for u in users if u.get("role") == "admin"),
        }
        return render_template("dashboard.html", stats=stats, recent_users=users[-5:])

    # ── Users list ────────────────────────────────────────────────────────────
    @app.route("/users")
    @login_required
    def users():
        all_users = load_users()
        active   = sum(1 for u in all_users if u.get("status") == "active")
        inactive = sum(1 for u in all_users if u.get("status") == "inactive")
        return render_template("users.html", users=all_users,
                               active=active, inactive=inactive)

    # ── Create user ───────────────────────────────────────────────────────────
    @app.route("/create-user", methods=["GET", "POST"])
    @login_required
    def create_user():
        if request.method == "POST":
            email       = request.form.get("email", "").strip()
            name        = request.form.get("name", "").strip()
            role        = request.form.get("role", "employee")
            department  = request.form.get("department", "").strip()
            license_type = request.form.get("license", "None")

            if not email or not name:
                flash("Email and name are required.", "danger")
                return render_template("create_user.html", departments=DEPARTMENTS)
            if not department:
                flash("Department is required.", "danger")
                return render_template("create_user.html", departments=DEPARTMENTS)
            if user_exists(email):
                flash(f"User {email} already exists.", "danger")
                return render_template("create_user.html", departments=DEPARTMENTS)

            model_create_user(email, name, role, department, license_type)
            flash(f"User {name} ({email}) created successfully.", "success")
            return redirect(url_for("users"))

        return render_template("create_user.html", departments=DEPARTMENTS)

    # ── Reset password ────────────────────────────────────────────────────────
    @app.route("/reset-password/<email>", methods=["GET", "POST"])
    @login_required
    def reset_password_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))
        if request.method == "POST":
            reset_password(email)
            flash(f"Password has been reset for {email}.", "success")
            return redirect(url_for("users"))
        return render_template("reset_password.html", user=user)

    # ── Disable / Enable / Delete ─────────────────────────────────────────────
    @app.route("/disable-user/<email>", methods=["GET", "POST"])
    @login_required
    def disable_user_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))
        if request.method == "POST":
            disable_user(email)
            flash(f"User {email} has been disabled.", "success")
            return redirect(url_for("users"))
        return render_template("confirm_action.html", user=user, action="Disable",
                               action_url=url_for("disable_user_view", email=email), danger=True)

    @app.route("/enable-user/<email>", methods=["GET", "POST"])
    @login_required
    def enable_user_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))
        if request.method == "POST":
            enable_user(email)
            flash(f"User {email} has been enabled.", "success")
            return redirect(url_for("users"))
        return render_template("confirm_action.html", user=user, action="Enable",
                               action_url=url_for("enable_user_view", email=email), danger=False)

    @app.route("/delete-user/<email>", methods=["GET", "POST"])
    @login_required
    def delete_user_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))
        if request.method == "POST":
            delete_user(email)
            flash(f"User {email} has been deleted.", "success")
            return redirect(url_for("users"))
        return render_template("confirm_action.html", user=user, action="Delete",
                               action_url=url_for("delete_user_view", email=email), danger=True)

    # ── Assign license / role ─────────────────────────────────────────────────
    @app.route("/assign-license/<email>", methods=["GET", "POST"])
    @login_required
    def assign_license_view(email):
        user = find_user(email)
        if not user:
            flash(f"User {email} not found.", "danger")
            return redirect(url_for("users"))
        if request.method == "POST":
            license_type = request.form.get("license", "None")
            role         = request.form.get("role", user.get("role", "employee"))
            assign_license(email, license_type)
            assign_role(email, role)
            flash(f"Role and license updated for {email}.", "success")
            return redirect(url_for("users"))
        return render_template("assign_license.html", user=user)

    # ── Bulk actions ──────────────────────────────────────────────────────────
    @app.route("/bulk-action", methods=["POST"])
    @login_required
    def bulk_action():
        action = request.form.get("action")
        emails = request.form.getlist("selected")
        if not emails:
            flash("No users selected.", "warning")
            return redirect(url_for("users"))
        if action == "disable":
            n = bulk_disable(emails)
            flash(f"Disabled {n} user(s).", "success")
        elif action == "delete":
            n = bulk_delete(emails)
            flash(f"Deleted {n} user(s).", "success")
        else:
            flash("Unknown action.", "danger")
        return redirect(url_for("users"))

    # ── Export CSV ────────────────────────────────────────────────────────────
    @app.route("/export-csv")
    @login_required
    def export_csv():
        users = load_users()
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "email", "name", "role", "department", "status", "license",
            "created_at", "password_reset_at",
        ])
        writer.writeheader()
        writer.writerows(users)
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=users.csv"},
        )

    # ── Audit log page ────────────────────────────────────────────────────────
    @app.route("/audit")
    @login_required
    def audit():
        logs = load_audit_log(limit=200)
        return render_template("audit.html", logs=logs)

    # ── AI Chat UI ────────────────────────────────────────────────────────────
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

        task = data["task"]
        q    = queue.Queue()

        def progress_callback(step, message):
            q.put({"type": "step", "step": step, "message": str(message)})

        def run():
            try:
                result = run_agent(task, progress_callback=progress_callback)
                _audit("ai_task", details=task[:200], actor="AI Agent")
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

        return Response(generate(), content_type="text/event-stream",
                        headers={"X-Accel-Buffering": "no",
                                 "Cache-Control": "no-cache"})

    # ── JSON API ──────────────────────────────────────────────────────────────
    @app.route("/api/users")
    @login_required
    def api_users():
        return jsonify(load_users())
