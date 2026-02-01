import time
from typing import Optional, Dict, Any, List
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoAlertPresentException, WebDriverException

DEFAULT_INLINE_SELECTORS = [
    "div.alert",            # bootstrap alerts
    "div[role='alert']",
    ".toast",               # toast libraries
    ".notify",              # custom
    ".notification",
]

def detect_popups(driver,
                  timeout: float = 8.0,
                  poll_interval: float = 0.25,
                  logger=None,
                  modal_ids: Optional[List[str]] = None,
                  extra_inline_selectors: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Wait up to `timeout` seconds, polling for any popup. Returns a dict:
    {
      "type": "native_alert" | "sweet_alert" | "modal" | "inline" | "none",
      "text": "detected text or ''",
      "element": WebElement or None,
      "selector": selector used or None
    }

    - modal_ids: optional list of modal element ids to check (e.g. ['logInModal','signInModal','orderModal'])
    - extra_inline_selectors: additional CSS selectors for inline alerts on this site
    """
    end = time.time() + timeout
    inline_selectors = DEFAULT_INLINE_SELECTORS.copy()
    if extra_inline_selectors:
        inline_selectors = extra_inline_selectors + inline_selectors

    modal_ids = modal_ids or ["logInModal", "signInModal", "orderModal", "exampleModal"]

    while time.time() < end:
        # 1) native JS alert
        try:
            alert = driver.switch_to.alert
            try:
                text = alert.text
            except Exception:
                text = ""
            # IMPORTANT: Accept alert to clear it and prevent blocking further checks
            try:
                alert.accept()
                if logger:
                    logger.debug(f"detect_popups: native alert detected and accepted: {text}")
            except Exception as e:
                if logger:
                    logger.warning(f"detect_popups: failed to accept alert: {e}")
            return {"type": "native_alert", "text": text or "", "element": None, "selector": None}
        except NoAlertPresentException:
            pass
        except WebDriverException:
            # sometimes switch_to.alert throws other errors in remote sessions; ignore and continue
            pass
        except Exception:
            pass

        # 2) sweet-alert (commonly .sweet-alert)
        try:
            sweets = driver.find_elements(By.CLASS_NAME, "sweet-alert")
            for s in sweets:
                if s.is_displayed():
                    txt = (s.text or "").strip()
                    if logger:
                        logger.debug(f"detect_popups: sweet-alert found: {txt[:200]}")
                    return {"type": "sweet_alert", "text": txt, "element": s, "selector": ".sweet-alert"}
        except Exception:
            pass

        # 3) bootstrap/modal (check provided modal ids or any .modal.show)
        try:
            # check given modal ids first
            for mid in modal_ids:
                try:
                    nodes = driver.find_elements(By.ID, mid)
                    for n in nodes:
                        if n.is_displayed():
                            txt = (n.text or "").strip()
                            if logger:
                                logger.debug(f"detect_popups: modal id={mid} visible, text={txt[:200]}")
                            return {"type": "modal", "text": txt, "element": n, "selector": f"#{mid}"}
                except Exception:
                    pass

            # fallback: any modal with .modal.show
            modal_shows = driver.find_elements(By.CSS_SELECTOR, ".modal.show")
            for m in modal_shows:
                if m.is_displayed():
                    txt = (m.text or "").strip()
                    if logger:
                        logger.debug(f"detect_popups: modal .modal.show visible, text={txt[:200]}")
                    return {"type": "modal", "text": txt, "element": m, "selector": ".modal.show"}
        except Exception:
            pass

        # 4) inline alerts / toasts
        try:
            for sel in inline_selectors:
                try:
                    nodes = driver.find_elements(By.CSS_SELECTOR, sel)
                    for n in nodes:
                        if n.is_displayed():
                            txt = (n.text or "").strip()
                            if txt:  # prefer nodes with text
                                if logger:
                                    logger.debug(f"detect_popups: inline selector={sel} => {txt[:200]}")
                                return {"type": "inline", "text": txt, "element": n, "selector": sel}
                except Exception:
                    pass
        except Exception:
            pass

        time.sleep(poll_interval)

    # nothing found
    if logger:
        logger.debug("detect_popups: no popup detected within timeout")
    return {"type": "none", "text": "", "element": None, "selector": None}
