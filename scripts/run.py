import json
import os
import sys

from llm_filter import classify_and_summarize
from fetch_post import fetch_latest_post
from telegram_notify import send_message

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "state.json")
PAGE_ID = os.environ.get("FB_PAGE_ID", "61587759043686")
PAGE_NAME = "達叔礙唬爛"


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"last_post_id": None, "last_post_hash": None}


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    state = load_state()

    post = fetch_latest_post(PAGE_ID)
    if post is None:
        print("No post found (page may be blocking access or has no public posts).")
        return

    if post["text_hash"] == state.get("last_post_hash"):
        print("No new post since last check.")
        return

    is_relevant, summary = classify_and_summarize(post["text"])
    print(f"post_id={post['id']} relevant={is_relevant}")

    if is_relevant:
        message = (
            f"📌 {PAGE_NAME} 新貼文重點（預覽摘要，完整內容請點連結）\n\n"
            f"{summary}\n\n"
            f"原文：{post['url']}"
        )
        send_message(message)
        print("Sent Telegram digest.")
    else:
        print("New post is not medical/treatment related, skipping notification.")

    state["last_post_id"] = post["id"]
    state["last_post_hash"] = post["text_hash"]
    save_state(state)


if __name__ == "__main__":
    sys.exit(main())
