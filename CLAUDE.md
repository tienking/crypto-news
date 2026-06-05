# CLAUDE.md — Project Instructions for Claude Code

> Loaded automatically at the start of every session.

**crypto-news** — a crypto news aggregator. A FastAPI backend (**port 8003**) pulls RSS
feeds on a schedule, stores articles in MongoDB, and serves them to a React news-site
frontend at `tienmai.space/projects/crypto-news`. Independent service: own repo, own
MongoDB cluster.

---

## Commit Message Standard

Conventional Commits:

```
type(scope): short description — ≤72 chars

- What changed and why
- Bundle doc updates into the same commit

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

**Types**: `feat` · `fix` · `refactor` · `style` · `docs` · `chore` · `ci`
**Scopes** (optional): `api` · `ui` · `rss` · `db` · `chat`

## Documentation Update Rule

After every code change, check and update in the same commit:
- `README.md` — features, tech stack, API, RSS sources
- `CLAUDE.md` — workflow rules or conventions

Use `type: docs` only when the commit touches docs exclusively.

## Workflow Conventions

- **Git**: commit only — never push. The developer pushes.
- **Remotes**: `origin` (GitLab) + `github` (GitHub). Branch `main` only. No force-push.

## Code Conventions

- **Language**: **English only** — UI text, comments, docs.
- **Frontend styling**: 100% inline styles — no CSS classes/Tailwind/modules. Dark theme
  via CSS vars in `index.css` (Bitcoin-orange accent `#f7931a`). Inter + JetBrains Mono.
- **API namespace**: every route under `/api/crypto-news/` so Nginx routes to port 8003.
- **Vite base**: `/projects/crypto-news/`.
- **RSS**: feed list lives in `rss.py` (`FEEDS`). Articles are deduped by `guid` (upsert).
  Refresh runs in-process via APScheduler every `REFRESH_MINUTES` (default 15) + on startup.
- **Chatbot**: uses **Grok (xAI)**, NOT Gemini — OpenAI-compatible API via `grok.py`
  (`XAI_API_KEY`, `GROK_MODEL` default `grok-3`). RAG context = 30 most recent headlines.
- **Admin**: JWT (`auth.py`), seeded from `ADMIN_USERNAME`/`ADMIN_PASSWORD`. Coin pairs +
  RSS feeds are stored in the `settings` collection (seeded once from DEFAULT_COINS /
  DEFAULT_FEEDS), editable at `/projects/crypto-news/admin`. The chart and RSS job read
  them from the DB, not hardcoded. Admin SPA is the same Vite build, routed client-side
  in `main.jsx` when the path ends with `/admin`.

## After Deploy

```bash
journalctl -u crypto-news -n 30   # look for "Application startup complete." + [refresh] logs
```

## tienmai.space project family

| Project | Port | Path |
|---------|------|------|
| tienmai-space (portfolio + admin) | 8000 | `/`, `/admin` |
| job-tracker | 8001 | `/jobtracker` |
| ai-dashboard | 8002 | `/projects/ai-dashboard` |
| crypto-news | 8003 | `/projects/crypto-news` |
