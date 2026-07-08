import json
import os
import sys

from llm_filter import classify_and_summarize
from fetch_post import fetch_latest_post
from telegram_notify import send_message

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "state.json")
PAGE_ID = os.environ.get("FB_PAGE_ID", "61587759043686")
PAGE_NAME = "達叔礙唬爛"

# Neither signal is stable on its own: Facebook's pfbid can change across
# scrapes for the same post (session-dependent), and the truncated preview
# text can also shift slightly between scrapes of the same post. Keeping a
# short history and matching on *either* id or hash means drift in one
# signal alone doesn't make an already-seen post look new.
HISTORY_SIZE = 15


def load_state():
    if not os.path.exists(STATE_PATH):
        return {"seen": []}

    with open(STATE_PATH, encoding="utf-8") as f:
        state = json.load(f)

    if "seen" not in state:
        # Migrate from the old single last_post_id/last_post_hash format.
        seen = []
        if state.get("last_post_id") or state.get("last_post_hash"):
            seen.append(
                {"id": state.get("last_post_id"), "hash": state.get("last_post_hash")}
            )
        state = {"seen": seen}

    return state


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def already_seen(post, seen):
    return any(
        entry.get("id") == post["id"] or entry.get("hash") == post["text_hash"]
        for entry in seen
    )


def main():
    state = load_state()
    seen = state["seen"]

    post = fetch_latest_post(PAGE_ID)
    if post is None:
        print("No post found (page may be blocking access or has no public posts).")
        return

    if already_seen(post, seen):
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

    seen.append({"id": post["id"], "hash": post["text_hash"]})
    state["seen"] = seen[-HISTORY_SIZE:]
    save_state(state)


if __name__ == "__main__":
    sys.exit(main())
