from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from database import (list_articles, get_article, list_sources, upsert_articles, get_recent_articles,
                      get_coins, set_coins, get_feeds, set_feeds, get_admin)
from rss import fetch_all
from grok import grok_chat
from auth import create_token, verify_admin, check_password

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


# ── Chatbot (Grok / xAI) ────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None

SYSTEM_PROMPT = (
    "You are the AI assistant for 'Crypto News', a cryptocurrency news aggregator. "
    "Help users understand crypto markets, projects, and the latest news. Be concise, "
    "accurate, and neutral — never give financial advice; add a brief risk caveat when "
    "users ask whether to buy/sell. Reply in the user's language.\n\n"
    "Below are the most recent headlines from the site for context. Use them when the user "
    "asks about current/latest news; otherwise answer from general crypto knowledge.\n"
)

@router.post("/api/crypto-news/chat")
async def chat(req: ChatRequest):
    recent = await get_recent_articles(30)
    context = "\n".join(
        f"- [{a.get('source','')}] {a.get('title','')} ({a.get('published','')}) — {a.get('summary','')}"
        for a in recent
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n=== LATEST HEADLINES ===\n" + context}]
    for m in (req.history or [])[-8:]:
        role = "assistant" if m.get("role") == "assistant" else "user"
        messages.append({"role": role, "content": m.get("content", "")})
    messages.append({"role": "user", "content": req.message})
    try:
        reply = await grok_chat(messages)
        return {"reply": reply}
    except Exception as e:
        print(f"[chat] error: {e}")
        return {"reply": "Sorry, the assistant is unavailable right now. Please try again."}


# ── Public: chart coins ─────────────────────────────────────────────────────────

@router.get("/api/crypto-news/coins")
async def coins():
    return await get_coins()


# ── Admin ───────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class CoinItem(BaseModel):
    label: str
    symbol: str

class FeedItem(BaseModel):
    name: str
    url: str

class CoinsUpdate(BaseModel):
    items: List[CoinItem]

class FeedsUpdate(BaseModel):
    items: List[FeedItem]

@router.post("/api/crypto-news/admin/login")
async def admin_login(req: LoginRequest):
    admin = await get_admin()
    if not admin or req.username != admin.get("username") or not check_password(req.password, admin.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"access_token": create_token(req.username), "token_type": "bearer"}

@router.get("/api/crypto-news/admin/coins")
async def admin_get_coins(_: str = Depends(verify_admin)):
    return await get_coins()

@router.put("/api/crypto-news/admin/coins")
async def admin_set_coins(data: CoinsUpdate, _: str = Depends(verify_admin)):
    await set_coins([c.model_dump() for c in data.items])
    return {"ok": True}

@router.get("/api/crypto-news/admin/feeds")
async def admin_get_feeds(_: str = Depends(verify_admin)):
    return await get_feeds()

@router.put("/api/crypto-news/admin/feeds")
async def admin_set_feeds(data: FeedsUpdate, _: str = Depends(verify_admin)):
    feeds = [f.model_dump() for f in data.items]
    await set_feeds(feeds)
    # fetch immediately with the new feed list
    items = await fetch_all(feeds)
    inserted = await upsert_articles(items)
    return {"ok": True, "fetched": len(items), "inserted": inserted}
