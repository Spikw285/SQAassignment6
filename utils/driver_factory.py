import os
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver import Remote
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FFService

from config import browserstack_config, sauce_config

def create_local_driver(browser: str = 'chrome') -> WebDriver:
    browser = browser.lower()
    if browser == 'chrome':
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        return driver
    elif browser == 'firefox':
        options = webdriver.FirefoxOptions()
        driver = webdriver.Firefox(service=FFService(GeckoDriverManager().install()), options=options)
        driver.maximize_window()
        return driver
    elif browser == 'safari':
        # only on macOS
        driver = webdriver.Safari()
        driver.maximize_window()
        return driver
    else:
        raise ValueError("Unsupported local browser: " + browser)

def create_browserstack_driver(preset_key: str, bs_user: str, bs_key: str) -> WebDriver:
    preset = browserstack_config.BROWSERSTACK_PRESETS.get(preset_key)
    if not preset:
        raise ValueError("Unknown BrowserStack preset")
    browser_name, browser_version, os_name, os_version = preset
    caps = {
        "browserName": browser_name,
        "browserVersion": browser_version,
        "bstack:options": {
            "os": os_name,
            "osVersion": os_version,
            "projectName": "DDT Demo"
        }
    }
    hub = f"https://{bs_user}:{bs_key}@hub-cloud.browserstack.com/wd/hub"
    return Remote(command_executor=hub, desired_capabilities=caps)

def create_sauce_driver(preset_key: str, sauce_user: str, sauce_key: str) -> WebDriver:
    preset = sauce_config.SAUCE_PRESETS.get(preset_key)
    if not preset:
        raise ValueError("Unknown Sauce preset")
    browser_name, browser_version, platform_name = preset
    caps = {
        "browserName": browser_name,
        "browserVersion": browser_version,
        "platformName": platform_name,
        "sauce:options": {"name": "Demoblaze DDT"}
    }
    hub = f"https://{sauce_user}:{sauce_key}@ondemand.saucelabs.com/wd/hub"
    return Remote(command_executor=hub, desired_capabilities=caps)
