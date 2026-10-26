from fastapi import APIRouter, Query, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Dict, Optional
import time
from database import (list_articles, get_article, list_sources, upsert_articles, get_recent_articles,
                      get_coins, set_coins, get_feeds, set_feeds, get_admin, set_admin_password,
                      get_ai_settings, set_ai_settings)
from rss import fetch_all
from ai import ai_chat
from auth import create_token, verify_admin, check_password, hash_password

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
    system = SYSTEM_PROMPT + "\n=== LATEST HEADLINES ===\n" + context
    conversation = [
        {"role": ("assistant" if m.get("role") == "assistant" else "user"), "content": m.get("content", "")}
        for m in (req.history or [])[-8:]
    ]
    conversation.append({"role": "user", "content": req.message})
    try:
        reply, provider = await ai_chat(system, conversation)
        return {"reply": reply, "provider": provider}
    except Exception as e:
        print(f"[chat] error: {e}")
        return {"reply": "Sorry, the assistant is unavailable right now. Please try again.", "provider": None}


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
    enabled: bool = True

class CoinsUpdate(BaseModel):
    items: List[CoinItem]

class FeedsUpdate(BaseModel):
    items: List[FeedItem]

# Login rate limiting (in-memory, per client IP, resets on restart).
_login_attempts: dict = {}  # ip -> {"count": int, "locked_until": float}
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 300  # 5 minutes

def _client_ip(request: Request) -> str:
    # Behind nginx the socket peer is always 127.0.0.1; nginx overwrites X-Real-IP
    # with the real $remote_addr, so it can't be spoofed by the client.
    host = request.client.host if request.client else ""
    if host in ("127.0.0.1", "::1"):
        return request.headers.get("x-real-ip") or host
    return host

def _check_login_rate(ip: str):
    entry = _login_attempts.get(ip)
    if entry and entry["locked_until"] > time.time():
        mins, secs = divmod(int(entry["locked_until"] - time.time()), 60)
        raise HTTPException(status_code=429, detail=f"Too many failed attempts. Try again in {mins}m {secs}s.")

def _record_login_failure(ip: str):
    now = time.time()
    if len(_login_attempts) > 10000:  # drop stale entries so the dict can't grow unbounded
        for k in [k for k, v in _login_attempts.items() if v["locked_until"] < now]:
            _login_attempts.pop(k, None)
    entry = _login_attempts.get(ip)
    if not entry or (entry["locked_until"] and entry["locked_until"] <= now):
        entry = {"count": 0, "locked_until": 0.0}  # fresh window after a lockout expires
    entry["count"] += 1
    if entry["count"] >= _MAX_ATTEMPTS:
        entry["locked_until"] = now + _LOCKOUT_SECONDS
    _login_attempts[ip] = entry

@router.post("/api/crypto-news/admin/login")
async def admin_login(req: LoginRequest, request: Request):
    ip = _client_ip(request)
    _check_login_rate(ip)
    admin = await get_admin()
    if not admin or req.username != admin.get("username") or not check_password(req.password, admin.get("hashed_password", "")):
        _record_login_failure(ip)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    _login_attempts.pop(ip, None)
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
    # fetch immediately with the enabled feeds only
    enabled = [f for f in feeds if f.get("enabled", True)]
    items = await fetch_all(enabled)
    inserted = await upsert_articles(items)
    return {"ok": True, "fetched": len(items), "inserted": inserted}


class AISettingsUpdate(BaseModel):
    provider: str                # "grok" | "gemini"
    grok_model: str
    gemini_model: str

@router.get("/api/crypto-news/admin/ai-settings")
async def admin_get_ai(_: str = Depends(verify_admin)):
    return await get_ai_settings()

@router.put("/api/crypto-news/admin/ai-settings")
async def admin_set_ai(data: AISettingsUpdate, _: str = Depends(verify_admin)):
    provider = data.provider if data.provider in ("grok", "gemini") else "grok"
    await set_ai_settings({"provider": provider, "grok_model": data.grok_model, "gemini_model": data.gemini_model})
    return {"ok": True}


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@router.put("/api/crypto-news/admin/password")
async def admin_change_password(data: PasswordChange, _: str = Depends(verify_admin)):
    admin = await get_admin()
    if not admin or not check_password(data.current_password, admin.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    await set_admin_password(hash_password(data.new_password))
    return {"ok": True}
