import os

BS_USER = os.getenv('BROWSERSTACK_USERNAME') or os.getenv('BROWSERSTACK_USER')
BS_KEY = os.getenv('BROWSERSTACK_ACCESS_KEY') or os.getenv('BROWSERSTACK_KEY')

# BrowserStack Hub URL
BROWSERSTACK_HUB = "https://hub-cloud.browserstack.com/wd/hub"

# Presets для разных браузеров/платформ
BROWSERSTACK_PRESETS = {
    'chrome_latest_win': {
        'browserName': 'Chrome',
        'browserVersion': 'latest',
        'bstack:options': {
            'os': 'Windows',
            'osVersion': '11',
            'projectName': 'SQA Assignment 6 - DDT',
            'buildName': 'Data-Driven Tests',
            'sessionName': 'Chrome Win11 - Login/Signup Tests',
            'local': 'false',
            'seleniumVersion': '4.0.0',
            'video': 'true',  # Включаем видеозапись
            'networkLogs': 'true',  # Включаем сетевые логи
            'consoleLogs': 'verbose',  # Подробные консольные логи
            'debug': 'true'  # Debug режим
        }
    },
    'firefox_latest_win': {
        'browserName': 'Firefox',
        'browserVersion': 'latest',
        'bstack:options': {
            'os': 'Windows',
            'osVersion': '11',
            'projectName': 'SQA Assignment 6 - DDT',
            'buildName': 'Data-Driven Tests',
            'sessionName': 'Firefox Win11 - Login/Signup Tests',
            'local': 'false',
            'seleniumVersion': '4.0.0',
            'video': 'true',
            'networkLogs': 'true',
            'consoleLogs': 'verbose',
            'debug': 'true'
        }
    },
    'safari_latest_mac': {
        'browserName': 'Safari',
        'browserVersion': 'latest',
        'bstack:options': {
            'os': 'OS X',
            'osVersion': 'Sonoma',
            'projectName': 'SQA Assignment 6 - DDT',
            'buildName': 'Data-Driven Tests',
            'sessionName': 'Safari macOS - Login/Signup Tests',
            'local': 'false',
            'seleniumVersion': '4.0.0',
            'video': 'true',
            'networkLogs': 'true',
            'consoleLogs': 'verbose',
            'debug': 'true'
        }
    },
    'edge_latest_win': {
        'browserName': 'Edge',
        'browserVersion': 'latest',
        'bstack:options': {
            'os': 'Windows',
            'osVersion': '11',
            'projectName': 'SQA Assignment 6 - DDT',
            'buildName': 'Data-Driven Tests',
            'sessionName': 'Edge Win11 - Login/Signup Tests',
            'local': 'false',
            'seleniumVersion': '4.0.0',
            'video': 'true',
            'networkLogs': 'true',
            'consoleLogs': 'verbose',
            'debug': 'true'
        }
    }
}


def get_capabilities(preset_key: str, test_name: str = None) -> dict:
    """
    Получить capabilities для BrowserStack с кастомным именем теста
    """
    caps = BROWSERSTACK_PRESETS.get(preset_key, BROWSERSTACK_PRESETS['chrome_latest_win']).copy()

    # Обновляем имя сессии если передано
    if test_name and 'bstack:options' in caps:
        caps['bstack:options']['sessionName'] = test_name

    return caps