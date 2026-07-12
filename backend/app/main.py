from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base
from app.api.routes import auth, documents
from app.models import user, document, command_history
import os

Base.metadata.create_all(bind=engine)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Agent for Word Document Editing — Texlify"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "Welcome to Texlify API", "version": settings.APP_VERSION}


@app.get("/health")
def health_check():
    return {"status": "healthy", "app": settings.APP_NAME}