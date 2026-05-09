import os
import requests
from datetime import datetime, timedelta, timezone

LINE_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
GROUP_ID = os.environ["LINE_GROUP_ID"]
EVENTBRITE_TOKEN = os.environ["EVENTBRITE_TOKEN"]

EVENTBRITE_URL = "https://www.eventbriteapi.com/v3/events/search/"

# グルメ・おでかけ・デート向けカテゴリ
# 110=Food & Drink, 105=Arts & Entertainment, 103=Music, 104=Film & Media
TARGET_CATEGORIES = "110,105,103,104"


def get_tokyo_events():
    today = datetime.now(timezone.utc)
    next_week = today + timedelta(days=7)

    params = {
        "token": EVENTBRITE_TOKEN,
        "location.address": "Tokyo, Japan",
        "location.within": "30km",
        "categories": TARGET_CATEGORIES,
        "start_date.range_start": today.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "start_date.range_end": next_week.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sort_by": "date",
        "expand": "venue",
        "page_size": 10,
    }

    resp = requests.get(EVENTBRITE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    events = []
    for e in data.get("events", []):
        start = e.get("start", {}).get("local", "")
        if not start:
            continue
        started_at = datetime.strptime(start[:10], "%Y-%m-%d")
        venue = e.get("venue") or {}
        place = venue.get("name") or venue.get("address", {}).get("city") or "東京"
        events.append({
            "title": e.get("name", {}).get("text", "タイトルなし"),
            "date": started_at.strftime("%m/%d(%a)"),
            "url": e.get("url", ""),
            "place": place,
        })

    return events[:5]


def build_message(events):
    today = datetime.now()
    lines = [f"🗓 今週の東京イベント情報 ({today.strftime('%m/%d')}週)"]
    lines.append("─" * 20)

    if not events:
        lines.append("今週は該当イベントが見つからへんかったわ。")
    else:
        for i, e in enumerate(events, 1):
            lines.append(f"\n【{i}】{e['title']}")
            lines.append(f"📅 {e['date']}  📍 {e['place']}")
            lines.append(f"🔗 {e['url']}")

    lines.append("\n─" * 20)
    lines.append("また来週もチェックするで！")
    return "\n".join(lines)


def send_line_message(text):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": GROUP_ID,
        "messages": [{"type": "text", "text": text}],
    }
    resp = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=payload,
        timeout=10,
    )
    resp.raise_for_status()
    print("送信完了やで！")


if __name__ == "__main__":
    events = get_tokyo_events()
    message = build_message(events)
    print(message)
    send_line_message(message)
