import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.scrape import router as scrape_router
from app.api.tenders import router as tenders_router
from app.core.config import settings
from app.db.session import Base, engine
from app.models import ScrapeJob, Tender  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="OliveSoft Tender Scraper", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(scrape_router)
app.include_router(tenders_router)


@app.on_event("startup")
def initialize_database() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables are ready")
    except Exception:
        logger.exception("Database initialization failed; requests requiring the database may fail")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
def database_health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}
