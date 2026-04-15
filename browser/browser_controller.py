import time
from playwright.sync_api import sync_playwright

from config.settings import BASE_URL, HEADLESS


class BrowserController:
    """Controls a Playwright browser to interact with the IT Admin Panel."""

    def __init__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=HEADLESS,
            slow_mo=20 if not HEADLESS else 0,
        )
        self._page = self._browser.new_page(viewport={"width": 1280, "height": 800})
        self._page.set_default_timeout(6000)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def go_to(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded")
        time.sleep(0.4)

    def get_current_url(self) -> str:
        return self._page.url

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def get_page_text(self) -> str:
        try:
            return self._page.inner_text("body")
        except Exception:
            return self._page.content()

    # ------------------------------------------------------------------
    # Clicking
    # ------------------------------------------------------------------

    def click_button(self, text: str) -> str:
        """Click a <button> by its visible text using multiple strategies."""
        strategies = [
            lambda: self._page.get_by_role("button", name=text, exact=True).click(),
            lambda: self._page.get_by_role("button", name=text, exact=False).first.click(),
            lambda: self._page.locator(f"button:has-text('{text}')").first.click(),
            lambda: self._page.get_by_text(text, exact=True).first.click(),
        ]
        return self._try_strategies(strategies, f"button '{text}'")

    def click_link(self, text: str) -> str:
        """Click an <a> link by its visible text."""
        strategies = [
            lambda: self._page.get_by_role("link", name=text, exact=True).first.click(),
            lambda: self._page.get_by_role("link", name=text, exact=False).first.click(),
            lambda: self._page.locator(f"a:has-text('{text}')").first.click(),
        ]
        return self._try_strategies(strategies, f"link '{text}'")

    # ------------------------------------------------------------------
    # Form filling
    # ------------------------------------------------------------------

    def fill_input(self, label_or_placeholder: str, value: str) -> str:
        """Fill an input by label text or placeholder attribute."""
        strategies = [
            lambda: self._page.get_by_label(label_or_placeholder, exact=True).fill(value),
            lambda: self._page.get_by_label(label_or_placeholder, exact=False).first.fill(value),
            lambda: self._page.get_by_placeholder(label_or_placeholder, exact=True).fill(value),
            lambda: self._page.get_by_placeholder(label_or_placeholder, exact=False).first.fill(value),
            lambda: self._page.locator(
                f"input[name='{label_or_placeholder.lower().replace(' ', '_')}']"
            ).fill(value),
        ]
        self._try_strategies(strategies, f"input '{label_or_placeholder}'")
        return f"Filled '{label_or_placeholder}' with '{value}'"

    def select_option(self, label: str, value: str) -> str:
        """Select a dropdown option by label and value/text."""
        strategies = [
            lambda: self._page.get_by_label(label, exact=True).select_option(value),
            lambda: self._page.get_by_label(label, exact=False).first.select_option(value),
            # Fall back: find select near the label text
            lambda: self._page.locator("select").first.select_option(value),
        ]
        self._try_strategies(strategies, f"select '{label}'")
        return f"Selected '{value}' in '{label}'"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _try_strategies(self, strategies: list, description: str) -> str:
        last_error = None
        for strategy in strategies:
            try:
                strategy()
                time.sleep(0.3)
                return f"Clicked {description}"
            except Exception as e:
                last_error = e
        raise Exception(f"Could not interact with {description}: {last_error}")

    def close(self) -> None:
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:
            pass
