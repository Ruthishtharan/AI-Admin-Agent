# AI IT Admin Agent

An AI agent that takes natural-language IT support requests — like _"reset password for john@company.com"_ or _"create a new user named Alice in Engineering"_ — and carries them out by controlling a real web browser, exactly like a human would.

Built with Python, Playwright, and a local LLM (Ollama) — **no API key required to run**.

---

## What it does

You type a plain-English IT task. The AI agent opens a browser, navigates to the admin panel, fills forms, clicks buttons, and completes the task — all on its own.

```
You:   "Reset the password for john.doe@company.com"

Agent: Opens browser → goes to Users page → finds John Doe
       → clicks Reset Password → clicks Confirm → done ✅
```

---

## Features

| Feature | Details |
|---|---|
| Mock IT Admin Panel | Flask web app with Dashboard, Users, Create/Reset/Disable/Delete actions |
| AI Browser Agent | Navigates like a human — no hardcoded DOM selectors or API shortcuts |
| Free LLM | Uses Ollama (runs locally, no API key needed) |
| Multi-step logic | "Check if user exists, if not create them, then assign a license" |
| Slack integration | DM the bot or @mention it — agent runs and replies with results |
| SaaS support | Point the agent at HubSpot, Notion, Google Workspace, or any web admin panel |
| Web Chat UI | Browser-based chat interface at `http://localhost:5000/chat` |

---

## How it works (Architecture)

```
You (text input)
      │
      ▼
  AI Agent (Claude / Ollama LLM)
      │  thinks about what to do
      ▼
  Browser Tools (Playwright)
  ┌─────────────────────────────┐
  │  navigate(url)              │
  │  read_page()                │
  │  fill_input(label, value)   │
  │  click_button(text)         │
  │  select_option(label, val)  │
  └─────────────────────────────┘
      │  controls real browser
      ▼
  IT Admin Panel (Flask app)
  ┌─────────────────────────────┐
  │  /users         (list)      │
  │  /create-user   (form)      │
  │  /reset-password (confirm)  │
  │  /disable-user  (confirm)   │
  │  /assign-license (form)     │
  └─────────────────────────────┘
```

The LLM decides what to do. Playwright does the clicking. No direct API calls or DOM manipulation — it's all done through the visible browser UI.

---

## Project Structure

```
AI-Admin-Agent/
│
├── main.py                  ← Start here (runs Flask + agent CLI)
├── slack_bot.py             ← Slack bot trigger
├── saas_agent.py            ← Real SaaS panel support
├── requirements.txt         ← Python dependencies
├── .env.example             ← Copy this to .env and fill in your keys
│
├── app/                     ← Flask IT Admin Panel
│   ├── __init__.py
│   ├── models.py            ← User data (JSON storage)
│   ├── routes.py            ← All web routes
│   ├── static/style.css
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── users.html
│       ├── create_user.html
│       ├── reset_password.html
│       ├── confirm_action.html
│       ├── assign_license.html
│       └── chat.html        ← Web chat UI
│
├── agent/
│   ├── agent.py             ← AI agent loop (Ollama + Anthropic support)
│   └── prompts.py           ← System prompt for the LLM
│
├── browser/
│   └── browser_controller.py ← Playwright wrapper (human-like interactions)
│
├── config/
│   └── settings.py          ← Loads .env settings
│
└── data/
    └── users.json           ← User database (simple JSON file)
```

---

## Prerequisites

