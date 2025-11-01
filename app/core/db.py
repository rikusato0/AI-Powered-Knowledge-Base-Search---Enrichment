from sqlalchemy import create_engine  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import sessionmaker, declarative_base  # pyright: ignore[reportMissingImports]
from app.core.config import settings


DATABASE_URL = f"sqlite:///{settings.DB_PATH}"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
