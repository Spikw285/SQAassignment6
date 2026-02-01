from selenium.webdriver.common.by import By
from utils.actions import wait_visible, wait_until_modal_shown, click_with_fallback, save_screenshot

HOME_URL = "https://www.demoblaze.com"

def run(driver, data, logger):
    test_id = data.get("test_id", "S-UNKNOWN")
    logger.info(f"[{test_id}] signup_flow start")
    result = {"id": test_id, "expected": data.get("expected_result"), "actual": None, "status": "NOT_RUN"}
    try:
        driver.get(HOME_URL)
        signup_btn = wait_visible(driver, By.ID, "signin2", timeout=10)
        if not click_with_fallback(driver, signup_btn, logger, "signin2"):
            save_screenshot(driver, f"{test_id}_signup_open_failed", logger)
            return {"id": test_id, "status":"ERROR", "error":"open_signup_failed"}

        wait_until_modal_shown(driver, (By.ID, "signInModal"), timeout=10)
        username = wait_visible(driver, By.ID, "sign-username", timeout=8)
        password = wait_visible(driver, By.ID, "sign-password", timeout=8)

        username.clear(); username.send_keys(str(data.get("username","")))
        password.clear(); password.send_keys(str(data.get("password","")))

        submit = wait_visible(driver, By.XPATH, "//div[@id='signInModal']//button[text()='Sign up']", timeout=8)
        if not click_with_fallback(driver, submit, logger, "signup_submit"):
            save_screenshot(driver, f"{test_id}_signup_submit_failed", logger)
            return {"id": test_id, "status":"ERROR", "error":"signup_submit_failed"}

        try:
            alert = driver.switch_to.alert
            text = alert.text
            logger.info(f"Signup alert: {text}")
            alert.accept()
            actual = "PASS" if "successful" in text.lower() or "sign up" in text.lower() else "FAIL"
        except Exception:
            actual = "FAIL"

        result['actual'] = actual
        result['status'] = "PASSED" if actual == str(data.get("expected_result")).upper() else "FAILED"
        save_screenshot(driver, f"{test_id}_signup_{actual}", logger)
        return result
    except Exception as e:
        logger.exception("Exception in signup_flow")
        save_screenshot(driver, f"{test_id}_signup_exception", logger)
        return {"id": test_id, "status":"ERROR", "error": str(e)}
