
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-gpu"
        ]
    )
    context = browser.new_context()
    page = context.new_page()

    # Spoof navigator.webdriver to avoid bot detection
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    page.goto("https://bet500.bet", timeout=60000)
    print("Page Title:", page.title())
    print("Cookies:", context.cookies())

    # Save results
    page.screenshot(path="bet500_homepage_stealth.png")
    with open("page_stealth.html", "w") as f:
        f.write(page.content())

    browser.close()
