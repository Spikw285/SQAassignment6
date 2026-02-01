import os

BS_USER = os.getenv('BROWSERSTACK_USER') or os.getenv('BROWSERSTACK_USERNAME')
BS_KEY = os.getenv('BROWSERSTACK_KEY') or os.getenv('BROWSERSTACK_ACCESS_KEY')

BROWSERSTACK_PRESETS = {
    'chrome_latest_win': ('Chrome', 'latest', 'Windows', '11'),
    'firefox_latest_win': ('Firefox', 'latest', 'Windows', '11'),
    'safari_latest_mac': ('Safari', 'latest', 'macOS', 'Ventura'),
}