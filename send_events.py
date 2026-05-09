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
    for item in root.findall(".//item")[:20]:
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

    return events[:15]


def build_messages(events):
    today = datetime.now()
    messages = []

    # 1通目：ヘッダー
    header = (
        f"🗓 今週の東京グルメ＆おでかけ情報\n"
        f"({today.strftime('%m/%d')}週）全{len(events)}件\n"
        f"{'─' * 20}"
    )
    messages.append(header)

    # 3件ずつに分割して送信
    chunk_size = 3
    for chunk_start in range(0, len(events), chunk_size):
        chunk = events[chunk_start:chunk_start + chunk_size]
        lines = []
        for i, e in enumerate(chunk, chunk_start + 1):
            lines.append(f"【{i}】{e['title']}")
            lines.append(f"🔗 {e['url']}")
            lines.append("")
        messages.append("\n".join(lines).strip())

    # 最後にフッター
    messages.append("詳細はリンクから確認してな！")
    return messages


def send_line_messages(texts):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json",
    }
    # LINEは1回のAPIで最大5メッセージまで送れる
    chunk_size = 5
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i + chunk_size]
        payload = {
            "to": GROUP_ID,
            "messages": [{"type": "text", "text": t} for t in chunk],
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
    if not events:
        print("イベントが取得できへんかったわ")
    else:
        messages = build_messages(events)
        for m in messages:
            print(m)
            print("---")
        send_line_messages(messages)
