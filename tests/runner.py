import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
from utils.excel_reader import read_testdata
from utils.actions import prepare_clean_session
from utils.driver_factory import (
    create_local_driver,
    create_browserstack_driver,
)

# flows
from tests.flows.login_flow import run as run_login
from tests.flows.signup_flow import run as run_signup
from tests.flows.contact_flow import run as run_contact
from tests.flows.add_to_cart_flow import run as run_cart
from tests.flows.purchase_flow import run as run_purchase

logger = get_logger("ddt_runner")

FLOW_MAP = {
    "login": run_login,
    "signup": run_signup,
    "contact": run_contact,
    "add_to_cart": run_cart,
    "purchase": run_purchase,
}


def run_sheet(mode, browser, preset, data_path, sheet):
    rows = read_testdata(data_path, sheet_name=sheet)
    logger.info(f"Loaded {len(rows)} rows from sheet '{sheet}'")
    results = []

    for row in rows:
        test_id = row.get("test_id")
        logger.info(f"=== Running {test_id} ({sheet}) in {mode} mode ===")
        driver = None

        try:
            # Создаём driver в зависимости от режима
            if mode == "local":
                driver = create_local_driver(browser)
                prepare_clean_session(driver, logger)
            elif mode == "browserstack":
                test_name = f"{sheet} - {test_id}"
                driver = create_browserstack_driver(preset, test_name)
                # BrowserStack уже создаёт чистую сессию
            else:
                raise ValueError(f"Unknown mode: {mode}")

            # Выполняем flow
            flow = FLOW_MAP.get(sheet)
            res = flow(driver, row, logger)
            results.append(res)

        except Exception as e:
            logger.exception(f"Fatal error running {test_id}: {e}")
            results.append({"id": test_id, "status": "ERROR", "error": str(e)})
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    return results


def main():
    parser = argparse.ArgumentParser(description="Data-Driven Test Runner")
    parser.add_argument("--mode", choices=["local", "browserstack", "sauce"],
                        default="local", help="Execution mode")
    parser.add_argument("--browser", default="chrome",
                        help="Browser for local mode")
    parser.add_argument("--preset", default="chrome_latest_win",
                        help="Preset for cloud mode (e.g., chrome_latest_win, firefox_latest_win)")
    parser.add_argument("--sheet", default="login",
                        help="Excel sheet to test")
    parser.add_argument("--data", default="sample_test_data.xlsx",
                        help="Path to Excel test data file")
    args = parser.parse_args()

    logger.info(f"Starting DDT Runner: mode={args.mode}, sheet={args.sheet}, preset={args.preset}")

    results = run_sheet(args.mode, args.browser, args.preset, args.data, args.sheet)

    # Выводим результаты
    print("\n" + "=" * 80)
    print("TEST RESULTS:")
    print("=" * 80)
    for r in results:
        status_symbol = "✅" if r.get("status") == "PASSED" else "❌"
        print(
            f"{status_symbol} {r.get('id')}: {r.get('status')} (expected: {r.get('expected')}, actual: {r.get('actual')})")
        if r.get('details'):
            print(f"   Details: {r['details'][:100]}...")
    print("=" * 80)

    # Подсчёт статистики
    passed = sum(1 for r in results if r.get('status') == 'PASSED')
    failed = sum(1 for r in results if r.get('status') == 'FAILED')
    errors = sum(1 for r in results if r.get('status') == 'ERROR')

    print(f"\nSummary: {passed} passed, {failed} failed, {errors} errors out of {len(results)} total")
    print("=" * 80)


if __name__ == "__main__":
    main()