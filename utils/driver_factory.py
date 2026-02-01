from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FFService

from config import browserstack_config


def create_local_driver(browser: str = 'chrome') -> WebDriver:
    """Создаёт локальный WebDriver"""
    browser = browser.lower()
    if browser == 'chrome':
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")  # Скрываем автоматизацию
        driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=options
        )
        return driver
    elif browser == 'firefox':
        options = webdriver.FirefoxOptions()
        driver = webdriver.Firefox(
            service=FFService(GeckoDriverManager().install()),
            options=options
        )
        driver.maximize_window()
        return driver
    elif browser == 'safari':
        driver = webdriver.Safari()
        driver.maximize_window()
        return driver
    else:
        raise ValueError(f"Unsupported local browser: {browser}")


def create_browserstack_driver(preset_key: str = 'chrome_latest_win', test_name: str = None) -> WebDriver:
    """
    Создаёт WebDriver для BrowserStack

    Args:
        preset_key: ключ preset из browserstack_config.BROWSERSTACK_PRESETS
        test_name: кастомное имя теста (опционально)

    Returns:
        WebDriver instance подключенный к BrowserStack
    """
    bs_user = browserstack_config.BS_USER
    bs_key = browserstack_config.BS_KEY

    if not bs_user or not bs_key:
        raise ValueError(
            "BrowserStack credentials not found! "
            "Set BROWSERSTACK_USERNAME and BROWSERSTACK_ACCESS_KEY in .env file"
        )

    # Получаем capabilities
    caps = browserstack_config.get_capabilities(preset_key, test_name)

    # Создаём hub URL с credentials
    hub_url = f"https://{bs_user}:{bs_key}@hub-cloud.browserstack.com/wd/hub"

    print(f"Connecting to BrowserStack...")
    print(f"Preset: {preset_key}")
    print(f"Browser: {caps.get('browserName')} {caps.get('browserVersion')}")
    print(f"Platform: {caps['bstack:options']['os']} {caps['bstack:options']['osVersion']}")

    # Создаём driver
    driver = webdriver.Remote(
        command_executor=hub_url,
        options=_dict_to_options(caps)
    )

    return driver


def _dict_to_options(caps: dict):
    """
    Конвертирует dict capabilities в соответствующий Options объект
    """
    browser_name = caps.get('browserName', '').lower()

    if 'chrome' in browser_name:
        options = webdriver.ChromeOptions()
    elif 'firefox' in browser_name:
        options = webdriver.FirefoxOptions()
    elif 'safari' in browser_name:
        options = webdriver.SafariOptions()
    elif 'edge' in browser_name or 'microsoftedge' in browser_name:
        options = webdriver.EdgeOptions()
    else:
        # Fallback to ChromeOptions
        options = webdriver.ChromeOptions()

    # Устанавливаем capabilities
    for key, value in caps.items():
        options.set_capability(key, value)

    return options