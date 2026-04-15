import json
from typing import Callable, Optional
from openai import OpenAI

from config.settings import (
    ANTHROPIC_API_KEY, GROQ_API_KEY,
    LLM_BACKEND, OLLAMA_URL, OLLAMA_MODEL,
    BASE_URL, ADMIN_PASSWORD,
)
from agent.prompts import SYSTEM_PROMPT

# ---------------------------------------------------------------------------
# LLM client setup
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS_OPENAI = [
    # ── Direct admin tools (instant, no browser) ──────────────────────────
    {
        "type": "function",
        "function": {
            "name": "admin_create_user",
            "description": "Create a new user directly in the database. Use this for ALL create user tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email":      {"type": "string", "description": "User email address"},
                    "name":       {"type": "string", "description": "Full name"},
                    "role":       {"type": "string", "description": "employee | admin | contractor | guest", "default": "employee"},
                    "department": {"type": "string", "description": "Department (Engineering, HR, IT, Marketing, etc.)"},
                    "license":    {"type": "string", "description": "License (None, Microsoft 365 E1/E3/E5, Google Workspace Basic/Business)", "default": "None"},
                },
                "required": ["email", "name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "admin_find_user",
            "description": "Look up a user by their email address.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Email address to look up"},
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "admin_list_users",
            "description": "List all users in the system.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "admin_disable_user",
            "description": "Disable a user account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "admin_enable_user",
            "description": "Enable a disabled user account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "admin_delete_user",
            "description": "Permanently delete a user account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "admin_reset_password",
            "description": "Reset a user's password.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "admin_assign_license",
            "description": "Assign a license and/or role to a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email":   {"type": "string"},
                    "license": {"type": "string", "description": "License type"},
                    "role":    {"type": "string", "description": "Role (optional)"},
                },
                "required": ["email", "license"],
            },
        },
    },

    # ── Browser tools (external websites only) ────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": "Navigate browser to a URL. Only use for external websites, NOT for admin panel tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_page",
            "description": "Read the current browser page content.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_input",
            "description": "Fill a text input field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "label_or_placeholder": {"type": "string"},
                    "value":               {"type": "string"},
                },
                "required": ["label_or_placeholder", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_option",
            "description": "Select a dropdown option.",
            "parameters": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["label", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click_button",
            "description": "Click a button by visible text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click_link",
            "description": "Click a link by visible text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Call when the task is fully done.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                },
                "required": ["summary"],
            },
        },
    },
]

TOOLS_ANTHROPIC = [
    {
        "name": t["function"]["name"],
        "description": t["function"]["description"],
        "input_schema": t["function"]["parameters"],
    }
    for t in TOOLS_OPENAI
]


# ---------------------------------------------------------------------------
# Lazy browser — only opens if a browser tool is actually called
# ---------------------------------------------------------------------------

class _LazyBrowser:
    def __init__(self):
        self._ctrl = None

    def get(self):
        if self._ctrl is None:
            from browser.browser_controller import BrowserController
            self._ctrl = BrowserController()
            _auto_login(self._ctrl)
        return self._ctrl

    def close(self):
        if self._ctrl:
            try:
                self._ctrl.close()
            except Exception:
                pass


def _auto_login(browser) -> None:
    """Authenticate the Playwright browser on the admin panel."""
    import time
    try:
        browser.go_to(f"{BASE_URL}/login")
        time.sleep(0.3)
        if "/login" not in browser.get_current_url():
            return
        browser._page.get_by_placeholder("Enter admin password").fill(ADMIN_PASSWORD)
        browser._page.get_by_role("button", name="Sign In").click()
        try:
            browser._page.wait_for_url(lambda url: "/login" not in url, timeout=6000)
        except Exception:
            time.sleep(1.5)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Direct admin tool execution (no browser needed)
# ---------------------------------------------------------------------------

