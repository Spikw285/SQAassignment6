from selenium.webdriver.common.by import By
from utils.actions import (
    wait_visible,
    wait_invisible,
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

        # КРИТИЧНО: Проверяем результат (alert/success) СРАЗУ после submit
        # НЕ ждём закрытия модалки, т.к. alert может заблокировать её!
        logger.debug(f"[{test_id}] Checking for result popup (alert or success)...")

        # Даём небольшую паузу для появления alert'а или закрытия модалки
        import time
        time.sleep(1.5)

        # Сначала проверяем ТОЛЬКО alert (приоритет!)
        alert_text = None
        try:
            alert = driver.switch_to.alert
            alert_text = alert.text
            logger.info(f"[{test_id}] Native alert found: {alert_text}")
            alert.accept()
            logger.debug(f"[{test_id}] Alert accepted")
        except:
            pass  # No alert

        # Decide actual result based on alert or logout presence
        actual = None
        details = None

        if alert_text:
            # Native alert detected - это всегда ошибка на demoblaze
            actual = "FAIL"
            details = f"native_alert: {alert_text}"
            logger.info(f"[{test_id}] native alert detected -> FAIL: {alert_text}")

            # Закрываем модалку вручную после ошибки
            try:
                close_btn = driver.find_element(By.XPATH, "//div[@id='logInModal']//button[text()='Close']")
                close_btn.click()
                logger.debug(f"[{test_id}] Closed login modal after alert")
            except:
                pass
        else:
            # No alert — check logout presence as success indicator
            try:
                logout_nodes = driver.find_elements(By.ID, "logout2")
                if logout_nodes and logout_nodes[0].is_displayed():
                    actual = "PASS"
                    details = "logout2 present"
                    logger.info(f"[{test_id}] logout2 found -> PASS")
                else:
                    # No logout - check if modal still open (might indicate error)
                    try:
                        modal = driver.find_element(By.ID, "logInModal")
                        if modal.is_displayed():
                            actual = "FAIL"
                            details = "login modal still open (no alert, no logout)"
                            logger.warning(f"[{test_id}] Modal still open -> FAIL")
                        else:
                            actual = "FAIL"
                            details = "no logout found after modal closed"
                            logger.warning(f"[{test_id}] No logout found -> FAIL")
                    except:
                        actual = "FAIL"
                        details = "no popup and no logout found"
                        logger.warning(f"[{test_id}] No indicators found -> FAIL (ambiguous)")

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
