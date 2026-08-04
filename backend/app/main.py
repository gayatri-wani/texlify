import logging
import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.security_middleware import SecurityMiddleware
from app.db.database import engine, Base, get_db

setup_logging(settings.LOG_FORMAT)
logger = logging.getLogger("texlify")

# ── Sentry (no-op when DSN is empty) ────────────────────────────────────────
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            send_default_pii=False,
        )
        logger.info("Sentry initialized")
    except ImportError:
        logger.warning("sentry-sdk not installed — run: pip install sentry-sdk[fastapi]")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Texlify v%s (%s)", settings.APP_VERSION, settings.ENVIRONMENT)
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info("Database tables verified")
    yield
    logger.info("Texlify shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Word Document Editor",
    docs_url="/api/docs"   if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ── Request-ID middleware ───────────────────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Security + CORS ─────────────────────────────────────────────────────────
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Content-Disposition", "X-Request-ID"],
    max_age=3600,
)


# ── Global error handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "?")
    logger.error(
        "Unhandled exception [%s] %s %s: %s: %s",
        request_id, request.method, request.url.path,
        type(exc).__name__, exc
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."}
    )


# ── Routers ──────────────────────────────────────────────────────────────────
from app.api.routes.auth      import router as auth_router
from app.api.routes.documents import router as documents_router

app.include_router(auth_router,      prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health")
def health():
    """Real health check — probes DB. Returns 503 if DB is down."""
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    upload_dir_ok = os.path.isdir(settings.UPLOAD_DIR)

    if not db_ok:
        return JSONResponse(
            status_code=503,
            content={
                "status":       "unhealthy",
                "database":     "down",
                "upload_dir":   upload_dir_ok,
            }
        )
    return {
        "status":     "healthy",
        "version":    settings.APP_VERSION,
        "database":   "ok",
        "upload_dir": upload_dir_ok,
    }