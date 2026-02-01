from selenium.webdriver.common.by import By
from utils.actions import wait_visible, click_with_fallback, save_screenshot, wait_clickable
from selenium.common.exceptions import TimeoutException

HOME_URL = "https://www.demoblaze.com"

def run(driver, data, logger):
    test_id = data.get("test_id", "P-UNKNOWN")
    logger.info(f"[{test_id}] purchase_flow start")
    try:
        driver.get(HOME_URL)
        prod = data.get("product","")
        prod_link = wait_visible(driver, By.LINK_TEXT, prod, timeout=10)
        click_with_fallback(driver, prod_link, logger, f"prod_{prod}")
        add_btn = wait_visible(driver, By.XPATH, "//a[text()='Add to cart']", timeout=8)
        click_with_fallback(driver, add_btn, logger, "add_to_cart")
        try:
            alert = driver.switch_to.alert
            logger.info(f"Add alert: {alert.text}")
            alert.accept()
        except Exception:
            logger.warning("No add-to-cart alert")

        cart = wait_visible(driver, By.ID, "cartur", timeout=10)
        click_with_fallback(driver, cart, logger, "cart_link")
        wait_visible(driver, By.ID, "tbodyid", timeout=10)

        place = wait_clickable(driver, By.XPATH, "//button[text()='Place Order']", timeout=8)
        click_with_fallback(driver, place, logger, "place_order")
        # wait modal fields
        name = wait_visible(driver, By.ID, "name", timeout=8)
        country = wait_visible(driver, By.ID, "country", timeout=8)
        city = wait_visible(driver, By.ID, "city", timeout=8)
        card = wait_visible(driver, By.ID, "card", timeout=8)
        month = wait_visible(driver, By.ID, "month", timeout=8)
        year = wait_visible(driver, By.ID, "year", timeout=8)

        name.clear(); name.send_keys(str(data.get("name","")))
        country.clear(); country.send_keys(str(data.get("country","")))
        city.clear(); city.send_keys(str(data.get("city","")))
        card.clear(); card.send_keys(str(data.get("card","")))
        month.clear(); month.send_keys(str(data.get("month","")))
        year.clear(); year.send_keys(str(data.get("year","")))

        purchase = wait_visible(driver, By.XPATH, "//div[@id='orderModal']//button[text()='Purchase']", timeout=8)
        click_with_fallback(driver, purchase, logger, "purchase_btn")

        try:
            # sweet-alert presence
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "sweet-alert")))
            actual = "PASS"
        except TimeoutException:
            actual = "FAIL"

        save_screenshot(driver, f"{test_id}_purchase_{actual}", logger)
        return {"id": test_id, "expected": data.get("expected_result"), "actual": actual, "status": "PASSED" if actual==str(data.get("expected_result")).upper() else "FAILED"}
    except Exception as e:
        logger.exception("Exception in purchase_flow")
        save_screenshot(driver, f"{test_id}_purchase_exception", logger)
        return {"id": test_id, "status":"ERROR", "error": str(e)}
