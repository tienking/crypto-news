from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import REFRESH_MINUTES
from database import ensure_indexes, upsert_articles
from rss import fetch_all
from api import router

scheduler = AsyncIOScheduler()


async def refresh_job():
    items = await fetch_all()
    inserted = await upsert_articles(items)
    print(f"[refresh] fetched={len(items)} inserted={inserted}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    await refresh_job()  # initial fill on startup
    scheduler.add_job(refresh_job, "interval", minutes=REFRESH_MINUTES, id="rss_refresh")
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Crypto News API", lifespan=lifespan)
app.include_router(router)
