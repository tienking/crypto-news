"""RSS fetching + parsing for crypto news sources."""
import re
import calendar
from datetime import datetime, timezone
import httpx
import feedparser

# Default crypto news feeds — seeded into MongoDB on first run, then editable via Admin.
DEFAULT_FEEDS = [
    {"name": "CoinDesk",      "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
    {"name": "Decrypt",       "url": "https://decrypt.co/feed"},
    {"name": "CryptoSlate",   "url": "https://cryptoslate.com/feed/"},
    {"name": "BeInCrypto",    "url": "https://beincrypto.com/feed/"},
    {"name": "CoinJournal",   "url": "https://coinjournal.net/feed/"},
    {"name": "U.Today",       "url": "https://u.today/rss"},
    {"name": "AMBCrypto",     "url": "https://ambcrypto.com/feed/"},
    {"name": "CryptoNews",    "url": "https://cryptonews.com/news/feed/"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)


def _strip_html(html: str) -> str:
    text = _TAG_RE.sub(" ", html or "")
    return _WS_RE.sub(" ", text).strip()


def _content(entry) -> str:
    if entry.get("content"):
        return entry["content"][0].get("value", "") or ""
    return entry.get("summary", "") or ""


def _image(entry) -> str | None:
    for m in entry.get("media_content", []) or []:
        if m.get("url"):
            return m["url"]
    for m in entry.get("media_thumbnail", []) or []:
        if m.get("url"):
            return m["url"]
    for enc in entry.get("enclosures", []) or []:
        if (enc.get("type") or "").startswith("image") and enc.get("href"):
            return enc["href"]
    match = _IMG_RE.search(_content(entry))
    return match.group(1) if match else None


def _published(entry) -> datetime:
    p = entry.get("published_parsed") or entry.get("updated_parsed")
    if p:
        return datetime.fromtimestamp(calendar.timegm(p), tz=timezone.utc)
    return datetime.now(timezone.utc)


def _to_article(entry, source: str) -> dict | None:
    guid = entry.get("id") or entry.get("link")
    title = (entry.get("title") or "").strip()
    if not guid or not title:
        return None
    summary = _strip_html(entry.get("summary", ""))
    if len(summary) > 400:
        summary = summary[:400].rsplit(" ", 1)[0] + "…"
    return {
        "guid": guid,
        "title": title,
        "link": entry.get("link", ""),
        "summary": summary,
        "content": _content(entry),
        "source": source,
        "author": entry.get("author", ""),
        "image": _image(entry),
        "published": _published(entry),
    }


async def fetch_feed(feed: dict) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=15, headers=HEADERS, follow_redirects=True) as client:
            r = await client.get(feed["url"])
            r.raise_for_status()
        parsed = feedparser.parse(r.content)
        out = []
        for e in parsed.entries:
            a = _to_article(e, feed["name"])
            if a:
                out.append(a)
        return out
    except Exception as e:
        print(f"[rss] {feed['name']} failed: {e}")
        return []


async def fetch_all(feeds: list[dict] | None = None) -> list[dict]:
    import asyncio
    feeds = feeds or DEFAULT_FEEDS
    results = await asyncio.gather(*(fetch_feed(f) for f in feeds))
    return [a for batch in results for a in batch]
