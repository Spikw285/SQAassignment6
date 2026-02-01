import sys
import argparse
import os
import pprint
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
from utils.excel_reader import read_testdata
from utils.actions import prepare_clean_session
from utils.driver_factory import (
    create_local_driver,
    create_browserstack_driver,
    create_sauce_driver
)
from config import browserstack_config, sauce_config

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

logger = get_logger("ddt_runner")

def run_sheet(mode, browser, preset, data_path, sheet, bs_user=None, bs_key=None, sauce_user=None, sauce_key=None):
    rows = read_testdata(data_path, sheet_name=sheet)
    logger.info(f"Loaded {len(rows)} rows from {sheet}")
    results = []
    for row in rows:
        test_id = row.get("test_id")
        logger.info(f"=== Running {test_id} ({sheet}) ===")
        driver = None
        try:
            if mode == "local":
                driver = create_local_driver(browser)
                prepare_clean_session(driver, logger)
            elif mode == "browserstack":
                driver = create_browserstack_driver(preset, bs_user, bs_key)
                prepare_clean_session(driver, logger)
            elif mode == "sauce":
                driver = create_sauce_driver(preset, sauce_user, sauce_key)
                prepare_clean_session(driver, logger)
            else:
                raise ValueError("Unknown mode")

            # execute flow
            flow = FLOW_MAP.get(sheet)
            res = flow(driver, row, logger)
            results.append(res)
        except Exception as e:
            logger.exception(f"Fatal error running {test_id}: {e}")
            results.append({"id": test_id, "status":"ERROR", "error": str(e)})
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
        finally:
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["local","browserstack","sauce"], default="local")
    parser.add_argument("--browser", default="chrome")
    parser.add_argument("--preset", default="chrome_latest_win")
    parser.add_argument("--sheet", default="login")
    parser.add_argument("--data", default="sample_test_data.xlsx")
    args = parser.parse_args()

    bs_user = os.getenv("BROWSERSTACK_USER") or os.getenv("BROWSERSTACK_USERNAME")
    bs_key = os.getenv("BROWSERSTACK_KEY") or os.getenv("BROWSERSTACK_ACCESS_KEY")
    sauce_user = os.getenv("SAUCE_USERNAME")
    sauce_key = os.getenv("SAUCE_ACCESS_KEY")

    results = run_sheet(args.mode, args.browser, args.preset, args.data, args.sheet, bs_user, bs_key, sauce_user, sauce_key)
    pprint.pprint(results)


if __name__ == "__main__":
    main()
