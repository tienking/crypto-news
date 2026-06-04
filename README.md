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
4. The React frontend lists articles (featured + grid), filters by source, searches, and
   opens an **in-app reader** (with a link to the original).
5. A **Grok-powered chatbot** (bottom-right) answers questions about crypto and the latest
   news — it gets the 30 most recent headlines as context (RAG).

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Backend | Python / FastAPI · Uvicorn (port **8003**) |
| RSS | feedparser + httpx (async fetch) |
| Scheduler | APScheduler (in-process, every 15 min) |
| Chatbot | Grok (xAI) — OpenAI-compatible API, RAG over recent headlines |
| Database | MongoDB (Motor) — db `cryptonews`, collection `articles` |
| Frontend | React 19 + Vite (base `/projects/crypto-news/`) · Inter + JetBrains Mono |
| Hosting | Hostinger VPS (shared), Nginx, systemd, GitLab CI/CD |

---

## Project Structure

```
crypto-news/
├── main.py                  # FastAPI app + APScheduler (refresh on startup + interval)
├── api.py                   # Routes (/api/crypto-news/*)
├── rss.py                   # FEEDS list + fetch/parse/normalize
├── grok.py                  # Grok (xAI) chat client
├── database.py              # Motor: upsert (dedup by guid), list, get, sources, recent
├── config.py                # Env loader (MONGODB_URL, REFRESH_MINUTES, XAI_API_KEY, GROK_MODEL)
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
        ├── main.jsx
        ├── App.jsx              # News list, source chips, search, load-more
        ├── index.css           # Dark theme + fonts
        ├── components/
        │   ├── ArticleCard.jsx  # Card (image, source, time-ago, summary)
        │   ├── Reader.jsx       # In-app article reader + "Read original"
        │   └── ChatPopup.jsx    # Grok chatbot (bottom-right)
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
| POST | `/api/crypto-news/refresh` | Manually trigger an RSS refresh |
| POST | `/api/crypto-news/chat` | Grok chatbot (`message`, `history`) → `{reply}` |

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
