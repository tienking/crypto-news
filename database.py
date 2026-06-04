from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne, DESCENDING
from config import MONGODB_URL
from datetime import datetime, timezone

client = AsyncIOMotorClient(MONGODB_URL)
db = client["cryptonews"]
articles_col = db["articles"]


async def ensure_indexes():
    await articles_col.create_index("guid", unique=True)
    await articles_col.create_index([("published", DESCENDING)])
    await articles_col.create_index("source")


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
