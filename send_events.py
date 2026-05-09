import os
import requests
from datetime import datetime, timedelta

LINE_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
GROUP_ID = os.environ["LINE_GROUP_ID"]

DOORKEEPER_URL = "https://api.doorkeeper.jp/events"


def get_tokyo_events():
    today = datetime.now()
    next_week = today + timedelta(days=7)

    params = {
        "locale": "ja",
        "sort": "starts_at",
        "per_page": 20,
        "page": 1,
        "q": "東京",
    }
    headers = {"Accept": "application/json"}

    resp = requests.get(DOORKEEPER_URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    events = []
    for item in data:
        e = item.get("event", {})
        starts_at = e.get("starts_at", "")
        if not starts_at:
            continue
        started_at = datetime.strptime(starts_at[:10], "%Y-%m-%d")
        if today <= started_at <= next_week:
            events.append({
                "title": e.get("title", "タイトルなし"),
                "date": started_at.strftime("%m/%d(%a)"),
                "url": e.get("public_url", ""),
                "place": e.get("venue_name") or "オンライン",
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
