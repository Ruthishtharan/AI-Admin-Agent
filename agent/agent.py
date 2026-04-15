"""
Vexa agent — navigates the IT Admin Panel like a human using a real browser.

Key design:
  - NO direct database shortcuts.  Every action goes through the browser.
  - show_browser=True  → headed Chromium window opens on screen (first 6 tasks)
  - show_browser=False → headless (user chose to hide the window)
  - Screenshots are captured after each action and streamed to the chat UI
    so the user can always see what's happening, even in headless mode.
"""

import json
import base64
from typing import Callable, Optional
from openai import OpenAI

from config.settings import (
    ANTHROPIC_API_KEY, GROQ_API_KEY,
    LLM_BACKEND, OLLAMA_URL, OLLAMA_MODEL,
    ADMIN_PANEL_URL, ADMIN_PANEL_PASSWORD,
)
from agent.prompts import build_system_prompt

# ── LLM client setup ──────────────────────────────────────────────────────────

_USE_ANTHROPIC = False
_USE_GROQ      = False
_GROQ_MODEL    = "meta-llama/llama-4-scout-17b-16e-instruct"

if LLM_BACKEND == "anthropic" and ANTHROPIC_API_KEY:
    import anthropic as _anthropic
    _anthropic_client = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    _USE_ANTHROPIC = True

elif LLM_BACKEND == "groq" and GROQ_API_KEY:
    _groq_client = OpenAI(
        api_key=GROQ_API_KEY.strip(),
        base_url="https://api.groq.com/openai/v1",
    )
    _USE_GROQ = True

else:
    _ollama_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")


# ── Tool definitions ──────────────────────────────────────────────────────────
# The LLM only has browser tools — it must navigate like a human.

TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": "Go to a URL in the browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL to navigate to"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_page",
            "description": "Read the current page's visible text and URL. Use this to understand where you are and what options are available.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click any visible element — button, link, or text — by its exact visible label.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The visible text on the element to click"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_input",
            "description": "Type a value into a form field, found by its label text or placeholder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "The label or placeholder text of the input field"},
                    "value": {"type": "string", "description": "The value to type"},
                },
                "required": ["label", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_option",
            "description": "Select an option in a dropdown, found by its label.",
            "parameters": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "The label text of the dropdown/select field"},
                    "value": {"type": "string", "description": "The option text or value to select"},
                },
                "required": ["label", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Call this when the task is fully done. Provide a clear human-readable summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "What was accomplished"},
                },
                "required": ["summary"],
            },
        },
    },
]

TOOLS_ANTHROPIC = [
    {
        "name":         t["function"]["name"],
        "description":  t["function"]["description"],
        "input_schema": t["function"]["parameters"],
    }
    for t in TOOLS_OPENAI
]


# ── Browser login helper ──────────────────────────────────────────────────────

def _ensure_logged_in(browser) -> None:
    """Navigate to admin panel and log in if the login page is showing."""
    import time
    try:
        current = browser.get_current_url()
        if "login" in current or current in ("about:blank", ""):
            browser.go_to(f"{ADMIN_PANEL_URL}/login")
            time.sleep(0.4)
        # If login page, authenticate
        page_text = browser.get_page_text()
        if "Admin Password" in page_text or "Sign In" in page_text:
            browser.fill_input("Admin Password", ADMIN_PANEL_PASSWORD)
            browser.click("Sign In")
            time.sleep(0.8)
    except Exception:
        pass


# ── Tool executor ─────────────────────────────────────────────────────────────

def _execute_tool(browser, name: str, inputs: dict) -> str:
    try:
        if name == "navigate":
            url = inputs["url"]
            # If navigating to admin panel root without path, go to dashboard
            if url in (ADMIN_PANEL_URL, ADMIN_PANEL_URL + "/"):
                url = f"{ADMIN_PANEL_URL}/"
            browser.go_to(url)
            return f"Navigated to {url}"

        elif name == "read_page":
            url  = browser.get_current_url()
            text = browser.get_page_text()
            return f"[URL]: {url}\n\n[PAGE CONTENT]:\n{text[:3000]}"

        elif name == "click":
            return browser.click(inputs["text"])

        elif name == "fill_input":
            return browser.fill_input(inputs["label"], inputs["value"])

        elif name == "select_option":
            return browser.select_option(inputs["label"], inputs["value"])

        elif name == "task_complete":
            return f"TASK_COMPLETE: {inputs.get('summary', 'Done.')}"

        else:
            return f"Unknown tool: {name}"

    except Exception as e:
        return f"Error in {name}: {e}"


# ── OpenAI-compatible agent loop (Groq / Ollama) ─────────────────────────────

