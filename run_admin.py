"""
Run the standalone IT Admin Panel on port 5001.
This is the TARGET website — Vexa navigates it like a human.

Usage:
    python run_admin.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admin_panel.app import app

if __name__ == "__main__":
    port = int(os.getenv("ADMIN_PANEL_PORT", "5001"))
    print(f"\n{'='*48}")
    print(f"  IT Admin Panel  →  http://127.0.0.1:{port}")
    print(f"  Password        →  admin123")
    print(f"{'='*48}\n")
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)
