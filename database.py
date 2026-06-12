from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne, DESCENDING, ASCENDING
from config import (MONGODB_URL, ADMIN_USERNAME, ADMIN_PASSWORD, AI_PROVIDER,
                    GROK_MODEL, GEMINI_MODEL, ARTICLE_TTL_DAYS)
from rss import DEFAULT_FEEDS
from datetime import datetime, timezone

client = AsyncIOMotorClient(MONGODB_URL)
db = client["cryptonews"]
articles_col = db["articles"]
settings_col = db["settings"]

DEFAULT_COINS = [
    {"label": "BTCUSDT", "symbol": "MEXC:BTCUSDT"},
    {"label": "ETHUSDT", "symbol": "MEXC:ETHUSDT"},
    {"label": "SOLUSDT", "symbol": "MEXC:SOLUSDT"},
    {"label": "TAOUSDT", "symbol": "MEXC:TAOUSDT"},
    {"label": "XRPUSDT", "symbol": "MEXC:XRPUSDT"},
    {"label": "LTCUSDT", "symbol": "MEXC:LTCUSDT"},
]


async def ensure_indexes():
    await articles_col.create_index("guid", unique=True)
    await articles_col.create_index("source")
    # TTL index: MongoDB auto-deletes articles older than ARTICLE_TTL_DAYS.
    # A {published: 1} index also serves the descending sort (scanned backwards).
    await _ensure_ttl_index()


async def _ensure_ttl_index():
    name = "published_ttl"
    ttl_seconds = ARTICLE_TTL_DAYS * 86400
    info = await articles_col.index_information()
    # Drop the old non-TTL sort index if it exists (now redundant).
    if "published_-1" in info:
        await articles_col.drop_index("published_-1")
    existing = info.get(name)
    if existing and existing.get("expireAfterSeconds") != ttl_seconds:
        await articles_col.drop_index(name)  # TTL value changed → recreate
        existing = None
    if not existing:
        await articles_col.create_index([("published", ASCENDING)], name=name, expireAfterSeconds=ttl_seconds)


# ── Settings: coins / feeds / admin (seeded on first run) ──────────────────────

DEFAULT_AI = {"provider": AI_PROVIDER, "grok_model": GROK_MODEL, "gemini_model": GEMINI_MODEL}


async def seed_defaults():
    from auth import hash_password
    if not await settings_col.find_one({"type": "coins"}):
        await settings_col.update_one({"type": "coins"}, {"$set": {"list": DEFAULT_COINS}}, upsert=True)
    if not await settings_col.find_one({"type": "feeds"}):
        await settings_col.update_one({"type": "feeds"}, {"$set": {"list": DEFAULT_FEEDS}}, upsert=True)
    if not await settings_col.find_one({"type": "ai"}):
        await settings_col.update_one({"type": "ai"}, {"$set": DEFAULT_AI}, upsert=True)
    if not await settings_col.find_one({"type": "admin"}):
        await settings_col.update_one(
            {"type": "admin"},
            {"$set": {"username": ADMIN_USERNAME, "hashed_password": hash_password(ADMIN_PASSWORD)}},
            upsert=True,
        )


async def get_coins():
    d = await settings_col.find_one({"type": "coins"}, {"_id": 0})
    return d["list"] if d else DEFAULT_COINS

async def set_coins(items: list[dict]):
    await settings_col.update_one({"type": "coins"}, {"$set": {"list": items}}, upsert=True)

async def get_feeds():
    d = await settings_col.find_one({"type": "feeds"}, {"_id": 0})
    items = d["list"] if d else DEFAULT_FEEDS
    # legacy items without `enabled` default to enabled
    return [{"name": f.get("name", ""), "url": f.get("url", ""), "enabled": f.get("enabled", True)} for f in items]

async def set_feeds(items: list[dict]):
    await settings_col.update_one({"type": "feeds"}, {"$set": {"list": items}}, upsert=True)

async def get_enabled_feeds():
    return [f for f in await get_feeds() if f.get("enabled", True)]

async def get_disabled_sources():
    return [f["name"] for f in await get_feeds() if not f.get("enabled", True)]

async def get_admin():
    return await settings_col.find_one({"type": "admin"}, {"_id": 0})

async def get_ai_settings():
    d = await settings_col.find_one({"type": "ai"}, {"_id": 0})
    if not d:
        return DEFAULT_AI
    return {
        "provider": d.get("provider", "grok"),
        "grok_model": d.get("grok_model", GROK_MODEL),
        "gemini_model": d.get("gemini_model", GEMINI_MODEL),
    }

async def set_ai_settings(data: dict):
    await settings_col.update_one({"type": "ai"}, {"$set": data}, upsert=True)


async def upsert_articles(items: list[dict]) -> int:
    """Insert new articles, skip existing (dedup by guid). Returns inserted count."""
    if not items:
        return 0
    ops = []
    now = datetime.now(timezone.utc)
    for a in items:
        ops.append(UpdateOne(
            {"guid": a["guid"]},
            {"$setOnInsert": {**a, "fetched_at": now}},
            upsert=True,
        ))
    res = await articles_col.bulk_write(ops, ordered=False)
    return res.upserted_count


async def list_articles(page: int = 1, limit: int = 24, source: str | None = None, q: str | None = None):
    disabled = await get_disabled_sources()
    conds = []
    if source:
        conds.append({"source": source})
    if disabled:
        conds.append({"source": {"$nin": disabled}})
    if q:
        conds.append({"$or": [
            {"title": {"$regex": q, "$options": "i"}},
            {"summary": {"$regex": q, "$options": "i"}},
        ]})
    query = {"$and": conds} if conds else {}
    total = await articles_col.count_documents(query)
    cursor = (articles_col.find(query, {"content": 0})
              .sort("published", DESCENDING)
              .skip((page - 1) * limit)
              .limit(limit))
    items = await cursor.to_list(length=limit)
    for it in items:
        it["id"] = str(it.pop("_id"))
        if isinstance(it.get("published"), datetime):
            it["published"] = it["published"].isoformat()
    return {"items": items, "total": total, "page": page, "limit": limit}


async def get_article(article_id: str):
    from bson import ObjectId
    try:
        doc = await articles_col.find_one({"_id": ObjectId(article_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    if isinstance(doc.get("published"), datetime):
        doc["published"] = doc["published"].isoformat()
    return doc


async def list_sources():
    disabled = set(await get_disabled_sources())
    srcs = await articles_col.distinct("source")
    return sorted(s for s in srcs if s not in disabled)


async def get_recent_articles(limit: int = 30):
    """Lightweight recent headlines for the chatbot context (excludes disabled sources)."""
    disabled = await get_disabled_sources()
    query = {"source": {"$nin": disabled}} if disabled else {}
    cursor = (articles_col.find(query, {"_id": 0, "title": 1, "source": 1, "summary": 1, "published": 1})
              .sort("published", DESCENDING)
              .limit(limit))
    items = await cursor.to_list(length=limit)
    for it in items:
        if isinstance(it.get("published"), datetime):
            it["published"] = it["published"].strftime("%Y-%m-%d %H:%M UTC")
    return items
