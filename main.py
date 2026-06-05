from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import REFRESH_MINUTES
from database import ensure_indexes, seed_defaults, upsert_articles, get_feeds
from rss import fetch_all
from api import router

scheduler = AsyncIOScheduler()


async def refresh_job():
    feeds = await get_feeds()
    items = await fetch_all(feeds)
    inserted = await upsert_articles(items)
    print(f"[refresh] feeds={len(feeds)} fetched={len(items)} inserted={inserted}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    await seed_defaults()
    await refresh_job()  # initial fill on startup
    scheduler.add_job(refresh_job, "interval", minutes=REFRESH_MINUTES, id="rss_refresh")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Crypto News API", lifespan=lifespan)
app.include_router(router)
