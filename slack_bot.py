"""
slack_bot.py — Trigger the IT Admin Agent from Slack
======================================================

DM the bot OR @mention it in any channel with an IT task.
The agent opens a browser, completes the task, and replies with the result.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ONE-TIME SLACK APP SETUP (free, takes ~5 minutes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Go to https://api.slack.com/apps → Create New App → "From scratch"
   Name it "IT Admin Agent", pick your workspace.

2. Enable Socket Mode
   Settings → Socket Mode → toggle ON
   Click "Generate Token" with scope: connections:write
   Copy the token (xapp-...) → SLACK_APP_TOKEN in .env

3. Add Bot Token Scopes
   OAuth & Permissions → Bot Token Scopes → Add:
     chat:write
     app_mentions:read
     im:read
     im:history
     channels:history  (optional — for channel monitoring)

4. Enable Event Subscriptions
   Event Subscriptions → Toggle ON
   Subscribe to bot events:
     app_mention
     message.im

5. Install app to workspace
   OAuth & Permissions → Install to Workspace → Allow
   Copy "Bot User OAuth Token" (xoxb-...) → SLACK_BOT_TOKEN in .env

6. Update .env:
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...

7. Run:
   python3 slack_bot.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USAGE IN SLACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• DM the bot:   reset password for john.doe@company.com
• In a channel: @IT Admin Agent create user alice@company.com
"""

import os
import ssl
import sys
import threading
import time
import certifi

# Fix SSL certificate verification on macOS (Python.org installer doesn't
# automatically trust system certificates — this uses certifi's trusted bundle)
ssl._create_default_https_context = lambda: ssl.create_default_context(
    cafile=certifi.where()
)

from dotenv import load_dotenv

load_dotenv()

# ── Validate tokens before importing slack_bolt ──────────────────────────────
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")

_missing = (
    not SLACK_BOT_TOKEN
    or not SLACK_APP_TOKEN
    or "your-bot-token" in SLACK_BOT_TOKEN
    or "your-app-token" in SLACK_APP_TOKEN
)
if _missing:
    print("\n[ERROR] Slack tokens are not configured in .env")
    print("  Set SLACK_BOT_TOKEN=xoxb-... and SLACK_APP_TOKEN=xapp-...")
    print("  See setup instructions at the top of slack_bot.py\n")
    sys.exit(1)

# ── Start Flask admin panel in background ────────────────────────────────────
from app import create_app
from config.settings import FLASK_PORT

_flask_app = create_app()
threading.Thread(
    target=lambda: _flask_app.run(debug=False, port=FLASK_PORT, use_reloader=False),
    daemon=True,
).start()
time.sleep(1.5)
print(f"[OK] Flask admin panel running at http://127.0.0.1:{FLASK_PORT}")

# ── Slack Bolt app ────────────────────────────────────────────────────────────
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

slack_app = App(token=SLACK_BOT_TOKEN)


def _handle_task(task: str, say) -> None:
    """Run the IT agent and post results to Slack."""
    task = task.strip()
    if not task:
        say(
            "👋 Hi! I'm the IT Admin Agent.\n"
            "Send me a task like:\n"
            "• `reset password for john.doe@company.com`\n"
            "• `create a user named Alice Chen with email alice@company.com`\n"
            "• `disable the account for bob.johnson@company.com`\n"
            "• `check if alice@company.com exists, if not create them then assign Microsoft 365 E3`"
        )
        return

    say(f"🤖 *IT Agent activated*\n> {task}\n_Opening browser..._")

    from agent.agent import run_agent

    steps: list[str] = []

    def callback(step: str, message: str) -> None:
        if step not in ("START",):
            steps.append(f"`[{step}]` {message}")

    try:
        result = run_agent(task, progress_callback=callback)

        # Keep last 10 steps to stay within Slack's message limit
        step_lines = "\n".join(steps[-10:]) if steps else "_No steps logged._"

        say(
            f"✅ *Task Complete*\n"
            f"*Result:* {result}\n\n"
            f"*Agent trace (last steps):*\n{step_lines}"
        )

    except Exception as e:
        say(f"❌ *Error running task*\n`{e}`")


# ── Event handlers ────────────────────────────────────────────────────────────

@slack_app.event("app_mention")
def handle_mention(event, say):
    """@IT Admin Agent <task> in any channel."""
    text = event.get("text", "")
    # Strip the leading @BotName mention token
    parts = text.split(None, 1)
    task = parts[1] if len(parts) > 1 else ""
    _handle_task(task, say)


@slack_app.event("message")
def handle_dm(event, say):
    """Direct messages sent to the bot."""
    # Only handle DMs (channel_type == "im"), ignore bot's own messages
    if event.get("channel_type") == "im" and not event.get("bot_id"):
        _handle_task(event.get("text", ""), say)


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n⚡ Slack IT Admin Agent is running!")
    print("  DM the bot or @mention it in a channel with an IT task.")
    print("  Press Ctrl+C to stop.\n")
    handler = SocketModeHandler(slack_app, SLACK_APP_TOKEN)
    handler.start()
