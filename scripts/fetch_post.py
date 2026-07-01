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


def _meta_content(page, prop):
    el = page.query_selector(f'meta[property="{prop}"]')
    return el.get_attribute("content") if el else None


def fetch_latest_post(page_id):
    profile_url = f"https://www.facebook.com/profile.php?id={page_id}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT, locale="zh-TW")
        page.goto(profile_url, timeout=30000)
        page.wait_for_timeout(4000)

        print(f"[fetch_post] profile page title={page.title()!r} url={page.url!r}")

        hrefs = page.eval_on_selector_all("a", "els => els.map(e => e.href)")
        permalinks = []
        for href in hrefs:
            if POST_LINK_PATTERN.search(href):
                cleaned = _clean_url(href)
                if cleaned not in permalinks:
                    permalinks.append(cleaned)

        print(f"[fetch_post] found {len(permalinks)} permalink(s)")

        if not permalinks:
            browser.close()
            return None

        post_url = permalinks[0]
        page.goto(post_url, timeout=30000)
        page.wait_for_timeout(3000)

        print(f"[fetch_post] post page title={page.title()!r} url={page.url!r}")

        description = _meta_content(page, "og:description")
        og_url = _meta_content(page, "og:url")

        if not description:
            body_snippet = page.inner_text("body")[:300]
            print(f"[fetch_post] no og:description found. body snippet: {body_snippet!r}")

        browser.close()

        if not description:
            return None

        return {
            "id": _extract_post_id(post_url),
            "url": og_url or post_url,
            "text": description.strip(),
        }


if __name__ == "__main__":
    import sys

    result = fetch_latest_post(sys.argv[1] if len(sys.argv) > 1 else "61587759043686")
    print(result)