def _execute_direct_tool(name: str, inputs: dict) -> str:
    from app.models import (
        create_user as _create_user,
        find_user as _find_user,
        load_users as _load_users,
        disable_user as _disable_user,
        enable_user as _enable_user,
        delete_user as _delete_user,
        reset_password as _reset_password,
        assign_license as _assign_license,
        assign_role as _assign_role,
        user_exists as _user_exists,
    )

    if name == "admin_create_user":
        email = inputs.get("email", "").strip().lower()
        uname = inputs.get("name", "").strip()
        if not email or not uname:
            return "Error: email and name are required."
        if _user_exists(email):
            return f"User {email} already exists — skipping creation."
        user = _create_user(
            email, uname,
            inputs.get("role", "employee"),
            inputs.get("department", ""),
            inputs.get("license", "None"),
        )
        return (
            f"✅ Created user: {user['name']} ({email}) "
            f"| Role: {user['role']} | Dept: {user.get('department','—')} "
            f"| License: {user.get('license','None')}"
        )

    elif name == "admin_find_user":
        user = _find_user(inputs.get("email", ""))
        if not user:
            return f"User '{inputs.get('email','')}' not found."
        return (
            f"Found: {user['name']} ({user['email']}) "
            f"| {user['role']} in {user.get('department','—')} "
            f"| Status: {user['status']} | License: {user.get('license','None')}"
        )

    elif name == "admin_list_users":
        users = _load_users()
        if not users:
            return "No users in the system."
        return "\n".join(
            f"- {u['name']} ({u['email']}) [{u['status']}] {u['role']} / {u.get('department','—')}"
            for u in users
        )

    elif name == "admin_disable_user":
        ok = _disable_user(inputs.get("email", ""))
        return "✅ User disabled." if ok else "User not found."

    elif name == "admin_enable_user":
        ok = _enable_user(inputs.get("email", ""))
        return "✅ User enabled." if ok else "User not found."

    elif name == "admin_delete_user":
        ok = _delete_user(inputs.get("email", ""))
        return "✅ User deleted permanently." if ok else "User not found."

    elif name == "admin_reset_password":
        ok = _reset_password(inputs.get("email", ""))
        return "✅ Password reset successfully." if ok else "User not found."

    elif name == "admin_assign_license":
        email = inputs.get("email", "")
        ok = _assign_license(email, inputs.get("license", "None"))
        if inputs.get("role"):
            _assign_role(email, inputs["role"])
        return f"✅ License/role updated for {email}." if ok else "User not found."

    return f"Unknown direct tool: {name}"


# ---------------------------------------------------------------------------
# Browser tool execution
# ---------------------------------------------------------------------------

def _execute_browser_tool(browser, name: str, inputs: dict) -> str:
    try:
        if name == "navigate":
            browser.go_to(inputs["url"])
            return f"Navigated to {inputs['url']}"
        elif name == "read_page":
            return f"[URL]: {browser.get_current_url()}\n\n[PAGE]:\n{browser.get_page_text()}"
        elif name == "fill_input":
            return browser.fill_input(inputs["label_or_placeholder"], inputs["value"])
        elif name == "select_option":
            return browser.select_option(inputs["label"], inputs["value"])
        elif name == "click_button":
            return browser.click_button(inputs["text"])
        elif name == "click_link":
            return browser.click_link(inputs["text"])
        else:
            return f"Unknown browser tool: {name}"
    except Exception as e:
        return f"Error in {name}: {e}"


# ---------------------------------------------------------------------------
# Unified tool dispatcher
# ---------------------------------------------------------------------------

_DIRECT_TOOLS = {
    "admin_create_user", "admin_find_user", "admin_list_users",
    "admin_disable_user", "admin_enable_user", "admin_delete_user",
    "admin_reset_password", "admin_assign_license",
}


def _execute_tool(lazy_browser: _LazyBrowser, name: str, inputs: dict) -> str:
    if name in _DIRECT_TOOLS:
        return _execute_direct_tool(name, inputs)
    if name == "task_complete":
        return f"TASK_COMPLETE: {inputs.get('summary', 'Done.')}"
    # Browser tools
    return _execute_browser_tool(lazy_browser.get(), name, inputs)


