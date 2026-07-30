from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings


def get_engine():
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_session_factory():
    engine = get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Session:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
