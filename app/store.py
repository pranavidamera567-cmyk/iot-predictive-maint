"""Persistence: PostgreSQL when DATABASE_URL is set, otherwise in-memory only."""
import os

from sqlalchemy import create_engine


def get_engine():
    url = os.environ.get("DATABASE_URL")
    return create_engine(url) if url else None


def save(engine, **frames):
    if engine is None:
        return
    for name, df in frames.items():
        df.to_sql(name, engine, if_exists="replace", index=False)
