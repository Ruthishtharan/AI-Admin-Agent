"""
saas_agent.py — Run the IT agent against a real SaaS admin panel
================================================================

The same Playwright + LLM agent can navigate real SaaS admin panels
(HubSpot, Notion, Google Workspace, etc.) — not just the local mock panel.

Configuration (set in .env):
    SAAS_TARGET=hubspot          # hubspot | notion | google | custom
    SAAS_URL=https://...         # required only when SAAS_TARGET=custom
    SAAS_EMAIL=admin@company.com # your SaaS login email
    SAAS_PASSWORD=yourpassword   # your SaaS login password
    SAAS_EXTRA=                  # optional extra context for the prompt

Usage:
    python3 saas_agent.py

Example tasks:
    "Invite a new user with email alice@company.com"
    "Deactivate the account for bob@company.com"
    "Check what users are in the workspace"
"""

import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# SaaS profile definitions
# ---------------------------------------------------------------------------

SAAS_PROFILES = {
    "hubspot": {
        "start_url": "https://app.hubspot.com/login",
        "name": "HubSpot CRM",
        "description": """
HubSpot CRM admin panel.

After login you will be on the HubSpot dashboard.
- To manage users: click the gear icon (Settings) → Users & Teams
- To create a contact: go to Contacts → click "Create contact"
- To invite a user: Settings → Users & Teams → click "Invite user" button
- Fill in email and role, click "Send invite"

Useful URLs (replace {PORTAL_ID} with the portal ID visible in the URL after login):
- Users list: https://app.hubspot.com/settings/{PORTAL_ID}/users
- Contacts: https://app.hubspot.com/contacts/{PORTAL_ID}/contacts
""",
    },
    "notion": {
        "start_url": "https://www.notion.so/login",
        "name": "Notion",
        "description": """
Notion workspace admin panel.

After login you are in the workspace.
- To manage members: click "Settings & members" in the left sidebar
- To invite someone: Settings & members → Members tab → "Add members" button → enter email
- To remove a member: Settings & members → Members tab → find the user → click "..." → Remove
- Workspace settings are under Settings & members → Workspace
""",
    },
    "google": {
        "start_url": "https://admin.google.com",
        "name": "Google Workspace Admin",
        "description": """
Google Workspace Admin Console.

Navigation:
- Users: Directory → Users (or click Users card on the home page)
- To add a user: Users → click "Add new user" → fill First name, Last name, Email
- To suspend a user: Users → find user → click user → click "Suspend user"
- To reset password: Users → find user → click "Reset password"
- Groups: Directory → Groups
""",
    },
    "custom": {
        "start_url": os.getenv("SAAS_URL", ""),
        "name": os.getenv("SAAS_NAME", "Custom SaaS"),
        "description": os.getenv("SAAS_EXTRA", "Navigate the admin panel to complete the requested IT task."),
    },
}

# ---------------------------------------------------------------------------
# Build system prompt for the chosen SaaS
# ---------------------------------------------------------------------------

GENERIC_SAAS_PROMPT_TEMPLATE = """You are an AI IT admin agent controlling a real web browser.

Target system: {name}
Starting URL: {start_url}

{description}

## Login
If the page shows a login form, fill in the email and password fields and submit.
The credentials are pre-configured — use them automatically if prompted.

## General Rules
1. Always read_page() after navigating to understand the current state
2. Find inputs by their visible labels or placeholders
3. Click buttons and links by their visible text
4. After submitting a form, read_page() to confirm success
5. If a step fails, read the page and try an alternative approach
6. Call task_complete() with a summary when the task is done

## Available Tools
- navigate(url) — go to any URL
- read_page() — read current page content and URL
- fill_input(label_or_placeholder, value) — fill a text field
- select_option(label, value) — choose a dropdown option
- click_button(text) — click a button
- click_link(text) — click a link
- task_complete(summary) — signal task completion
"""


def _build_prompt(profile: dict) -> str:
    return GENERIC_SAAS_PROMPT_TEMPLATE.format(
        name=profile["name"],
        start_url=profile["start_url"],
        description=profile["description"].strip(),
    )


# ---------------------------------------------------------------------------
# Auto-login helper
# ---------------------------------------------------------------------------

def _attempt_login(browser, email: str, password: str) -> None:
    """Try common login field patterns."""
    page_text = browser.get_page_text().lower()
    if "password" not in page_text and "sign in" not in page_text and "log in" not in page_text:
        return  # Not a login page

    print("[LOGIN] Login page detected — attempting auto-login...")
    for email_label in ("Email", "email", "Email address", "Username"):
        try:
            browser.fill_input(email_label, email)
            break
        except Exception:
            continue

    for pw_label in ("Password", "password"):
        try:
            browser.fill_input(pw_label, password)
            break
        except Exception:
            continue

    for btn_text in ("Log in", "Sign in", "Login", "Continue", "Next"):
        try:
            browser.click_button(btn_text)
            time.sleep(2)
            break
        except Exception:
            continue

    print("[LOGIN] Login attempt complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_saas_task(task: str) -> str:
    target = os.getenv("SAAS_TARGET", "custom").lower()

    if target not in SAAS_PROFILES:
        print(f"[ERROR] Unknown SAAS_TARGET '{target}'. Choose: {', '.join(SAAS_PROFILES)}")
        sys.exit(1)

    profile = SAAS_PROFILES[target]

    if not profile["start_url"]:
        print("[ERROR] No URL configured. Set SAAS_URL in .env or choose a known SAAS_TARGET.")
        sys.exit(1)

    email    = os.getenv("SAAS_EMAIL", "")
    password = os.getenv("SAAS_PASSWORD", "")
    prompt   = _build_prompt(profile)

    print(f"[TARGET] {profile['name']} → {profile['start_url']}")

    from browser.browser_controller import BrowserController
    from agent.agent import run_agent

    # Open browser and navigate to SaaS
    browser = BrowserController()
    try:
        browser.go_to(profile["start_url"])
        time.sleep(1.5)

        if email:
            _attempt_login(browser, email, password)
            time.sleep(1)

        # Now hand control to the LLM agent (browser already open and logged in)
        # We pass the browser's current state by importing internal functions
        from agent.agent import _run_ollama, _run_anthropic, _USE_ANTHROPIC

        def log(step, message):
            print(f"[{step}] {message}")

        if _USE_ANTHROPIC:
            return _run_anthropic(task, log, browser, prompt)
        else:
            return _run_ollama(task, log, browser, prompt)

    except Exception as e:
        print(f"[ERROR] {e}")
        return f"Error: {e}"
    finally:
        try:
            browser.close()
        except Exception:
            pass


if __name__ == "__main__":
    target  = os.getenv("SAAS_TARGET", "custom")
    profile = SAAS_PROFILES.get(target, SAAS_PROFILES["custom"])

    print(f"\n{'='*56}")
    print(f"  SaaS IT Agent  —  {profile['name']}")
    print(f"  URL: {profile['start_url']}")
    print(f"{'='*56}")
    print("Type an IT task for this SaaS admin panel.")
    print("Examples:")
    print("  Invite a new user with email alice@company.com")
    print("  Deactivate the account for bob@company.com")
    print("  List all users in the workspace")
    print("Type 'quit' to exit.\n")

    while True:
        try:
            task = input("SaaS IT request> ").strip()
            if not task:
                continue
            if task.lower() in ("quit", "exit", "q"):
                print("Goodbye.")
                break
            print()
            result = run_saas_task(task)
            print(f"\n✅ {result}\n")
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break
