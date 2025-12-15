import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import settings

# check if production
is_production = os.getenv("ENVIRONMENT") == "prd"

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20 if is_production else 5,
    max_overflow=10 if is_production else 0,
    pool_timeout=30,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


