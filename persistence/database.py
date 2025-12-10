import os
from typing import Generator

from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from persistence.model.abstract_entity import Base

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

def drop_db() -> None:
    Base.metadata.drop_all(bind=engine)

def get_test_db() -> Generator[Session, None, None]:
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    Base.metadata.create_all(bind=test_engine)

    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )

    db = TestSessionLocal()

    try:
        yield db
    finally:db.close()