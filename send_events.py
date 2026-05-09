import os
import requests
from datetime import datetime, timedelta

LINE_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
GROUP_ID = os.environ["LINE_GROUP_ID"]

CONNPASS_URL = "https://connpass.com/api/v1/event/"


def get_tokyo_events():
    today = datetime.now()
    next_week = today + timedelta(days=7)

    params = {
        "prefecture": "tokyo",
        "count": 10,
        "order": 2,
        "ym": today.strftime("%Y%m"),
    }

    resp = requests.get(CONNPASS_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    events = []
    for e in data.get("events", []):
        started_at = datetime.strptime(e["started_at"][:10], "%Y-%m-%d")
        if today <= started_at <= next_week:
            events.append({
                "title": e["title"],
                "date": started_at.strftime("%m/%d(%a)"),
                "url": e["event_url"],
                "place": e.get("place") or "オンライン",
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
