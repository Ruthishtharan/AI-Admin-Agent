import sqlite3
import os
import json
from datetime import datetime
from contextlib import contextmanager

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE        = os.path.dirname(os.path.abspath(__file__))
DB_PATH      = os.path.join(_HERE, "..", "data", "users.db")
PROFILE_PATH = os.path.join(_HERE, "..", "data", "profile.json")
WEBAUTHN_PATH = os.path.join(_HERE, "..", "data", "webauthn.json")

# ── DB connection ─────────────────────────────────────────────────────────────
@contextmanager
def _db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create tables and seed default users if DB is new."""
    with _db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                email             TEXT PRIMARY KEY,
                name              TEXT NOT NULL,
                role              TEXT DEFAULT 'employee',
                department        TEXT DEFAULT '',
                status            TEXT DEFAULT 'active',
                license           TEXT DEFAULT 'None',
                created_at        TEXT,
                password_reset_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                action      TEXT NOT NULL,
                target      TEXT,
                details     TEXT,
                actor       TEXT DEFAULT 'system'
            );
        """)

        # Seed only when the table is empty
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            seed = [
                ("john.doe@company.com",  "John Doe",    "employee",   "Engineering", "active",   "Microsoft 365 E3", "2024-01-10"),
                ("jane.smith@company.com","Jane Smith",   "admin",      "IT",          "active",   "Microsoft 365 E5", "2023-06-15"),
                ("bob.johnson@company.com","Bob Johnson", "contractor", "Marketing",   "inactive", "None",             "2024-03-20"),
                ("sarah.lee@company.com", "Sarah Lee",   "employee",   "HR",          "active",   "Microsoft 365 E1", "2024-02-05"),
                ("mike.ross@company.com", "Mike Ross",   "contractor", "Legal",       "active",   "None",             "2024-01-20"),
            ]
            conn.executemany(
                "INSERT INTO users (email,name,role,department,status,license,created_at)"
                " VALUES (?,?,?,?,?,?,?)",
                seed,
            )


# ── Helpers ───────────────────────────────────────────────────────────────────
def _row_to_dict(row) -> dict:
    return dict(row) if row else None


# ── User CRUD ─────────────────────────────────────────────────────────────────
def load_users() -> list[dict]:
    with _db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY name").fetchall()
        return [dict(r) for r in rows]


def find_user(email: str) -> dict | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(email)=LOWER(?)", (email,)
        ).fetchone()
        return _row_to_dict(row)


def user_exists(email: str) -> bool:
    return find_user(email) is not None


def create_user(email, name, role="employee", department="", license_type="None") -> dict:
    now = datetime.now().strftime("%Y-%m-%d")
    with _db() as conn:
        conn.execute(
            "INSERT INTO users (email,name,role,department,status,license,created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (email, name, role, department, "active", license_type, now),
        )
    _audit("create_user", email, f"Created {name} as {role} in {department}")
    return find_user(email)


def reset_password(email: str) -> bool:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with _db() as conn:
        rows = conn.execute(
            "UPDATE users SET password_reset_at=? WHERE LOWER(email)=LOWER(?)",
            (now, email),
        ).rowcount
    if rows:
        _audit("reset_password", email, f"Password reset at {now}")
    return bool(rows)


def disable_user(email: str) -> bool:
    with _db() as conn:
        rows = conn.execute(
            "UPDATE users SET status='inactive' WHERE LOWER(email)=LOWER(?)", (email,)
        ).rowcount
    if rows:
        _audit("disable_user", email, "Account disabled")
    return bool(rows)


def enable_user(email: str) -> bool:
    with _db() as conn:
        rows = conn.execute(
            "UPDATE users SET status='active' WHERE LOWER(email)=LOWER(?)", (email,)
        ).rowcount
    if rows:
        _audit("enable_user", email, "Account enabled")
    return bool(rows)


def delete_user(email: str) -> bool:
    with _db() as conn:
        rows = conn.execute(
            "DELETE FROM users WHERE LOWER(email)=LOWER(?)", (email,)
        ).rowcount
    if rows:
        _audit("delete_user", email, "Account deleted permanently")
    return bool(rows)


def assign_license(email: str, license_type: str) -> bool:
    with _db() as conn:
        rows = conn.execute(
            "UPDATE users SET license=? WHERE LOWER(email)=LOWER(?)",
            (license_type, email),
        ).rowcount
    if rows:
        _audit("assign_license", email, f"License set to {license_type}")
    return bool(rows)


def assign_role(email: str, role: str) -> bool:
    with _db() as conn:
        rows = conn.execute(
            "UPDATE users SET role=? WHERE LOWER(email)=LOWER(?)", (role, email)
        ).rowcount
    if rows:
        _audit("assign_role", email, f"Role set to {role}")
    return bool(rows)


# ── Bulk operations ───────────────────────────────────────────────────────────
def bulk_disable(emails: list[str]) -> int:
    count = 0
    for email in emails:
        if disable_user(email):
            count += 1
    return count


def bulk_delete(emails: list[str]) -> int:
    count = 0
    for email in emails:
        if delete_user(email):
            count += 1
    return count


# ── Audit log ─────────────────────────────────────────────────────────────────
def _audit(action: str, target: str = None, details: str = None, actor: str = "AI Agent"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _db() as conn:
        conn.execute(
            "INSERT INTO audit_log (timestamp,action,target,details,actor) VALUES (?,?,?,?,?)",
            (now, action, target, details, actor),
        )


def load_audit_log(limit: int = 100) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


# ── Profile ───────────────────────────────────────────────────────────────────
def load_profile() -> dict:
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH) as f:
            return json.load(f)
    return {"name": "Admin", "title": "IT Administrator", "email": "", "phone": "", "photo": ""}


def save_profile(data: dict) -> None:
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        json.dump(data, f)


# ── Feedback ──────────────────────────────────────────────────────────────────
def save_feedback(rating: int, comment: str, task: str = "") -> None:
    with _db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS feedback "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, rating INTEGER, comment TEXT, task TEXT)"
        )
        conn.execute(
            "INSERT INTO feedback (timestamp, rating, comment, task) VALUES (?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rating, comment, task),
        )


def load_feedback() -> list[dict]:
    with _db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS feedback "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, rating INTEGER, comment TEXT, task TEXT)"
        )
        rows = conn.execute("SELECT * FROM feedback ORDER BY id DESC LIMIT 50").fetchall()
        return [dict(r) for r in rows]


# ── WebAuthn credentials (demo) ───────────────────────────────────────────────
def save_webauthn_credential(credential_id: str) -> None:
    os.makedirs(os.path.dirname(WEBAUTHN_PATH), exist_ok=True)
    creds = load_webauthn_credentials()
    if credential_id not in creds:
        creds.append(credential_id)
    with open(WEBAUTHN_PATH, "w") as f:
        json.dump(creds, f)


def load_webauthn_credentials() -> list:
    if os.path.exists(WEBAUTHN_PATH):
        with open(WEBAUTHN_PATH) as f:
            return json.load(f)
    return []
