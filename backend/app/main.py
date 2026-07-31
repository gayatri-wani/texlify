import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.security_middleware import SecurityMiddleware
from app.db.database import engine, Base

setup_logging()
logger = logging.getLogger("texlify")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting Texlify v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
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

# Middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["Content-Disposition"],
    max_age=3600,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception on {request.method} "
        f"{request.url.path}: {type(exc).__name__}: {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."}
    )


# Import routers AFTER app is created
from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router

app.include_router(auth_router,      prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health")
def health():
    return {"status": "healthy", "version": settings.APP_VERSION}