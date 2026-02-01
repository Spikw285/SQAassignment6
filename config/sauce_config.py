import os

SAUCE_USER= os.getenv('SAUCE_USERNAME')
SAUCE_KEY= os.getenv('SAUCE_ACCESS_KEY')

SAUCE_PRESETS = {
    'chrome_latest_win': ('chrome', 'latest', 'Windows 11'),
    'firefox_latest_win': ('firefox', 'latest', 'Windows 11'),
    'safari_latest_mac': ('safari', 'latest', 'macOS 14'),
}