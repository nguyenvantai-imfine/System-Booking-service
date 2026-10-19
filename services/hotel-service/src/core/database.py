import asyncio
from functools import partial
from typing import TypeVar, Callable, Any

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.core.config import settings

# Khởi tạo SQLAlchemy Engine cho SQL Server
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"fast_executemany": True}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

T = TypeVar('T')

async def run_in_threadpool(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Chạy sync function trong thread pool để không block event loop.

    Sử dụng cho các DB operations sync (commit, rollback, refresh, execute).
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))