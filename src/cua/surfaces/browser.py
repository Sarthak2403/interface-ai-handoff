from __future__ import annotations
from typing import Protocol
from playwright.async_api import Page

class ComputerSurface(Protocol):
    async def observe(self) -> dict: ...
    async def click(self, strategy: str, target: str) -> None: ...
    async def fill(self, strategy: str, target: str, value: str) -> None: ...
    async def extract(self, strategy: str, target: str) -> str: ...
    async def navigate(self, url: str) -> None: ...

class BrowserSurface:
    def __init__(self, page: Page):
        self.page = page

    async def observe(self) -> dict:
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "visible_text": await self.page.locator("body").inner_text(),
        }

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
        await self._locator(strategy, target).click()

    async def fill(self, strategy: str, target: str, value: str) -> None:
        await self._locator(strategy, target).fill(value)

    async def extract(self, strategy: str, target: str) -> str:
        loc = self._locator(strategy, target)
        return (await loc.inner_text()).strip()

    async def navigate(self, url: str) -> None:
        await self.page.goto(url, wait_until="domcontentloaded")
