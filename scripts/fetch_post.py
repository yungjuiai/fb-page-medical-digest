import os
import re

from firecrawl import Firecrawl

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


def fetch_latest_post(page_id, api_key=None):
    client = Firecrawl(api_key=api_key or os.environ["FIRECRAWL_API_KEY"])
    profile_url = f"https://www.facebook.com/profile.php?id={page_id}"

    profile_doc = client.scrape(
        profile_url,
        formats=["links"],
        wait_for=4000,
        headers={"Accept-Language": "zh-TW,zh;q=0.9"},
    )

    permalinks = []
    for href in profile_doc.links or []:
        if POST_LINK_PATTERN.search(href):
            cleaned = _clean_url(href)
            if cleaned not in permalinks:
                permalinks.append(cleaned)

    if not permalinks:
        return None

    post_url = permalinks[0]
    post_doc = client.scrape(
        post_url,
        formats=["markdown"],
        wait_for=3000,
        headers={"Accept-Language": "zh-TW,zh;q=0.9"},
    )

    metadata = post_doc.metadata
    description = getattr(metadata, "og_description", None) if metadata else None
    canonical_url = getattr(metadata, "og_url", None) if metadata else None

    if not description:
        return None

    return {
        "id": _extract_post_id(post_url),
        "url": canonical_url or post_url,
        "text": description.strip(),
    }


if __name__ == "__main__":
    import sys

    result = fetch_latest_post(sys.argv[1] if len(sys.argv) > 1 else "61587759043686")
    print(result)
