from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver, WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


DEFAULT_WAIT = 15


def wait_css(driver: WebDriver, selector: str, timeout: float = DEFAULT_WAIT) -> WebElement:
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )


def wait_clickable_css(driver: WebDriver, selector: str, timeout: float = DEFAULT_WAIT) -> WebElement:
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