def _run_openai_compatible(
    client: OpenAI,
    model: str,
    task: str,
    log: Callable,
    browser,
    max_steps: int = 20,
) -> str:
    system = build_system_prompt(ADMIN_PANEL_URL, ADMIN_PANEL_PASSWORD)
    messages = [
        {"role": "system",  "content": system},
        {"role": "user",    "content": task},
    ]

    for step in range(max_steps):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS_OPENAI,
            tool_choice="auto",
            temperature=0,
        )
        msg = response.choices[0].message

        # No tool call → natural language response (shouldn't happen much)
        if not msg.tool_calls:
            content = msg.content or "Task complete."
            log("DONE", content)
            return content

        # Process each tool call
        messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except Exception:
                fn_args = {}

            # Log the tool call
            if fn_name == "navigate":
                log("NAVIGATE", f"Going to {fn_args.get('url','')}")
            elif fn_name == "read_page":
                log("READ", "Reading page content…")
            elif fn_name == "click":
                log("CLICK", f"Clicking \"{fn_args.get('text','')}\"")
            elif fn_name == "fill_input":
                log("TYPE", f"Filling \"{fn_args.get('label','')}\" → \"{fn_args.get('value','')}\"")
            elif fn_name == "select_option":
                log("SELECT", f"Selecting \"{fn_args.get('value','')}\" in \"{fn_args.get('label','')}\"")
            elif fn_name == "task_complete":
                log("COMPLETE", fn_args.get("summary", "Done."))
            else:
                log("TOOL", fn_name)

            result = _execute_tool(browser, fn_name, fn_args)

            # After every browser action, capture and stream a screenshot
            if fn_name not in ("task_complete", "read_page"):
                try:
                    shot = browser.screenshot_base64()
                    if shot:
                        log("SCREENSHOT", shot)
                except Exception:
                    pass

            if fn_name == "task_complete":
                return fn_args.get("summary", "Done.")

            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      result,
            })

    return "Task reached maximum steps."


# ── Anthropic agent loop ──────────────────────────────────────────────────────

def _run_anthropic(task: str, log: Callable, browser, max_steps: int = 20) -> str:
    import anthropic as _ant

    system = build_system_prompt(ADMIN_PANEL_URL, ADMIN_PANEL_PASSWORD)
    messages = [{"role": "user", "content": task}]

    for step in range(max_steps):
        response = _anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            tools=TOOLS_ANTHROPIC,
            messages=messages,
        )

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if not tool_uses:
            result = text_blocks[0].text if text_blocks else "Done."
            log("DONE", result)
            return result

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []

        for tu in tool_uses:
            fn_name = tu.name
            fn_args = tu.input or {}

            if fn_name == "navigate":
                log("NAVIGATE", f"Going to {fn_args.get('url','')}")
            elif fn_name == "click":
                log("CLICK", f"Clicking \"{fn_args.get('text','')}\"")
            elif fn_name == "fill_input":
                log("TYPE", f"Filling \"{fn_args.get('label','')}\" → \"{fn_args.get('value','')}\"")
            elif fn_name == "select_option":
                log("SELECT", f"Selecting \"{fn_args.get('value','')}\" in \"{fn_args.get('label','')}\"")
            elif fn_name == "task_complete":
                log("COMPLETE", fn_args.get("summary", "Done."))
            else:
                log("TOOL", fn_name)

            result = _execute_tool(browser, fn_name, fn_args)

            if fn_name not in ("task_complete", "read_page"):
                try:
                    shot = browser.screenshot_base64()
                    if shot:
                        log("SCREENSHOT", shot)
                except Exception:
                    pass

            if fn_name == "task_complete":
                return fn_args.get("summary", "Done.")

            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": tu.id,
                "content":     result,
            })

        messages.append({"role": "user", "content": tool_results})

    return "Task reached maximum steps."


# ── Public entry point ────────────────────────────────────────────────────────

def run_agent(
    task: str,
    progress_callback: Optional[Callable] = None,
    show_browser: bool = True,
) -> str:
    """
    Run Vexa on the given task.

    show_browser=True  → headed Chromium window (user watches on screen)
    show_browser=False → headless (silent, only chat steps shown)
    """

    def log(step: str, message: str):
        if progress_callback:
            progress_callback(step, message)
        else:
            icon = {
                "NAVIGATE": "🌐", "READ": "👁", "CLICK": "🖱",
                "TYPE": "⌨", "SELECT": "📋", "COMPLETE": "✅",
                "SCREENSHOT": None,
            }.get(step, "•")
            if icon:
                print(f"  {icon} [{step}] {message}")

    from browser.browser_controller import BrowserController

    # headed=True means Chromium opens visibly; headless=True means hidden
    browser = BrowserController(headless=not show_browser)

    try:
        # Start at the admin panel login page
        log("NAVIGATE", f"Opening admin panel at {ADMIN_PANEL_URL}")
        browser.go_to(f"{ADMIN_PANEL_URL}/login")
        shot = browser.screenshot_base64()
        if shot:
            log("SCREENSHOT", shot)

        if _USE_ANTHROPIC:
            return _run_anthropic(task, log, browser)
        elif _USE_GROQ:
            return _run_openai_compatible(_groq_client, _GROQ_MODEL, task, log, browser)
        else:
            return _run_openai_compatible(_ollama_client, OLLAMA_MODEL, task, log, browser)

    finally:
        browser.close()
