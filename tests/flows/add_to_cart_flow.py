from selenium.webdriver.common.by import By
from utils.actions import wait_visible, click_with_fallback, save_screenshot
from selenium.common.exceptions import NoSuchElementException

HOME_URL = "https://www.demoblaze.com"

def run(driver, data, logger):
    test_id = data.get("test_id", "A-UNKNOWN")
    logger.info(f"[{test_id}] add_to_cart_flow start")
    try:
        driver.get(HOME_URL)
        products = [p.strip() for p in str(data.get("product","")).split(";") if p.strip()]
        added = []
        for prod in products:
            logger.info(f"[{test_id}] add product: {prod}")
            prod_link = wait_visible(driver, By.LINK_TEXT, prod, timeout=10)
            if not click_with_fallback(driver, prod_link, logger, f"prod_link_{prod}"):
                save_screenshot(driver, f"{test_id}_prod_click_failed_{prod}", logger)
                return {"id": test_id, "status":"ERROR", "error":"product_click_failed"}

            add_btn = wait_visible(driver, By.XPATH, "//a[text()='Add to cart']", timeout=8)
            if not click_with_fallback(driver, add_btn, logger, f"add_to_cart_{prod}"):
                save_screenshot(driver, f"{test_id}_add_click_failed_{prod}", logger)
                return {"id": test_id, "status":"ERROR", "error":"add_click_failed"}
            # alert accept
            try:
                alert = driver.switch_to.alert
                logger.info(f"Add alert: {alert.text}")
                alert.accept()
            except Exception:
                logger.warning("No add-to-cart alert")
            added.append(prod)
            # go home
            home = wait_visible(driver, By.XPATH, "//a[text()='Home '] | //a[text()='Home']", timeout=10)
            click_with_fallback(driver, home, logger, "home_link")
            wait_visible(driver, By.ID, "tbodyid", timeout=10)

        # verify cart
        cart = wait_visible(driver, By.ID, "cartur", timeout=10)
        click_with_fallback(driver, cart, logger, "cart_link")
        wait_visible(driver, By.ID, "tbodyid", timeout=10)
        missing = []
        for prod in added:
            try:
                driver.find_element(By.XPATH, f"//td[text()='{prod}']")
            except NoSuchElementException:
                missing.append(prod)
        actual = "PASS" if not missing else "FAIL"
        if missing:
            logger.warning(f"[{test_id}] missing in cart: {missing}")
        save_screenshot(driver, f"{test_id}_cart_{actual}", logger)
        return {"id": test_id, "expected": data.get("expected_result"), "actual": actual, "status": "PASSED" if actual==str(data.get("expected_result")).upper() else "FAILED"}
    except Exception as e:
        logger.exception("Exception in add_to_cart_flow")
        save_screenshot(driver, f"{test_id}_cart_exception", logger)
        return {"id": test_id, "status":"ERROR", "error": str(e)}
