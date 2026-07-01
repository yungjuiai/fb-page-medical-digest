import re
from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)

POST_LINK_PATTERN = re.compile(r"story_fbid=|/posts/(pfbid|\d)")


def _clean_url(url):
    return url.split("&__cft__")[0].split("&__tn__")[0]


def _extract_post_id(url):
    match = re.search(r"story_fbid=(pfbid[0-9A-Za-z]+|\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/posts/(pfbid[0-9A-Za-z]+|\d+)", url)
    if match:
        return match.group(1)
    return url


def _clean_preview_text(text):
    text = text.replace("查看更多", "")
    text = re.sub(r"\s*\n\s*", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def fetch_latest_post(page_id):
    """Reads the currently visible latest post from the logged-out profile page.

    Facebook forces a login wall on the individual post permalink page, so this
    only captures the truncated preview text shown on the profile feed itself
    (cut off at "查看更多"), not the full post body. The permalink is still
    included so a logged-in human can tap through to read the rest.
    """
    profile_url = f"https://www.facebook.com/profile.php?id={page_id}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT, locale="zh-TW")
        page.goto(profile_url, timeout=30000)
        page.wait_for_timeout(4000)

        hrefs = page.eval_on_selector_all("a", "els => els.map(e => e.href)")
        permalinks = []
        for href in hrefs:
            if POST_LINK_PATTERN.search(href):
                cleaned = _clean_url(href)
                if cleaned not in permalinks:
                    permalinks.append(cleaned)

        message_el = page.query_selector('[data-ad-preview="message"]')
        preview_text = message_el.inner_text() if message_el else None

        browser.close()

        if not permalinks or not preview_text:
            return None

        return {
            "id": _extract_post_id(permalinks[0]),
            "url": permalinks[0],
            "text": _clean_preview_text(preview_text),
        }


if __name__ == "__main__":
    import sys

    result = fetch_latest_post(sys.argv[1] if len(sys.argv) > 1 else "61587759043686")
    print(result)
