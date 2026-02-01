from selenium.webdriver.common.by import By
from utils.actions import wait_visible, wait_until_modal_shown, click_with_fallback, save_screenshot
HOME_URL = "https://www.demoblaze.com"

def run(driver, data, logger):
    test_id = data.get("test_id", "C-UNKNOWN")
    logger.info(f"[{test_id}] contact_flow start")
    try:
        driver.get(HOME_URL)
        contact = wait_visible(driver, By.XPATH, "//a[text()='Contact']", timeout=10)
        if not click_with_fallback(driver, contact, logger, "contact_link"):
            save_screenshot(driver, f"{test_id}_contact_open_failed", logger)
            return {"id": test_id, "status":"ERROR", "error":"open_contact_failed"}

        wait_until_modal_shown(driver, (By.ID, "exampleModal"), timeout=10)
        email = wait_visible(driver, By.ID, "recipient-email", timeout=8)
        name = wait_visible(driver, By.ID, "recipient-name", timeout=8)
        message = wait_visible(driver, By.ID, "message-text", timeout=8)

        email.clear(); email.send_keys(str(data.get("email","")))
        name.clear(); name.send_keys(str(data.get("name","")))
        message.clear(); message.send_keys(str(data.get("message","")))

        send = wait_visible(driver, By.XPATH, "//div[@id='exampleModal']//button[text()='Send message']", timeout=8)
        if not click_with_fallback(driver, send, logger, "contact_send"):
            save_screenshot(driver, f"{test_id}_contact_send_failed", logger)
            return {"id": test_id, "status":"ERROR", "error":"contact_send_failed"}

        try:
            alert = driver.switch_to.alert
            logger.info(f"Contact alert: {alert.text}")
            alert.accept()
            actual = "PASS"
        except Exception:
            actual = "FAIL"

        save_screenshot(driver, f"{test_id}_contact_{actual}", logger)
        return {"id": test_id, "expected": data.get("expected_result"), "actual": actual, "status": "PASSED" if actual==str(data.get("expected_result")).upper() else "FAILED"}
    except Exception as e:
        logger.exception("Exception in contact_flow")
        save_screenshot(driver, f"{test_id}_contact_exception", logger)
        return {"id": test_id, "status":"ERROR", "error": str(e)}
