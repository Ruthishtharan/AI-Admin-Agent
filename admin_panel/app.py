"""
Mock IT Admin Panel — standalone Flask app on port 5001.
This is the TARGET website that Vexa navigates like a human.
"""
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, g,
)

# ── App setup ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "data", "users.db")
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("ADMIN_PANEL_SECRET", "admin-panel-secret-2024")

ADMIN_PASSWORD = os.getenv("ADMIN_PANEL_PASSWORD", "admin123")

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Marketing", "Sales",
    "HR", "Finance", "Legal", "IT", "Operations",
    "Customer Support", "Management",
]
LICENSES = [
    "None",
    "Microsoft 365 E1", "Microsoft 365 E3", "Microsoft 365 E5",
    "Google Workspace Basic", "Google Workspace Business",
]
ROLES = ["employee", "admin", "contractor", "guest"]


# ── Database ──────────────────────────────────────────────────────────────────

def get_db():
    if not hasattr(g, "_db"):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        g._db = conn
    return g._db


@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                email            TEXT    UNIQUE NOT NULL,
                name             TEXT    NOT NULL,
                role             TEXT    DEFAULT 'employee',
                department       TEXT    DEFAULT '',
                license          TEXT    DEFAULT 'None',
                status           TEXT    DEFAULT 'active',
                created_at       TEXT    DEFAULT (datetime('now')),
                password_reset_at TEXT
            )
        """)
        # Seed demo users (INSERT OR IGNORE so re-runs are safe)
        seeds = [
            ("john.doe@company.com",   "John Doe",    "admin",      "IT",          "Microsoft 365 E5", "active"),
            ("jane.smith@company.com", "Jane Smith",  "employee",   "HR",          "Microsoft 365 E1", "active"),
            ("bob.johnson@company.com","Bob Johnson",  "contractor", "Engineering", "None",             "inactive"),
            ("sara.lee@company.com",   "Sara Lee",    "employee",   "Marketing",   "Google Workspace Basic", "active"),
        ]
        for row in seeds:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO users (email,name,role,department,license,status) VALUES (?,?,?,?,?,?)",
                    row,
                )
            except Exception:
                pass


init_db()


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin"):
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("dashboard"))
        error = "Incorrect password. Please try again."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    db    = get_db()
    users = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    total    = len(users)
    active   = sum(1 for u in users if u["status"] == "active")
    inactive = total - active
    admins   = sum(1 for u in users if u["role"] == "admin")
    recent   = users[:5]
    return render_template(
        "dashboard.html",
        total=total, active=active, inactive=inactive, admins=admins,
        recent=recent,
    )


@app.route("/users")
@login_required
def users():
    db    = get_db()
    all_u = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return render_template("users.html", users=all_u)


@app.route("/users/create", methods=["GET", "POST"])
@login_required
def create_user():
    if request.method == "POST":
        email        = request.form.get("email", "").strip().lower()
        name         = request.form.get("name",  "").strip()
        role         = request.form.get("role",  "employee")
        department   = request.form.get("department", "")
        license_type = request.form.get("license", "None")

        if not email or not name:
            flash("Email and full name are required.", "error")
            return render_template("create_user.html",
                                   departments=DEPARTMENTS,
                                   licenses=LICENSES, roles=ROLES)
        if not department:
            flash("Please select a department.", "error")
            return render_template("create_user.html",
                                   departments=DEPARTMENTS,
                                   licenses=LICENSES, roles=ROLES)

        db = get_db()
        existing = db.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            flash(f"A user with email {email} already exists.", "error")
            return render_template("create_user.html",
                                   departments=DEPARTMENTS,
                                   licenses=LICENSES, roles=ROLES)

        db.execute(
            "INSERT INTO users (email, name, role, department, license, status) VALUES (?,?,?,?,?,'active')",
            (email, name, role, department, license_type),
        )
        db.connection.commit() if hasattr(db, 'connection') else db.execute("SELECT 1")
        # sqlite3 connection in WAL mode — commit via context or explicit
        get_db().execute("SELECT 1")  # ensure write flushed
        flash(f"User '{name}' ({email}) has been created successfully!", "success")
        return redirect(url_for("users"))

    return render_template("create_user.html",
                           departments=DEPARTMENTS,
                           licenses=LICENSES, roles=ROLES)


@app.route("/users/<path:email>/disable", methods=["POST"])
@login_required
def disable_user(email):
    get_db().execute("UPDATE users SET status='inactive' WHERE email=?", (email,))
    flash(f"User {email} has been disabled.", "success")
    return redirect(url_for("users"))


@app.route("/users/<path:email>/enable", methods=["POST"])
@login_required
def enable_user(email):
    get_db().execute("UPDATE users SET status='active' WHERE email=?", (email,))
    flash(f"User {email} has been enabled.", "success")
    return redirect(url_for("users"))


@app.route("/users/<path:email>/delete", methods=["POST"])
@login_required
def delete_user(email):
    get_db().execute("DELETE FROM users WHERE email=?", (email,))
    flash(f"User {email} has been deleted.", "success")
    return redirect(url_for("users"))


@app.route("/users/<path:email>/reset-password", methods=["POST"])
@login_required
def reset_password(email):
    get_db().execute(
        "UPDATE users SET password_reset_at=datetime('now') WHERE email=?", (email,)
    )
    flash(f"Password has been reset for {email}.", "success")
    return redirect(url_for("users"))


# ── Commit helper ─────────────────────────────────────────────────────────────
# sqlite3 in WAL mode with row_factory needs explicit commit on the connection

@app.after_request
def commit_db(response):
    db = getattr(g, "_db", None)
    if db is not None:
        try:
            db.commit()
        except Exception:
            pass
    return response


if __name__ == "__main__":
    port = int(os.getenv("ADMIN_PANEL_PORT", "5001"))
    app.run(host="127.0.0.1", port=port, debug=False)
