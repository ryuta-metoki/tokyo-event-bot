import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

LINE_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
GROUP_ID = os.environ["LINE_GROUP_ID"]

RSS_URL = "https://event-checker.info/feed/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TokyoEventBot/1.0)"}


def get_tokyo_events():
    resp = requests.get(RSS_URL, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    events = []
    for item in root.findall(".//item")[:10]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate") or ""

        date_str = "今週"
        if pub:
            try:
                dt = parsedate_to_datetime(pub).replace(tzinfo=None)
                date_str = dt.strftime("%m/%d公開")
            except Exception:
                pass

        events.append({"title": title, "url": link, "date": date_str})

    return events[:5]


def build_message(events):
    today = datetime.now()
    lines = [f"🗓 今週の東京グルメ＆おでかけ情報 ({today.strftime('%m/%d')}週)"]
    lines.append("─" * 20)

    if not events:
        lines.append("今週は情報が取得できへんかったわ。")
    else:
        for i, e in enumerate(events, 1):
            lines.append(f"\n【{i}】{e['title']}")
            lines.append(f"🔗 {e['url']}")

    lines.append("\n─" * 20)
    lines.append("詳細はリンクから確認してな！")
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
