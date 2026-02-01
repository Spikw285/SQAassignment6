import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
import os

SCREENSHOT_DIR = os.path.join(os.getcwd(), "logs", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def prepare_clean_session(driver, logger=None):
    try:
        driver.delete_all_cookies()
    except Exception as e:
        if logger: logger.warning(f"Failed to delete cookies: {e}")
    try:
        driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
    except Exception:
        if logger: logger.exception("Clear storage failed")


def save_screenshot(driver: WebDriver, name: str, logger=None):
    safe_name = name.replace(" ", "_").replace("/", "_")
    path = os.path.join(SCREENSHOT_DIR, f"{safe_name}.png")
    try:
        driver.save_screenshot(path)
        if logger: logger.info(f"Saved screenshot: {path}")
    except Exception:
        if logger: logger.exception("Failed to save screenshot")

def wait_visible(driver: WebDriver, by, value, timeout: int = 10):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, value)))

def wait_clickable(driver: WebDriver, by, value, timeout: int = 10):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))

def wait_alert(driver: WebDriver, timeout: int = 5):
    return WebDriverWait(driver, timeout).until(EC.alert_is_present())

def wait_until_modal_shown(driver: WebDriver, by_value_tuple: tuple, timeout: int = 8):
    by, val = by_value_tuple
    modal = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, val)))
    try:
        WebDriverWait(driver, timeout).until(lambda d: 'show' in (modal.get_attribute('class') or '') or modal.is_displayed())
    except TimeoutException:
        # proceed even if 'show' class absent
        pass
    time.sleep(0.12)
    return modal

def scroll_into_view(driver: WebDriver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element)
    except Exception:
        pass

def debug_element_state(element, label: str = None, logger=None):
    try:
        label = label or "element"
        disp = element.is_displayed()
        enabled = element.is_enabled()
        outer = element.get_attribute('outerHTML') or ""
        snippet = outer[:600]
        if logger:
            logger.debug(f"[DEBUG] {label} - displayed={disp}, enabled={enabled}, outerHTML_snippet={snippet}")
    except Exception:
        if logger:
            logger.exception("Failed to get element debug state")

def click_with_fallback(driver: WebDriver, element, logger=None, name_for_logs: str = None):
    nm = name_for_logs or (element.get_attribute('id') or element.get_attribute('class') or str(element))
    try:
        scroll_into_view(driver, element)
        element.click()
        if logger: logger.debug(f"Clicked element normally: {nm}")
        return True
    except Exception as e1:
        if logger: logger.warning(f"Normal click failed for {nm}: {e1}; trying ActionChains")
        try:
            ActionChains(driver).move_to_element(element).click().perform()
            if logger: logger.debug(f"Clicked element via ActionChains: {nm}")
            return True
        except Exception as e2:
            if logger: logger.warning(f"ActionChains failed for {nm}: {e2}; trying JS click")
            try:
                driver.execute_script("arguments[0].click();", element)
                if logger: logger.debug(f"Clicked element via JS: {nm}")
                return True
            except Exception as e3:
                if logger: logger.exception(f"All click methods failed for {nm}: {e3}")
                debug_element_state(element, nm, logger)
                return False