- **Python 3.10+**
- **Ollama** (free local LLM runner) — [ollama.com/download](https://ollama.com/download)

---

## Setup (Step by Step)

### Step 1 — Clone the repo

```bash
git clone https://github.com/Ruthishtharan/AI-Admin-Agent.git
cd AI-Admin-Agent
```

### Step 2 — Install Python dependencies

```bash
pip3 install -r requirements.txt
```

### Step 3 — Install Playwright browser

```bash
python3 -m playwright install chromium
```

### Step 4 — Install Ollama and pull a model

1. Download Ollama from [ollama.com/download](https://ollama.com/download) and install it
2. Pull the AI model (downloads ~4.7 GB once):

```bash
ollama pull qwen2.5:7b
```

> **Low RAM?** Use the smaller model instead (2 GB):
> ```bash
> ollama pull llama3.2
> ```
> Then change `OLLAMA_MODEL=llama3.2` in your `.env`

### Step 5 — Set up your .env file

```bash
cp .env.example .env
```

The default settings work out of the box with Ollama. You only need to edit `.env` if you want Slack or SaaS features (see below).

---

## Running the project

### Option 1 — CLI mode (simplest)

```bash
python3 main.py
```

This starts the admin panel and gives you a prompt to type IT tasks:

```
IT Admin Panel  →  http://127.0.0.1:5000
AI Chat UI      →  http://127.0.0.1:5000/chat
LLM Backend     →  Ollama / qwen2.5:7b

IT request> Reset the password for john.doe@company.com
```

### Option 2 — Web Chat UI

Start the app with `python3 main.py`, then open your browser to:

```
http://127.0.0.1:5000/chat
```

Click the example task chips or type your own request and hit **Run Task**. You can watch the browser complete the task in real time.

### Option 3 — Slack Bot

```bash
python3 slack_bot.py
```

Then in Slack:
- **DM the bot:** `reset password for john.doe@company.com`
- **Mention in a channel:** `@IT Admin Agent create user alice@company.com`

See [Slack Setup](#slack-setup) below for how to create the Slack app.

### Option 4 — Real SaaS Panel

```bash
python3 saas_agent.py
```

Configure your target in `.env` (HubSpot, Notion, Google Workspace, or any URL). See [SaaS Setup](#saas-setup) below.

---

## Example Tasks

### Basic tasks
```
Create a new user named Alice Chen with email alice.chen@company.com in Engineering
Reset the password for john.doe@company.com
Disable the account for bob.johnson@company.com
Enable the account for bob.johnson@company.com
Delete the user sarah.lee@company.com
Assign Microsoft 365 E3 license to john.doe@company.com
```

### Multi-step conditional logic
```
Check if alice.chen@company.com exists, if not create them with role employee,
then assign Microsoft 365 E3 license

Check if bob@company.com exists — if yes reset their password, if no create them
```

---

## Admin Panel Pages

Once running, open `http://127.0.0.1:5000` in your browser:

| Page | URL | What it does |
|---|---|---|
| Dashboard | `/` | Shows user stats overview |
| Users | `/users` | Lists all users with action buttons |
| Create User | `/create-user` | Form to add a new user |
| Reset Password | `/reset-password/<email>` | Confirm password reset |
| Disable User | `/disable-user/<email>` | Confirm disable |
| Enable User | `/enable-user/<email>` | Confirm enable |
| Delete User | `/delete-user/<email>` | Confirm delete |
| Assign License | `/assign-license/<email>` | Change role and license |
| AI Chat | `/chat` | Web chat interface for the agent |

---

## Configuration (.env)

```bash
# Which LLM to use
LLM_BACKEND=ollama          # "ollama" (free/local) or "anthropic" (needs credits)

# Ollama settings
OLLAMA_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5:7b     # or llama3.2 for smaller machines

# Anthropic (optional — only if LLM_BACKEND=anthropic)
ANTHROPIC_API_KEY=sk-ant-...

# Flask server
FLASK_PORT=5000
HEADLESS=false              # true = browser runs invisibly in background

# Slack (optional — only for slack_bot.py)
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...

# SaaS target (optional — only for saas_agent.py)
SAAS_TARGET=hubspot         # hubspot | notion | google | custom
SAAS_EMAIL=you@company.com
SAAS_PASSWORD=yourpassword
```

---

## Slack Setup

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. **Enable Socket Mode** — Settings → Socket Mode → Toggle ON → Generate App-Level Token with `connections:write` scope → copy to `SLACK_APP_TOKEN`
3. **Add Bot Scopes** — OAuth & Permissions → Bot Token Scopes → Add: `chat:write`, `app_mentions:read`, `im:read`, `im:history`
4. **Enable Events** — Event Subscriptions → Toggle ON → Subscribe to: `app_mention`, `message.im`
5. **Install to workspace** — OAuth & Permissions → Install to Workspace → copy Bot Token to `SLACK_BOT_TOKEN`
6. Update `.env` with both tokens, then run `python3 slack_bot.py`

---

## SaaS Setup

Edit `.env`:

```bash
# HubSpot
SAAS_TARGET=hubspot
SAAS_EMAIL=you@company.com
SAAS_PASSWORD=yourpassword

# Notion
SAAS_TARGET=notion
SAAS_EMAIL=you@company.com
SAAS_PASSWORD=yourpassword

# Google Workspace Admin
SAAS_TARGET=google
SAAS_EMAIL=admin@yourdomain.com
SAAS_PASSWORD=yourpassword

# Any other URL
SAAS_TARGET=custom
SAAS_URL=https://your-admin-panel.com
SAAS_NAME=My Admin Panel
SAAS_EXTRA=Brief description of what the panel does
```

Then run:
```bash
python3 saas_agent.py
```

---

## Using Anthropic Claude instead of Ollama

If you have Anthropic API credits:

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. Update `.env`:
```bash
LLM_BACKEND=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```
3. Run normally — the agent automatically uses Claude claude-sonnet-4-6

---

## Troubleshooting

**Ollama not running**
```bash
# Check if it's running
curl http://localhost:11434

# Start it manually
ollama serve
```

**SSL error on macOS**
```bash
# Run the Python certificate installer
open "/Applications/Python 3.x/Install Certificates.command"
```

**Port 5000 already in use**
```bash
# Change the port in .env
FLASK_PORT=5001
```

**Browser doesn't open**
```bash
# Make sure HEADLESS=false in .env
# Or set HEADLESS=true to run invisible
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Admin Panel | Python / Flask |
| Browser Automation | Playwright (Chromium) |
| AI Agent | Ollama (qwen2.5:7b) or Anthropic Claude |
| LLM API | OpenAI-compatible (Ollama) / Anthropic SDK |
| Slack Integration | slack-bolt (Socket Mode) |
| Data Storage | JSON file |

---

## License

MIT
