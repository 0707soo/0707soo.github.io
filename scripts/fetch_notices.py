#!/usr/bin/env python3
import json
import html
import re
from pathlib import Path
from urllib.parse import urljoin

import requests

SOURCE_URL = "https://mabinogi.nexon.com/page/news/notice_list.asp"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "notices.json"
BASE_URL = "https://mabinogi.nexon.com/page/news/"


def clean_text(value: str) -> str:
    value = re.sub(r"<img[^>]*>", "", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def fetch_notice_html() -> str:
    response = requests.get(SOURCE_URL, timeout=20)
    response.raise_for_status()
    response.encoding = "euc-kr"
    return response.text


def parse_notices(markup: str):
    pattern = re.compile(
        r'<a[^>]+href="(?P<href>(?:/page/news/)?notice_view\.asp\?id=(?P<id>\d+))"[^>]*>(?P<title>.*?)</a>.*?<span[^>]*class="date"[^>]*>(?P<date>\d{4}\.\d{2}\.\d{2})</span>',
        re.I | re.S,
    )
    notices = []
    seen = set()
    for match in pattern.finditer(markup):
        notice_id = match.group("id")
        title = clean_text(match.group("title"))
        if not title or notice_id in seen:
            continue
        seen.add(notice_id)
        notices.append(
            {
                "id": notice_id,
                "title": title,
                "date": match.group("date"),
                "url": urljoin(BASE_URL, match.group("href")),
            }
        )
    return notices


def main():
    markup = fetch_notice_html()
    notices = parse_notices(markup)[:8]
    payload = {"source": SOURCE_URL, "count": len(notices), "items": notices}
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(notices)} notices to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
