"""
Pytest-based test runner для генерации красивых HTML отчётов

Использование:
    # Все тесты
    pytest tests/test_runner_pytest.py --html=reports/report.html --self-contained-html

    # Только login
    pytest tests/test_runner_pytest.py --sheet=login --html=reports/login.html --self-contained-html

    # С другим браузером
    pytest tests/test_runner_pytest.py --browser=firefox --html=reports/report.html --self-contained-html
"""
import pytest
import sys
from pathlib import Path

# Убедимся что корень проекта в sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
from utils.excel_reader import read_testdata

# Import flows
from tests.flows.login_flow import run as run_login
from tests.flows.signup_flow import run as run_signup
from tests.flows.contact_flow import run as run_contact
from tests.flows.add_to_cart_flow import run as run_cart
from tests.flows.purchase_flow import run as run_purchase

logger = get_logger("pytest_runner")

FLOW_MAP = {
    "login": run_login,
    "signup": run_signup,
    "contact": run_contact,
    "add_to_cart": run_cart,
    "purchase": run_purchase,
}

def get_test_cases(sheet_name, data_file):
    """Загружает тест-кейсы из Excel для конкретного sheet"""
    try:
        rows = read_testdata(data_file, sheet_name=sheet_name)
        return [(sheet_name, row) for row in rows]
    except Exception as e:
        logger.error(f"Failed to load {sheet_name}: {e}")
        return []

def pytest_generate_tests(metafunc):
    """Генерация тестов на основе данных из Excel"""
    if "test_case" in metafunc.fixturenames:
        # Получаем параметры из command line
        data_file = metafunc.config.getoption("--data-file", default="sample_test_data.xlsx")
        sheet = metafunc.config.getoption("--sheet", default=None)

        # Определяем какие sheets тестировать
        if sheet:
            sheets = [sheet]
        else:
            sheets = ["login", "signup", "contact", "add_to_cart", "purchase"]

        # Собираем все test cases
        all_cases = []
        for sheet_name in sheets:
            cases = get_test_cases(sheet_name, data_file)
            all_cases.extend(cases)

        # Параметризация с ID для красивых имён в отчёте
        metafunc.parametrize(
            "test_case",
            all_cases,
            ids=[f"{sheet}_{row.get('test_id', 'unknown')}" for sheet, row in all_cases]
        )

def test_flow(test_case, browser, request):
    """
    Основная функция теста - запускает flow для каждого test case
    """
    sheet_name, row = test_case
    test_id = row.get("test_id", "UNKNOWN")

    logger.info(f"=== Running {test_id} from sheet '{sheet_name}' ===")

    # Получаем нужный flow
    flow = FLOW_MAP.get(sheet_name)
    if not flow:
        pytest.fail(f"Unknown sheet/flow: {sheet_name}")

    # Запускаем flow
    result = flow(browser, row, logger)

    # Сохраняем результат в item для использования в хуках
    request.node.test_result = result

    # Логируем результат
    logger.info(f"[{test_id}] Result: {result}")

    # Проверяем статус
    status = result.get("status")
    actual = result.get("actual")
    expected = result.get("expected")
    details = result.get("details", "")

    # Assert для pytest
    assert status == "PASSED", (
        f"Test {test_id} FAILED\n"
        f"Expected: {expected}\n"
        f"Actual: {actual}\n"
        f"Details: {details[:500]}"
    )
