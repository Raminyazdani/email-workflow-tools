from __future__ import annotations

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from .config import StepSetup
from .utils import clean_dict


def create_chrome_driver(setup: StepSetup) -> WebDriver:
    options = ChromeOptions()
    options.add_argument(f"--user-data-dir={setup.user_data_dir}")

    if setup.browser.profile_directory:
        options.add_argument(f"--profile-directory={setup.browser.profile_directory}")

    for argument in setup.browser.arguments:
        if argument:
            options.add_argument(argument)

    prefs = clean_dict(setup.browser.prefs)
    if setup.download_dir:
        prefs.setdefault("download.default_directory", str(setup.download_dir))

    if prefs:
        options.add_experimental_option("prefs", prefs)

    for key, value in clean_dict(setup.browser.experimental_options).items():
        if key == "prefs":
            continue
        options.add_experimental_option(key, value)

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(setup.timeouts.implicit)
    driver.set_page_load_timeout(setup.timeouts.page_load)
    driver.set_script_timeout(setup.timeouts.script)
    return driver
