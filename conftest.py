"""
Pytest configuration file - должен быть в корне проекта!
"""
import pytest
import sys
from pathlib import Path

# Правильный импорт для pytest-html
try:
    from pytest_html import extras
    PYTEST_HTML_AVAILABLE = True
except ImportError:
    PYTEST_HTML_AVAILABLE = False
    print("WARNING: pytest-html not installed. Install it: pip install pytest-html")
# Добавляем корень проекта в sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
from utils.driver_factory import create_local_driver
from utils.actions import prepare_clean_session

logger = get_logger("pytest_runner")

# ============================================================================
# PYTEST OPTIONS
# ============================================================================
def pytest_addoption(parser):
    """Добавляем custom опции для pytest"""
    parser.addoption(
        "--data-file",
        action="store",
        default="sample_test_data.xlsx",
        help="Path to Excel test data file"
    )
    parser.addoption(
        "--sheet",
        action="store",
        default=None,
        help="Specific sheet to test (e.g., 'login', 'signup')"
    )
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        help="Browser to use (chrome, firefox, edge)"
    )

# ============================================================================
# FIXTURES
# ============================================================================
@pytest.fixture(scope="function")
def browser(request):
    """Fixture для создания браузера"""
    browser_name = request.config.getoption("--browser")
    logger.info(f"Creating browser: {browser_name}")
    driver = create_local_driver(browser_name)
    prepare_clean_session(driver, logger)
    yield driver
    try:
        driver.quit()
    except Exception as e:
        logger.warning(f"Failed to quit driver: {e}")

# ============================================================================
# HTML REPORT CUSTOMIZATION (только если pytest-html установлен)
# ============================================================================
def pytest_configure(config):
    """Настройки для pytest-html"""
    if PYTEST_HTML_AVAILABLE:
        config._metadata = {
            'Project': 'SQA Assignment 6 - Data-Driven Testing',
            'Tester': 'Timur',
            'Environment': 'Local/Chrome',
            'Python': '3.x',
            'Framework': 'Selenium + Pytest',
            'Test Data': config.getoption("--data-file", default="sample_test_data.xlsx")
        }

@pytest.hookimpl(optionalhook=True)
def pytest_html_report_title(report):
    """Кастомный заголовок отчёта"""
    if PYTEST_HTML_AVAILABLE:
        report.title = "Data-Driven Test Report - Assignment 6"

def pytest_html_results_table_header(cells):
    """Кастомизация заголовков таблицы"""
    if not PYTEST_HTML_AVAILABLE:
        return

    cells.insert(2, '<th class="sortable" data-column-type="test_id">Test ID</th>')
    cells.insert(3, '<th class="sortable" data-column-type="expected">Expected</th>')
    cells.insert(4, '<th class="sortable" data-column-type="actual">Actual</th>')

def pytest_html_results_table_row(report, cells):
    """Добавление кастомных колонок в таблицу результатов"""
    if not PYTEST_HTML_AVAILABLE:
        return

    try:
        # Извлекаем test_id из имени теста
        test_name = report.nodeid
        # Формат: test_flow[login_L-01] -> извлекаем L-01
        if "[" in test_name and "]" in test_name:
            param = test_name.split("[")[1].split("]")[0]
            sheet_test = param.split("_")
            if len(sheet_test) >= 2:
                test_id = sheet_test[1]
            else:
                test_id = param
        else:
            test_id = "N/A"

        # Пытаемся получить expected и actual из report
        expected = getattr(report, 'expected', 'N/A')
        actual = getattr(report, 'actual', 'N/A')

        cells.insert(2, f'<td class="col-test_id">{test_id}</td>')
        cells.insert(3, f'<td class="col-expected">{expected}</td>')
        cells.insert(4, f'<td class="col-actual">{actual}</td>')
    except Exception as e:
        logger.error(f"Error customizing table row: {e}")
        cells.insert(2, '<td class="col-test_id">N/A</td>')
        cells.insert(3, '<td class="col-expected">N/A</td>')
        cells.insert(4, '<td class="col-actual">N/A</td>')

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Добавляем скриншоты и детали в HTML отчёт"""
    outcome = yield
    report = outcome.get_result()

    if not PYTEST_HTML_AVAILABLE or report.when != "call":
        return

    extra = getattr(report, 'extra', [])

    # Пытаемся получить test_case из funcargs
    test_case = item.funcargs.get('test_case')
    if test_case:
        sheet_name, row = test_case
        test_id = row.get('test_id', 'UNKNOWN')

        # Сохраняем expected и actual для таблицы
        report.expected = row.get('expected_result', 'N/A')

        # Добавляем скриншоты
        screenshots_dir = Path("logs/screenshots")
        if screenshots_dir.exists():
            screenshots = sorted(list(screenshots_dir.glob(f"{test_id}*.png")))
            for screenshot in screenshots[-3:]:  # Последние 3 скриншота
                try:
                    # Конвертируем путь в относительный для HTML
                    rel_path = screenshot.relative_to(Path.cwd())
                    extra.append(extras.image(str(rel_path)))
                except Exception as e:
                    logger.warning(f"Failed to add screenshot {screenshot}: {e}")

        # Добавляем детали результата
        if hasattr(item, 'test_result'):
            result = item.test_result
            details = result.get('details', '')
            if details:
                # Экранируем HTML символы
                details_escaped = details.replace('<', '&lt;').replace('>', '&gt;')
                details_html = f"""
                <div style='background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-top: 10px;'>
                    <h4>Test Details:</h4>
                    <pre style='white-space: pre-wrap; word-wrap: break-word;'>{details_escaped}</pre>
                </div>
                """
                extra.append(extras.html(details_html))

            # Сохраняем actual для таблицы
            report.actual = result.get('actual', 'N/A')

    report.extra = extra