import json
from typing import Callable, Optional
from openai import OpenAI

from config.settings import (
    ANTHROPIC_API_KEY, GROQ_API_KEY,
    LLM_BACKEND, OLLAMA_URL, OLLAMA_MODEL,
)
from agent.prompts import SYSTEM_PROMPT
from browser.browser_controller import BrowserController

# ---------------------------------------------------------------------------
# LLM client — auto-selects Anthropic | Google Gemini | Ollama
# Google uses its OpenAI-compatible endpoint (no extra library needed)
# ---------------------------------------------------------------------------

_USE_ANTHROPIC = False
_USE_GROQ      = False
_GROQ_MODEL    = "llama-3.1-70b-versatile"

if LLM_BACKEND == "anthropic" and ANTHROPIC_API_KEY:
    import anthropic as _anthropic
    _anthropic_client = _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    _USE_ANTHROPIC = True

elif LLM_BACKEND == "groq" and GROQ_API_KEY:
    # Google's OpenAI-compatible endpoint — works with standard openai SDK
    _google_client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )
    _USE_GROQ = True

else:
    _ollama_client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")

# ---------------------------------------------------------------------------
# Tool definitions — OpenAI function-call format (works for Ollama + Google)
# ---------------------------------------------------------------------------

TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": "Navigate the browser to a full URL on the admin panel.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL, e.g. http://127.0.0.1:5000/users"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_page",
            "description": "Read the current page content and URL to understand what is on screen.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_input",
            "description": "Fill a text/email input field identified by its label or placeholder text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "label_or_placeholder": {"type": "string", "description": "Label or placeholder of the input"},
                    "value": {"type": "string", "description": "Value to enter"},
                },
                "required": ["label_or_placeholder", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_option",
            "description": "Select an option from a dropdown by its label and option value.",
            "parameters": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "description": "Label above the dropdown, e.g. 'Role'"},
                    "value": {"type": "string", "description": "Option value/text to select"},
                },
                "required": ["label", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click_button",
            "description": "Click a button on the page by its visible text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Visible text of the button"}
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "click_link",
            "description": "Click a link on the page by its visible text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Visible text of the link"}
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "task_complete",
            "description": "Call when the task has been fully completed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "What was accomplished"}
                },
                "required": ["summary"],
            },
        },
    },
]

# Anthropic format
TOOLS_ANTHROPIC = [
    {
        "name": t["function"]["name"],
        "description": t["function"]["description"],
        "input_schema": t["function"]["parameters"],
    }
    for t in TOOLS_OPENAI
]


# ---------------------------------------------------------------------------
# Tool execution (shared by all backends)
# ---------------------------------------------------------------------------

def _execute_tool(browser: BrowserController, name: str, inputs: dict) -> str:
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
        elif name == "task_complete":
            return f"TASK_COMPLETE: {inputs['summary']}"
        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error in {name}: {e}"


# ---------------------------------------------------------------------------
# Shared OpenAI-compatible agent loop (used by Ollama AND Google)
# ---------------------------------------------------------------------------

def _run_openai_compatible(
    client: OpenAI,
    model: str,
    task: str,
    log,
    browser: BrowserController,
    prompt: str = None,
) -> str:
    messages = [
        {"role": "system", "content": prompt or SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    result = "Task could not be completed."

    for _ in range(25):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS_OPENAI,
            tool_choice="auto",
        )

        msg = response.choices[0].message
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

            tool_result = _execute_tool(browser, name, args)
            short = tool_result[:300] + "..." if len(tool_result) > 300 else tool_result
            log("RESULT", short)

            tool_results.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": tool_result,
            })

        messages.extend(tool_results)

    return result


# ---------------------------------------------------------------------------
# Anthropic agent loop
# ---------------------------------------------------------------------------

def _run_anthropic(task: str, log, browser: BrowserController, prompt: str = None) -> str:
    messages = [{"role": "user", "content": task}]
    result = "Task could not be completed."

    for _ in range(25):
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

                    tool_result = _execute_tool(browser, block.name, block.input)
                    short = tool_result[:300] + "..." if len(tool_result) > 300 else tool_result
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

    browser = BrowserController()
    try:
        if start_url:
            browser.go_to(start_url)
        if _USE_ANTHROPIC:
            return _run_anthropic(task, log, browser, system_prompt)
        elif _USE_GROQ:
            return _run_openai_compatible(_groq_client, _GROQ_MODEL, task, log, browser, system_prompt)
        else:
            return _run_openai_compatible(_ollama_client, OLLAMA_MODEL, task, log, browser, system_prompt)
    except Exception as e:
        log("ERROR", str(e))
        return f"Error: {e}"
    finally:
        try:
            browser.close()
        except Exception:
            pass
