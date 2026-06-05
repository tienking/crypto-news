from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne, DESCENDING
from config import MONGODB_URL, ADMIN_USERNAME, ADMIN_PASSWORD, AI_PROVIDER, GROK_MODEL, GEMINI_MODEL
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
    await articles_col.create_index([("published", DESCENDING)])
    await articles_col.create_index("source")


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
    return d["list"] if d else DEFAULT_FEEDS

async def set_feeds(items: list[dict]):
    await settings_col.update_one({"type": "feeds"}, {"$set": {"list": items}}, upsert=True)

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
    query = {}
    if source:
        query["source"] = source
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"summary": {"$regex": q, "$options": "i"}},
        ]
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
    return sorted(await articles_col.distinct("source"))


async def get_recent_articles(limit: int = 30):
    """Lightweight recent headlines for the chatbot context."""
    cursor = (articles_col.find({}, {"_id": 0, "title": 1, "source": 1, "summary": 1, "published": 1})
              .sort("published", DESCENDING)
              .limit(limit))
    items = await cursor.to_list(length=limit)
    for it in items:
        if isinstance(it.get("published"), datetime):
            it["published"] = it["published"].strftime("%Y-%m-%d %H:%M UTC")
    return items
