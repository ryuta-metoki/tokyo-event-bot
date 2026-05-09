import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

LINE_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
GROUP_ID = os.environ["LINE_GROUP_ID"]

# グルメ・デート系キーワードでPeatix検索（APIキー不要）
PEATIX_RSS_URLS = [
    "https://peatix.com/search/events/rss?tag=グルメ&country=JP&state=13",
    "https://peatix.com/search/events/rss?tag=食&country=JP&state=13",
    "https://peatix.com/search/events/rss?tag=マルシェ&country=JP&state=13",
    "https://peatix.com/search/events/rss?tag=フード&country=JP&state=13",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TokyoEventBot/1.0)"
}


def get_tokyo_events():
    today = datetime.now()
    next_week = today + timedelta(days=7)
    seen = set()
    events = []

    for url in PEATIX_RSS_URLS:
        if len(events) >= 5:
            break
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            for item in root.findall(".//item"):
                title_el = item.find("title")
                link_el = item.find("link")
                pubdate_el = item.find("pubDate")
                if title_el is None or link_el is None:
                    continue

                title = title_el.text or ""
                link = link_el.text or ""

                if link in seen:
                    continue
                seen.add(link)

                # 日付パース
                date_str = "今週"
                if pubdate_el is not None and pubdate_el.text:
                    try:
                        dt = parsedate_to_datetime(pubdate_el.text)
                        started_at = dt.replace(tzinfo=None)
                        if not (today - timedelta(days=1) <= started_at <= next_week):
                            continue
                        date_str = started_at.strftime("%m/%d(%a)")
                    except Exception:
                        pass

                events.append({
                    "title": title,
                    "date": date_str,
                    "url": link,
                    "place": "東京",
                })

                if len(events) >= 5:
                    break
        except Exception as e:
            print(f"RSS取得エラー: {e}")
            continue

    return events


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
