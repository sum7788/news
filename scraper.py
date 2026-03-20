"""
서울 정비사업 통합심의위원회 개최결과 뉴스 수집기
"""
import json, os, urllib.request, urllib.parse, re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

KST = timezone(timedelta(hours=9))
DATA_PATH = "data/news.json"
CLIENT_ID = os.environ["NAVER_CLIENT_ID"]
CLIENT_SECRET = os.environ["NAVER_CLIENT_SECRET"]

KEYWORDS = [
    "서울 통합심의",
    "정비사업 통합심의",
    "재개발 통합심의",
    "재건축 통합심의",
]

def load():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"updated": "", "items": []}

def save(data):
    os.makedirs("data", exist_ok=True)
    data["updated"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean(text):
    return re.sub(r"<[^>]+>", "", text).strip()

def parse_date(s):
    try:
        return parsedate_to_datetime(s).astimezone(KST).strftime("%Y-%m-%d")
    except:
        return s[:10] if s else ""

def search(keyword):
    url = "https://openapi.naver.com/v1/search/news.json?query=" + \
          urllib.parse.quote(keyword) + "&display=20&sort=date"
    req = urllib.request.Request(url, headers={
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"오류 ({keyword}): {e}")
        return {"items": []}

# 이 중 하나라도 포함되면 저장 (필터 완화)
FILTER_KEYWORDS = ["통합심의"]

def is_relevant(title, summary):
    text = title + " " + summary
    matched = [kw for kw in FILTER_KEYWORDS if kw in text]
    print(f"  → {'통과' if matched else '제외'} | {title[:50]}")
    return len(matched) >= 1

def main():
    data = load()
    existing = {it["url"] for it in data["items"]}
    added = []

    for kw in KEYWORDS:
        print(f"\n검색: {kw}")
        result = search(kw)
        items = result.get("items", [])
        print(f"  API 결과: {len(items)}건")

        for item in items:
            title = clean(item.get("title", ""))
            url = item.get("originallink") or item.get("link", "")
            summary = clean(item.get("description", ""))[:300]
            date = parse_date(item.get("pubDate", ""))

            if url in existing:
                print(f"  → 중복 건너뜀 | {title[:40]}")
                continue
            if not is_relevant(title, summary):
                continue

            data["items"].append({
                "title": title, "url": url,
                "summary": summary, "date": date,
                "source": "네이버뉴스",
                "collected_at": datetime.now(KST).strftime("%Y-%m-%d"),
            })
            existing.add(url)
            added.append(title)

    data["items"].sort(key=lambda x: x.get("date", ""), reverse=True)
    data["items"] = data["items"][:300]

    if added:
        print(f"\n신규 {len(added)}건:")
        for t in added[:10]:
            print(f"  · {t}")
    else:
        print("\n신규 없음")

    save(data)
    print(f"\n총 {len(data['items'])}건 저장")

if __name__ == "__main__":
    main()
