import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import auth, documents
from app.db.database import engine, Base
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.security_middleware import SecurityMiddleware

# Setup logging first
setup_logging()
logger = logging.getLogger("texlify")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Texlify v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    Base.metadata.create_all(bind=engine)
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

# ── Security middleware (order matters) ───────────────────────────────────────

# 1. Security headers + brute force protection
app.add_middleware(SecurityMiddleware)

# 2. CORS — only allow your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Content-Disposition"],
    max_age=3600,
)

# ── Global exception handlers ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: "
        f"{type(exc).__name__}: {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again."
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


# ── Routes ────────────────────────────────────────────────────────────────────

app.include_router(auth,      prefix="/api/v1")
app.include_router(documents, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "app":     settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status":  "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy", "version": settings.APP_VERSION}