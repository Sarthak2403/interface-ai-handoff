from __future__ import annotations
from typing import Protocol
from playwright.async_api import Page
from urllib.parse import urlparse

DEFAULT_TIMEOUT_MS = 6000

class ComputerSurface(Protocol):
    async def observe(self) -> dict: ...
    async def click(self, strategy: str, target: str) -> None: ...
    async def fill(self, strategy: str, target: str, value: str) -> None: ...
    async def extract(self, strategy: str, target: str) -> str: ...
    async def navigate(self, url: str) -> None: ...

class BrowserSurface:
    def __init__(self, page: Page, allowed_domains: list[str] | None = None):
        self.page = page
        self.allowed_domains = allowed_domains or []

    def _check_domain(self) -> None:
        if not self.allowed_domains:
            return
        host = urlparse(self.page.url).hostname or ""
        if not any(host == d or host.endswith("." + d) for d in self.allowed_domains):
            raise RuntimeError(
                f"Guardrail violation: navigated outside allowlist to '{host}' ({self.page.url})"
            )

    async def observe(self) -> dict:
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "visible_text": await self.page.locator("body").inner_text(),
        }

    async def list_interactive_elements(self, limit: int = 40) -> list[dict]:
            elements = await self.page.eval_on_selector_all(
                "a, button, input, select, textarea, [role=button], [role=link]",
                """(els, limit) => els.slice(0, limit).map((e) => ({
                    tag: e.tagName.toLowerCase(),
                    text: (e.innerText || e.placeholder || '').trim().slice(0, 60),
                    value: e.value || null,
                    id: e.id || null,
                    name: e.getAttribute('name'),
                    type: e.getAttribute('type')
                }))""",
                limit,
            )
            return [e for e in elements if e["text"] or e["id"] or e["name"]]

    def _locator(self, strategy: str, target: str):
        if strategy == "label":
            return self.page.get_by_label(target)
        if strategy == "role":
            return self.page.get_by_role("button", name=target)
        if strategy == "text":
            return self.page.get_by_text(target, exact=False)
        if strategy == "css":
            return self.page.locator(target)
        if strategy == "xpath":
            return self.page.locator(f"xpath={target}")
        raise ValueError(f"Unsupported locator strategy: {strategy}")

    async def click(self, strategy: str, target: str) -> None:
        await self._locator(strategy, target).click(timeout=DEFAULT_TIMEOUT_MS)
        self._check_domain()

    async def fill(self, strategy: str, target: str, value: str) -> None:
        await self._locator(strategy, target).fill(value, timeout=DEFAULT_TIMEOUT_MS)
        self._check_domain()

    async def extract(self, strategy: str, target: str) -> str:
        loc = self._locator(strategy, target)
        return (await loc.inner_text(timeout=DEFAULT_TIMEOUT_MS)).strip()

    async def navigate(self, url: str) -> None:
        await self.page.goto(url, wait_until="domcontentloaded")
        self._check_domain()