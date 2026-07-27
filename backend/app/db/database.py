from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from app.core.config import settings
import logging

logger = logging.getLogger("texlify.database")

# ── Engine with connection pooling ────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pooling for production
    poolclass=QueuePool,
    pool_size=10,          # Keep 10 connections open
    max_overflow=20,       # Allow 20 extra connections under load
    pool_timeout=30,       # Wait 30 seconds before giving up
    pool_recycle=1800,     # Recycle connections every 30 minutes
    pool_pre_ping=True,    # Verify connection is alive before using
    echo=settings.DEBUG,   # Log SQL only in debug mode
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()