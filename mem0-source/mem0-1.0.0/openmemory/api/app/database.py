import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# load .env file (make sure you have DATABASE_URL set)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./openmemory.db")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment")

# SQLAlchemy engine & session
# Configure connection pool to prevent exhaustion:
# - pool_size: Number of connections to maintain (default 5)
# - max_overflow: Additional connections beyond pool_size (default 10)
# - pool_timeout: Seconds to wait for connection from pool (default 30)
# - pool_recycle: Seconds before recycling connection (prevent stale connections)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    pool_size=5,  # Default pool size
    max_overflow=10,  # Default overflow
    # pool_timeout=30,  # Default 30 seconds
    # pool_recycle=3600,  # Recycle connections after 1 hour
    # pool_pre_ping=True,  # Verify connections before using
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
