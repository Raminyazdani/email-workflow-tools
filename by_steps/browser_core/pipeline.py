from __future__ import annotations

import time
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver

from .config import StepSetup
from .driver import create_chrome_driver
from .utils import timestamped_name
from .waiters import DEFAULT_WAIT, wait_clickable_css, wait_css


class PipelineBrowser:
    def __init__(self, driver: WebDriver, setup: StepSetup) -> None:
        self.driver = driver
        self.setup = setup

    @classmethod
    def from_setup(cls, setup: StepSetup) -> "PipelineBrowser":
        driver = create_chrome_driver(setup)
        browser = cls(driver=driver, setup=setup)
        if setup.browser.start_url:
            browser.open(setup.browser.start_url)
        return browser

    def open(self, url: str) -> None:
        self.driver.get(url)

    def wait_css(self, selector: str, timeout: float = DEFAULT_WAIT):
        return wait_css(self.driver, selector, timeout=timeout)

    def click_css(self, selector: str, timeout: float = DEFAULT_WAIT) -> None:
        element = wait_clickable_css(self.driver, selector, timeout=timeout)
        element.click()

    def type_css(
        self,
        selector: str,
        text: str,
        *,
        clear_first: bool = True,
        timeout: float = DEFAULT_WAIT,
    ) -> None:
        element = self.wait_css(selector, timeout=timeout)
        if clear_first:
            element.clear()
        element.send_keys(text)

    def get_text_css(self, selector: str, timeout: float = DEFAULT_WAIT) -> str:
        return self.wait_css(selector, timeout=timeout).text

    def save_html(self, file_name: str | None = None, html: str | None = None) -> Path:
        target = self.setup.artifacts_dir / (file_name or timestamped_name("page", ".html"))
        content = html if html is not None else self.driver.page_source
        target.write_text(content, encoding="utf-8")
        return target

    def save_screenshot(self, file_name: str | None = None) -> Path:
        target = self.setup.artifacts_dir / (file_name or timestamped_name("page", ".png"))
        self.driver.save_screenshot(str(target))
        return target

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)

    def quit(self) -> None:
        self.driver.quit()

    def __enter__(self) -> "PipelineBrowser":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.quit()
