import time
import base64
from playwright.sync_api import sync_playwright


class BrowserController:
    """
    Controls a Playwright browser to navigate websites like a human.
    Headless=False means a real visible Chrome window appears on screen.
    """

    def __init__(self, headless: bool = False):
        self._headless = headless
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=headless,
            slow_mo=80 if not headless else 0,   # visible: 80ms delay per action
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        self._page = self._browser.new_page(viewport={"width": 1280, "height": 800})
        self._page.set_default_timeout(8000)

    # ── Navigation ────────────────────────────────────────────────────────────

    def go_to(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded")
        time.sleep(0.5)

    def get_current_url(self) -> str:
        return self._page.url

    # ── Reading ───────────────────────────────────────────────────────────────

    def get_page_text(self) -> str:
        """Return visible page text (what a human would read)."""
        try:
            return self._page.inner_text("body")
        except Exception:
            return self._page.content()

    def screenshot_base64(self) -> str:
        """Capture current page as base64 PNG — for streaming to chat UI."""
        try:
            data = self._page.screenshot(type="png")
            return base64.b64encode(data).decode()
        except Exception:
            return ""

    # ── Clicking ──────────────────────────────────────────────────────────────

    def click(self, text: str) -> str:
        """
        Click any visible element by its text — buttons, links, labels.
        Tries multiple strategies so the LLM only needs to pass the visible text.
        """
        strategies = [
            # Exact button
            lambda: self._page.get_by_role("button", name=text, exact=True).first.click(),
            # Partial button
            lambda: self._page.get_by_role("button", name=text, exact=False).first.click(),
            # Exact link
            lambda: self._page.get_by_role("link", name=text, exact=True).first.click(),
            # Partial link
            lambda: self._page.get_by_role("link", name=text, exact=False).first.click(),
            # Any element containing text (broad fallback)
            lambda: self._page.get_by_text(text, exact=True).first.click(),
            lambda: self._page.get_by_text(text, exact=False).first.click(),
            # CSS text match
            lambda: self._page.locator(f"button:has-text('{text}')").first.click(),
            lambda: self._page.locator(f"a:has-text('{text}')").first.click(),
        ]
        return self._try(strategies, f"element '{text}'")

    def click_button(self, text: str) -> str:
        return self.click(text)

    def click_link(self, text: str) -> str:
        return self.click(text)

    # ── Form filling ──────────────────────────────────────────────────────────

    def fill_input(self, label_or_placeholder: str, value: str) -> str:
        """Type into an input found by its label text or placeholder."""
        strategies = [
            lambda: self._page.get_by_label(label_or_placeholder, exact=True).fill(value),
            lambda: self._page.get_by_label(label_or_placeholder, exact=False).first.fill(value),
            lambda: self._page.get_by_placeholder(label_or_placeholder, exact=True).fill(value),
            lambda: self._page.get_by_placeholder(label_or_placeholder, exact=False).first.fill(value),
            # Fall back to name= attribute
            lambda: self._page.locator(
                f"input[name='{label_or_placeholder.lower().replace(' ', '_').replace(' ', '')}']"
            ).first.fill(value),
        ]
        self._try(strategies, f"input '{label_or_placeholder}'")
        return f"Filled '{label_or_placeholder}' → '{value}'"

    def select_option(self, label: str, value: str) -> str:
        """Select a dropdown option by field label and option text/value."""
        strategies = [
            # By label — try value then visible text
            lambda: self._page.get_by_label(label, exact=True).select_option(value),
            lambda: self._page.get_by_label(label, exact=True).select_option(label=value),
            lambda: self._page.get_by_label(label, exact=False).first.select_option(value),
            lambda: self._page.get_by_label(label, exact=False).first.select_option(label=value),
            # Fall back: find select by nearby text
            lambda: self._page.locator(f"select[name='{label.lower()}']").select_option(value),
            lambda: self._page.locator(f"select[name='{label.lower()}']").select_option(label=value),
        ]
        self._try(strategies, f"select '{label}'")
        return f"Selected '{value}' in '{label}'"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _try(self, strategies: list, description: str) -> str:
        last_err = None
        for s in strategies:
            try:
                s()
                time.sleep(0.3)
                return f"OK: {description}"
            except Exception as e:
                last_err = e
        raise Exception(f"Could not interact with {description}: {last_err}")

    def close(self) -> None:
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:
            pass