# ---------------------------------------------------------------------------
# OpenAI-compatible agent loop (Groq / Ollama)
# ---------------------------------------------------------------------------

def _run_openai_compatible(
    client: OpenAI,
    model: str,
    task: str,
    log,
    lazy_browser: _LazyBrowser,
    prompt: str = None,
) -> str:
    messages = [
        {"role": "system", "content": prompt or SYSTEM_PROMPT},
        {"role": "user",   "content": task},
    ]
    result = "Task could not be completed."

    for _ in range(20):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS_OPENAI,
            tool_choice="auto",
            max_tokens=1024,
        )

        msg    = response.choices[0].message
        finish = response.choices[0].finish_reason

        assistant_entry: dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_entry)

        if msg.content:
            log("THINK", msg.content)

        if finish == "stop" or not msg.tool_calls:
            result = msg.content or "Task completed."
            log("DONE", result)
            break

        tool_results = []
        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}

            log("TOOL", f"{name}({args})")

            if name == "task_complete":
                result = args.get("summary", "Task completed.")
                log("COMPLETE", result)
                return result

            tool_result = _execute_tool(lazy_browser, name, args)
            short = tool_result[:400] + "…" if len(tool_result) > 400 else tool_result
            log("RESULT", short)

            tool_results.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      tool_result,
            })

        messages.extend(tool_results)

    return result


# ---------------------------------------------------------------------------
# Anthropic agent loop
# ---------------------------------------------------------------------------

def _run_anthropic(
    task: str, log, lazy_browser: _LazyBrowser, prompt: str = None
) -> str:
    messages = [{"role": "user", "content": task}]
    result   = "Task could not be completed."

    for _ in range(20):
        response = _anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=prompt or SYSTEM_PROMPT,
            tools=TOOLS_ANTHROPIC,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    result = block.text
                    log("DONE", result)
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "text" and block.text:
                    log("THINK", block.text)
                elif block.type == "tool_use":
                    log("TOOL", f"{block.name}({block.input})")

                    if block.name == "task_complete":
                        result = block.input.get("summary", "Task completed.")
                        log("COMPLETE", result)
                        tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
                        messages.append({"role": "user", "content": tool_results})
                        return result

                    tool_result = _execute_tool(lazy_browser, block.name, block.input)
                    short = tool_result[:400] + "…" if len(tool_result) > 400 else tool_result
                    log("RESULT", short)
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": tool_result})

            messages.append({"role": "user", "content": tool_results})

    return result


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_agent(
    task: str,
    progress_callback: Optional[Callable[[str, str], None]] = None,
    system_prompt: Optional[str] = None,
    start_url: Optional[str] = None,
) -> str:
    def log(step: str, message: str):
        print(f"[{step}] {message}")
        if progress_callback:
            progress_callback(step, message)

    if _USE_ANTHROPIC:
        backend = "Anthropic (claude-sonnet-4-6)"
    elif _USE_GROQ:
        backend = f"Groq ({_GROQ_MODEL})"
    else:
        backend = f"Ollama ({OLLAMA_MODEL})"

    log("START", f"Task: {task}  |  Backend: {backend}")

    lazy_browser = _LazyBrowser()
    try:
        if start_url:
            lazy_browser.get().go_to(start_url)

        if _USE_ANTHROPIC:
            return _run_anthropic(task, log, lazy_browser, system_prompt)
        elif _USE_GROQ:
            return _run_openai_compatible(_groq_client, _GROQ_MODEL, task, log, lazy_browser, system_prompt)
        else:
            return _run_openai_compatible(_ollama_client, OLLAMA_MODEL, task, log, lazy_browser, system_prompt)

    except Exception as e:
        log("ERROR", str(e))
        return f"Error: {e}"
    finally:
        lazy_browser.close()
