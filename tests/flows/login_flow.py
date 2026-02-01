from selenium.webdriver.common.by import By
from utils.actions import (
    wait_visible,
    wait_until_modal_shown,
    click_with_fallback,
    save_screenshot,
    debug_element_state,
)
# detect_popups должен лежать в utils/popups.py
from utils.popups import detect_popups

HOME_URL = "https://www.demoblaze.com"

def run(driver, data, logger):
    test_id = data.get("test_id", "L-UNKNOWN")
    logger.info(f"[{test_id}] login_flow start")
    result = {"id": test_id, "expected": data.get("expected_result"), "actual": None, "status": "NOT_RUN"}

    try:
        # Optional: try to clear session if helper exists (keeps this flow robust)
        try:
            from utils.actions import prepare_clean_session
            try:
                prepare_clean_session(driver, logger)
                logger.debug("Session cleaned before test")
            except Exception:
                logger.debug("prepare_clean_session exists but failed; continuing")
        except Exception:
            # helper not present — ok to continue
            pass

        driver.get(HOME_URL)

        # open login modal (safe click)
        login_button = wait_visible(driver, By.ID, "login2", timeout=10)
        if not click_with_fallback(driver, login_button, logger, "login2"):
            logger.error(f"[{test_id}] Could not click login2 button")
            save_screenshot(driver, f"{test_id}_login_open_failed", logger)
            result.update({"actual":"ERROR","status":"ERROR","error":"click_failed"})
            return result

        # wait until modal fully shown/interactive
        wait_until_modal_shown(driver, (By.ID, "logInModal"), timeout=10)

        # locate inputs (re-query after modal shown)
        username = wait_visible(driver, By.ID, "loginusername", timeout=8)
        password = wait_visible(driver, By.ID, "loginpassword", timeout=8)

        # debug state & enter credentials
        debug_element_state(username, f"{test_id}_loginusername", logger)
        username.clear(); username.send_keys(str(data.get("username","")))
        password.clear(); password.send_keys(str(data.get("password","")))
        logger.debug(f"[{test_id}] Credentials filled")

        submit = wait_visible(driver, By.XPATH, "//div[@id='logInModal']//button[text()='Log in']", timeout=8)
        if not click_with_fallback(driver, submit, logger, "login_submit"):
            logger.error(f"[{test_id}] Failed to click login submit")
            save_screenshot(driver, f"{test_id}_login_submit_failed", logger)
            result.update({"actual":"ERROR","status":"ERROR","error":"submit_click_failed"})
            return result

        # --- improved outcome detection using detect_popups ---
        pop = detect_popups(driver, timeout=6.0, logger=logger, modal_ids=["logInModal"])
        ptype = pop.get("type")
        ptext = (pop.get("text") or "").strip()

        logger.debug(f"[{test_id}] detect_popups returned: type={ptype}, text={ptext[:200]}")

        # Decide actual result based on popup detection and logout element
        actual = None
        details = None

        if ptype == "native_alert":
            # native alert most likely indicates failure (error message)
            actual = "FAIL"
            details = f"native_alert: {ptext}"
            logger.info(f"[{test_id}] native alert detected -> FAIL: {ptext[:200]}")
        elif ptype in ("sweet_alert", "modal", "inline"):
            # DOM popup present: typically indicates failure (login error or info)
            # If you have an app-specific rule where certain modal text means PASS, handle it here.
            actual = "FAIL"
            details = f"{ptype}: {ptext}"
            logger.info(f"[{test_id}] DOM popup ({ptype}) detected -> FAIL: {ptext[:200]}")
        else:
            # no popup detected — check logout presence as success indicator
            try:
                logout_nodes = driver.find_elements(By.ID, "logout2")
                if logout_nodes:
                    actual = "PASS"
                    details = "logout2 present"
                    logger.info(f"[{test_id}] logout2 found -> PASS")
                else:
                    # neither popup nor logout — ambiguous: treat as FAIL and capture debug info
                    actual = "FAIL"
                    details = "no popup and no logout found"
                    logger.warning(f"[{test_id}] No popup and no logout -> FAIL (ambiguous)")
                    # capture screenshot and snippet to help debugging
                    save_screenshot(driver, f"{test_id}_no_indicator", logger)
            except Exception as e:
                actual = "FAIL"
                details = f"exception_during_check: {e}"
                logger.exception(f"[{test_id}] Exception while checking logout presence")

        # fill result and compare with expected
        result['actual'] = actual
        expected = str(data.get('expected_result', "")).upper()
        result['status'] = "PASSED" if actual == expected else "FAILED"
        if details:
            result['details'] = details

        # Save final screenshot for records
        save_screenshot(driver, f"{test_id}_login_{actual}", logger)

        logger.info(f"[{test_id}] login test finished: expected={expected}, actual={actual}, status={result['status']}")
        return result

    except Exception as e:
        logger.exception(f"[{test_id}] Exception in login_flow: {e}")
        save_screenshot(driver, f"{test_id}_login_exception", logger)
        result.update({"actual":"ERROR","status":"ERROR","error": str(e)})
        return result
    finally:
        try:
            driver.quit()
        except Exception:
            pass
