
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://bet500.bet", timeout=60000)
    print(page.title())
    print("Cookies:", context.cookies())
    print("Page status:", page.status if hasattr(page, 'status') else "unknown")

    # OPTIONAL: save page content or take a screenshot
    page.screenshot(path="bet500_homepage.png")
    with open("page.html", "w") as f:
        f.write(page.content())

    browser.close()
