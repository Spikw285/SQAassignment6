from selenium.webdriver.common.by import By
from utils.actions import (
    wait_visible,
    wait_invisible,
    wait_until_modal_shown,
    click_with_fallback,
    save_screenshot,
)
from utils.popups import detect_popups
import time

HOME_URL = "https://www.demoblaze.com"
MAX_SIGNUP_ATTEMPTS = 3  # Максимум попыток регистрации


def run(driver, data, logger):
    test_id = data.get("test_id", "S-UNKNOWN")
    logger.info(f"[{test_id}] signup_flow start")
    result = {"id": test_id, "expected": data.get("expected_result"), "actual": None, "status": "NOT_RUN"}

    # История попыток для логирования
    attempts_history = []

    try:
        # Handle dynamic username generation
        username_raw = data.get("username", "")
        base_username = username_raw
        if isinstance(username_raw, str) and (username_raw.startswith("GENERATE_") or username_raw.startswith("AUTO_")):
            base_username = username_raw.replace("GENERATE_", "").replace("AUTO_", "")

        # Retry logic - до MAX_SIGNUP_ATTEMPTS попыток
        for attempt in range(1, MAX_SIGNUP_ATTEMPTS + 1):
            logger.info(f"[{test_id}] Attempt {attempt}/{MAX_SIGNUP_ATTEMPTS}")

            # Генерируем уникальное имя для каждой попытки
            if isinstance(username_raw, str) and (
                    username_raw.startswith("GENERATE_") or username_raw.startswith("AUTO_")):
                username = f"{base_username}_{int(time.time())}_{attempt}"
                logger.info(f"[{test_id}] Generated unique username: {username}")
            else:
                username = str(username_raw) if username_raw else ""

            # Попытка регистрации
            attempt_result = _attempt_signup(driver, data, username, test_id, attempt, logger)

            # Сохраняем результат попытки
            attempts_history.append({
                'attempt': attempt,
                'username': username,
                'actual': attempt_result['actual'],
                'details': attempt_result.get('details', '')
            })

            # Если успешно - прерываем цикл
            if attempt_result['actual'] == "PASS":
                logger.info(f"[{test_id}] Signup successful on attempt {attempt}")
                result['actual'] = "PASS"
                result[
                    'details'] = f"Success on attempt {attempt}/{MAX_SIGNUP_ATTEMPTS}. {attempt_result.get('details', '')}"
                break

            # Если это была последняя попытка - используем её результат
            if attempt == MAX_SIGNUP_ATTEMPTS:
                logger.warning(f"[{test_id}] All {MAX_SIGNUP_ATTEMPTS} attempts failed")
                result['actual'] = "FAIL"
                result[
                    'details'] = f"Failed all {MAX_SIGNUP_ATTEMPTS} attempts. Last: {attempt_result.get('details', '')}"
            else:
                # Не последняя попытка - логируем и продолжаем
                logger.warning(
                    f"[{test_id}] Attempt {attempt} failed: {attempt_result.get('details', '')}. Retrying...")
                # Небольшая пауза перед следующей попыткой
                time.sleep(1)

        # Добавляем историю всех попыток в результат
        if len(attempts_history) > 1:
            history_str = "\nAttempts history:\n" + "\n".join([
                f"  #{h['attempt']}: {h['actual']} - {h['username']} - {h['details'][:100]}"
                for h in attempts_history
            ])
            result['details'] = (result.get('details', '') + history_str).strip()
            logger.info(f"[{test_id}] {history_str}")

        # Определяем финальный статус
        expected = str(data.get('expected_result', "")).upper()
        result['status'] = "PASSED" if result['actual'] == expected else "FAILED"

        save_screenshot(driver, f"{test_id}_signup_final_{result['actual']}", logger)
        logger.info(
            f"[{test_id}] signup test finished: expected={expected}, actual={result['actual']}, status={result['status']}")
        return result

    except Exception as e:
        logger.exception(f"[{test_id}] Exception in signup_flow: {e}")
        save_screenshot(driver, f"{test_id}_signup_exception", logger)
        result.update({"actual": "ERROR", "status": "ERROR", "error": str(e)})
        return result
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def _attempt_signup(driver, data, username, test_id, attempt_num, logger):
    attempt_result = {
                      "actual": None,
                      "details": None
                     }

    try:
        driver.get(HOME_URL)

        # Open signup modal
        signup_btn = wait_visible(driver, By.ID, "signin2", timeout=10)
        if not click_with_fallback(driver, signup_btn, logger, "signin2"):
            save_screenshot(driver, f"{test_id}_attempt{attempt_num}_signup_open_failed", logger)
            attempt_result['actual'] = "ERROR"
            attempt_result['details'] = "Failed to open signup modal"
            return attempt_result

        wait_until_modal_shown(driver, (By.ID, "signInModal"), timeout=10)

        # Fill credentials
        username_field = wait_visible(driver, By.ID, "sign-username", timeout=8)
        password_field = wait_visible(driver, By.ID, "sign-password", timeout=8)
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(str(data.get("password", "")))
        logger.debug(f"[{test_id}] Attempt {attempt_num}: Credentials filled: username={username}")

        # Submit signup
        submit = wait_visible(driver, By.XPATH, "//div[@id='signInModal']//button[text()='Sign up']", timeout=8)
        if not click_with_fallback(driver, submit, logger, "signup_submit"):
            save_screenshot(driver, f"{test_id}_attempt{attempt_num}_submit_failed", logger)
            attempt_result['actual'] = "ERROR"
            attempt_result['details'] = "Failed to click submit button"
            return attempt_result

        # Wait for modal to close
        try:
            logger.debug(f"[{test_id}] Attempt {attempt_num}: Waiting for signup modal to close...")
            wait_invisible(driver, By.ID, "signInModal", timeout=5)
            logger.debug(f"[{test_id}] Signup modal closed successfully")
        except Exception as e:
            logger.warning(f"[{test_id}] Signup modal did not close: {e}")

        # Detect popup/alert
        pop = detect_popups(driver, timeout=6.0, logger=logger, modal_ids=[])
        ptype = pop.get("type")
        ptext = (pop.get("text") or "").strip()

        logger.debug(f"[{test_id}] Attempt {attempt_num}: detect_popups returned: type={ptype}, text={ptext[:200]}")

        # Determine result based on alert text
        if ptype == "native_alert":
            # Check if success or failure
            if "successful" in ptext.lower() or "sign up successful" in ptext.lower():
                attempt_result['actual'] = "PASS"
                attempt_result['details'] = f"native_alert: {ptext}"
                logger.info(f"[{test_id}] Attempt {attempt_num}: Signup successful -> PASS")
            else:
                # Failure alert (user exists, validation error, etc.)
                attempt_result['actual'] = "FAIL"
                attempt_result['details'] = f"native_alert: {ptext}"
                logger.info(f"[{test_id}] Attempt {attempt_num}: Signup failed -> FAIL: {ptext}")
        elif ptype in ("sweet_alert", "modal", "inline"):
            # DOM popup - likely an error
            attempt_result['actual'] = "FAIL"
            attempt_result['details'] = f"{ptype}: {ptext}"
            logger.info(f"[{test_id}] Attempt {attempt_num}: DOM popup detected -> FAIL: {ptext[:200]}")
        else:
            # No popup detected - ambiguous, likely error
            attempt_result['actual'] = "FAIL"
            attempt_result['details'] = "no popup detected"
            logger.warning(f"[{test_id}] Attempt {attempt_num}: No popup detected -> FAIL")
            save_screenshot(driver, f"{test_id}_attempt{attempt_num}_no_popup", logger)

        save_screenshot(driver, f"{test_id}_attempt{attempt_num}_{attempt_result['actual']}", logger)
        return attempt_result

    except Exception as e:
        logger.exception(f"[{test_id}] Exception in attempt {attempt_num}: {e}")
        save_screenshot(driver, f"{test_id}_attempt{attempt_num}_exception", logger)
        attempt_result['actual'] = "ERROR"
        attempt_result['details'] = f"exception: {str(e)}"
        return attempt_result