from fastapi import APIRouter, Query, HTTPException
from database import list_articles, get_article, list_sources, upsert_articles
from rss import fetch_all

router = APIRouter()


@router.get("/api/crypto-news/health")
async def health():
    return {"status": "ok", "service": "crypto-news"}

@router.get("/api/crypto-news/articles")
async def articles(
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=60),
    source: str | None = None,
    q: str | None = None,
):
    return await list_articles(page=page, limit=limit, source=source, q=q)

@router.get("/api/crypto-news/article/{article_id}")
async def article(article_id: str):
    doc = await get_article(article_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Article not found")
    return doc

@router.get("/api/crypto-news/sources")
async def sources():
    return await list_sources()

@router.post("/api/crypto-news/refresh")
async def refresh():
    """Manually trigger an RSS refresh."""
    items = await fetch_all()
    inserted = await upsert_articles(items)
    return {"fetched": len(items), "inserted": inserted}
