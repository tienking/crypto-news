# Crypto News

A crypto news aggregator. Pulls the latest articles from top crypto RSS feeds on a
schedule, stores them in MongoDB, and serves them as a clean, auto-updating news site
with in-app reading, source filters, and search.

🔗 **Live:** [tienmai.space/projects/crypto-news](https://tienmai.space/projects/crypto-news)

---

## How it works

1. A FastAPI backend fetches a curated list of crypto RSS feeds (CoinDesk, Cointelegraph,
   Decrypt, The Block, CryptoSlate, Bitcoin Magazine, BeInCrypto, CoinJournal).
2. Articles are normalized (title, summary, content, image, source, published) and
   **upserted into MongoDB, deduped by `guid`** — so each refresh only adds new items.
3. An in-process **APScheduler** job refreshes every `REFRESH_MINUTES` (default 15) and
   once on startup. No external cron needed.
   A **MongoDB TTL index** auto-deletes articles older than `ARTICLE_TTL_DAYS` (default 30)
   so storage stays bounded — no cleanup job required.
4. The React frontend lists articles (featured + grid), filters by source, searches, and
   opens an **in-app reader** (with a link to the original).
5. An **AI chatbot** (bottom-right) answers questions about crypto and the latest news —
   it gets the 30 most recent headlines as context (RAG). The provider is switchable
   between **Grok (xAI)** and **Gemini (Google)**, each with its own model.
6. An **Admin page** (`/projects/crypto-news/admin`, JWT login) edits the TradingView chart
   coin pairs, the RSS source list, and the AI provider/model — all stored in MongoDB
   (`settings` collection).

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Backend | Python / FastAPI · Uvicorn (port **8003**) |
| RSS | feedparser + httpx (async fetch) |
| Scheduler | APScheduler (in-process, every 15 min) |
| Chatbot | Grok (xAI) or Gemini (Google) — switchable in Admin, RAG over recent headlines |
| Database | MongoDB (Motor) — db `cryptonews`, collection `articles` |
| Frontend | React 19 + Vite (base `/projects/crypto-news/`) · Inter + JetBrains Mono |
| Hosting | Hostinger VPS (shared), Nginx, systemd, GitLab CI/CD |

---

## Project Structure

```
crypto-news/
├── main.py                  # FastAPI app + APScheduler (refresh on startup + interval)
├── api.py                   # Routes (/api/crypto-news/*)
├── rss.py                   # DEFAULT_FEEDS + fetch/parse/normalize (feeds come from DB)
├── ai.py                    # Chat dispatcher → Grok or Gemini per AI settings
├── grok.py                  # Grok (xAI) chat client
├── gemini.py                # Gemini (Google) chat client
├── auth.py                  # Admin JWT + bcrypt
├── database.py              # Motor: articles + settings (coins/feeds/admin), seed defaults
├── config.py                # Env loader (Mongo, Grok, JWT_SECRET, ADMIN_*)
├── requirements.txt
├── .env.example
├── .gitlab-ci.yml
├── deploy/
│   ├── crypto-news.service  # systemd unit (port 8003)
│   └── nginx-snippet.conf
└── frontend/
    ├── index.html
    ├── vite.config.js       # base "/projects/crypto-news/", proxy → 8003
    ├── public/favicon.svg   # 📰
    └── src/
        ├── main.jsx            # Routes to AdminApp if path ends with /admin, else App
        ├── App.jsx             # News list, source chips, search, load-more, Admin link
        ├── AdminApp.jsx        # Login + coin-pairs editor + RSS-sources editor
        ├── index.css           # Dark theme + fonts
        ├── components/
        │   ├── ArticleCard.jsx  # Card (image, source, time-ago, summary)
        │   ├── Reader.jsx       # In-app article reader + "Read original"
        │   ├── ChatPopup.jsx    # Grok chatbot (bottom-right)
        │   └── MarketChart.jsx  # TradingView candle chart (coins from /coins API)
        └── lib/api.js           # API client + timeAgo()
```

---

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/crypto-news/health` | Health check |
| GET | `/api/crypto-news/articles` | Paginated list (`page`, `limit`, `source`, `q`) |
| GET | `/api/crypto-news/article/{id}` | Single article (with full content) |
| GET | `/api/crypto-news/sources` | Distinct source names (for filters) |
| GET | `/api/crypto-news/coins` | Chart coin pairs (public, for MarketChart) |
| POST | `/api/crypto-news/refresh` | Manually trigger an RSS refresh |
| POST | `/api/crypto-news/chat` | Grok chatbot (`message`, `history`) → `{reply}` |
| POST | `/api/crypto-news/admin/login` | Admin login → JWT |
| GET/PUT | `/api/crypto-news/admin/coins` | Read / save chart coin pairs |
| GET/PUT | `/api/crypto-news/admin/feeds` | Read / save RSS sources (PUT also refetches) |
| GET/PUT | `/api/crypto-news/admin/ai-settings` | Read / save provider + per-provider model |

> **Admin:** seeded on first run from `ADMIN_USERNAME` (default `admin`) /
> `ADMIN_PASSWORD` env. If `ADMIN_PASSWORD` is unset, a random one is generated and
> printed once at startup — there is no guessable default. Coin pairs and feeds live
> in the `settings` collection — seeded once, then editable via the Admin page.
>
> **Required env:** `MONGODB_URL` and `JWT_SECRET` are mandatory — the app refuses to
> start without them (no fallback secret). Generate `JWT_SECRET` as a long random string.

---

## Local Development

```bash
# Backend
python -m venv crypto-news-venv
source crypto-news-venv/bin/activate     # Windows: crypto-news-venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                       # set MONGODB_URL + XAI_API_KEY
uvicorn main:app --port 8003               # fetches RSS on startup

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                                # proxies /api/ to http://127.0.0.1:8003
```

> **MongoDB Atlas:** whitelist your local IP under Network Access first.

---

## Deployment

Auto-deploy via GitLab CI/CD on push to `main`. On the VPS:

```bash
# /usr/local/bin/deploy-crypto-news.sh
cd /root/projects/crypto-news
git pull origin main
source crypto-news-venv/bin/activate
pip install -r requirements.txt --quiet
cd frontend && npm install --silent && npm run build && cd ..
systemctl restart crypto-news
```

Add the blocks from `deploy/nginx-snippet.conf` to the tienmai Nginx server block.

### Adding / removing feeds

Edit the `FEEDS` list in [`rss.py`](rss.py) and redeploy.
