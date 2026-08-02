"""
SQLAlchemy engine, session factory, and declarative Base.
Uses a pooled connection so the app survives 24/7 without exhausting
Postgres connections (Supabase free tier caps concurrent connections).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,     # detects dead connections before using them —
                            # critical for long-running 24/7 processes, since
                            # managed Postgres providers silently drop idle
                            # connections after a timeout
    pool_size=5,
    max_overflow=10,
    pool_recycle=1800,      # recycle connections every 30 min
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
