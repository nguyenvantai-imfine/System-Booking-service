
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from src.core.config import settings


def create_database_url():
    server = settings.DB_SERVER.strip()

    if not server:
        raise ValueError("DB_SERVER khong duoc de trong.")

    if not settings.DB_NAME.strip():
        raise ValueError("DB_NAME khong duoc de trong.")

    # SQL Server instance: localhost\SQLEXPRESS
    # SQL Server port: localhost,1433
    if "\\" not in server and settings.DB_PORT > 0:
        server = f"{server},{settings.DB_PORT}"

    connection_args = {
        "driver": settings.DB_DRIVER,
        "TrustServerCertificate": "yes",
    }

    if settings.DB_TRUSTED_CONNECTION:
        connection_args["trusted_connection"] = "yes"

        return URL.create(
            "mssql+pyodbc",
            host=server,
            database=settings.DB_NAME,
            query=connection_args,
        )

    return URL.create(
        "mssql+pyodbc",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=server,
        database=settings.DB_NAME,
        query=connection_args,
    )


engine = create_engine(
    create_database_url(),
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
    connect_args={
        "timeout": 30,
    },
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
