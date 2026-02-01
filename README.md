# SQA Assignment 6 — Automated UI Tests for demoblaze.com

## Overview
This project contains a data-driven Selenium test suite for the demo e-commerce site `https://www.demoblaze.com`. Tests are written in Python and use `selenium`, `pandas` and `openpyxl` to read test cases from an Excel file. Tests are modular and include flows for **login**, **signup**, **contact**, **add_to_cart** and **purchase**.

This README explains setup, run instructions (local and BrowserStack), how to interpret results, known issues and mitigations.

## Repository structure
```
SQAassignment6/
├── .gitignore
├── config/
│   └── browserstack_config.py
├── conftest.py
├── README.md
├── requirements.txt
├── tests/
│   ├── flows/
│   │   ├── add_to_cart_flow.py
│   │   ├── contact_flow.py
│   │   ├── login_flow.py
│   │   ├── purchase_flow.py
│   │   └── signup_flow.py
│   ├── runner.py
│   └── test_runner_pytest.py
└── utils/
    ├── actions.py
    ├── driver_factory.py
    ├── excel_reader.py
    ├── logger.py
    └── popups.py
```
## Requirements & virtual environment
```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

For convenience locally create a .env (do not commit it):

BROWSERSTACK_USER=your_user_here
BROWSERSTACK_KEY=your_key_here

Load it at runtime with python-dotenv:

from dotenv import load_dotenv
load_dotenv()


In CI, add those values as secure secrets instead.
## How to run tests locally
Ensure sample_test_data.xlsx is present in repo root.

Example: run login sheet locally in Chrome:
```bash
python tests/runner.py --mode local --browser chrome --sheet login --data sample_test_data.xlsx
```

Artifacts (logs, screenshots) are written under logs/. If your runner writes a pytest-html file, it will be under reports/.

## How to run tests on BrowserStack
Set environment variables (or .env):
```bash
export BROWSERSTACK_USER=...
export BROWSERSTACK_KEY=...
```

Run:
```bash
python tests/runner.py --mode browserstack --preset chrome_latest_win --sheet login --data sample_test_data.xlsx
```

Use BrowserStack Dashboard to see session videos, console logs and screenshots — extremely helpful for debugging UI and modal/overlay issues.

## Test data strategy

- sample_test_data.xlsx contains sheets named login, signup, contact, purchase, add_to_cart. Each row includes test_id, inputs and expected_result.

- For signup tests, use randomized usernames (e.g. user_{timestamp}_{random}) to avoid false failures due to already-existing accounts.

## Known issues observed & mitigations

1. Popup/modal detection flakiness

   - Symptoms: test code fails to detect a popup or misinterprets the login modal template as an error popup.

   - Mitigations in code:

     - utils/popups.py central detector searching for native alert(), .sweet-alert, .modal.show, and inline alert selectors.

     - Heuristic in login_flow.py treats unchanged login modal body (words like "Username", "Password", "Log in") as template, not an error, and performs extended wait for either #logout2 or a real popup.

     - `click_with_fallback` (regular click, ActionChains, JS click) used to overcome overlay/backdrop issues.

     - Screenshots and a short page-source snippet are saved when an ambiguous state occurs.

2. `prepare_clean_session` localStorage error

   - Symptom: attempted driver.execute_script("localStorage...") throws Storage is disabled inside 'data:' URLs.

   - Mitigation: the helper is wrapped in try/except; failure is logged but test continues. Recommended improvement: detect data: URLs and skip localStorage clearing (or navigate to about:blank/home page before clearing).

3. Animation / overlay timing

- Use WebDriverWait not sleep; add a tiny delay (0.1–0.3s) after modal show to allow animations to finish; disable animations locally for debugging if necessary.

## Interpreting results

- Each flow returns a dict: {id, expected, actual, status, details}; runner aggregates them and writes logs/screenshots.

- For cloud runs, use BrowserStack video/snapshot playback for UI debugging.
