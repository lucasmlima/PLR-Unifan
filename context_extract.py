from playwright.sync_api import sync_playwright
import time

STORAGE_STATE = 'state.json'

with sync_playwright() as pw:

    browser = pw.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://www.reddit.com/')
    time.sleep(20)

    context.storage_state(path=STORAGE_STATE)
    


