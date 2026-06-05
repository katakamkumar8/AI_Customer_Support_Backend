"""
app/main.py
FastAPI application factory with middleware, exception handlers, and lifespan.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings
from app.database.engine import init_db
from app.utils.logging import configure_logging, get_logger
from app.utils.middleware import (
    LoggingMiddleware,
    RequestIDMiddleware,
    register_exception_handlers,
)

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────────
    logger.info("Starting AI Customer Support Agent", env=settings.app_env)

    logger.info("Initialising PostgreSQL schema …")
    try:
        await asyncio.wait_for(init_db(), timeout=30.0)
        logger.info("PostgreSQL ready ✓")
    except Exception as exc:
        logger.error("PostgreSQL init failed – starting without DB", error=str(exc))

    logger.info("Application startup complete ✓")
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────────
    logger.info("Shutting down gracefully …")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Customer Support Agent",
        description=(
            "Production-ready multi-agent customer support backend "
            "powered by LangGraph, Groq LLM and Zilliz Cloud Vector DB.\n\n"
            "## Agents\n"
            "- **A. Intent Classifier** – detects FAQ / Refund / Technical / Order / Escalation\n"
            "- **B. Knowledge Agent** – RAG over uploaded PDF knowledge base\n"
            "- **C. Ticket Agent** – auto-creates PostgreSQL support tickets\n"
            "- **D. Escalation Agent** – routes to human when confidence is low\n"
            "- **E. Response Agent** – composes the final customer reply\n"
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware (outermost first) ────────────────────────────────────────────
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],          # tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ────────────────────────────────────────────────────────────────
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.app_env == "development"),
        log_level=settings.log_level.lower(),
    )
