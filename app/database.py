"""
database.py — SQLAlchemy setup with PostgreSQL / SQLite fallback.
"""
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, DateTime, Text, Boolean, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker

# ── Connection ──────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./predictions.db"   # SQLite fallback for local dev
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Models ──────────────────────────────────────────────────────────────
class PredictionRecord(Base):
    __tablename__ = "predictions"

    prediction_id   = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp       = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    gpu_id          = Column(String, index=True, nullable=True)
    hostname        = Column(String, index=True, nullable=True)
    serial          = Column(String, nullable=True)
    failure_probability = Column(Float, nullable=False)
    risk_level      = Column(String, nullable=False)   # HIGH / MEDIUM / LOW
    model_name      = Column(String, default="GPU_Failure_XGBoost")
    model_version   = Column(String, default="1")
    features_json   = Column(Text, nullable=True)      # JSON blob for replay
    acknowledged    = Column(Boolean, default=False, nullable=False)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_db():
    """FastAPI dependency: yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy import inspect, text

def init_db():
    """Create all tables (called at startup) and migrate missing columns."""
    Base.metadata.create_all(bind=engine)
    try:
        inspector = inspect(engine)
        if "predictions" in inspector.get_table_names():
            existing_cols = {col["name"] for col in inspector.get_columns("predictions")}
            with engine.begin() as conn:
                if "model_name" not in existing_cols:
                    conn.execute(text("ALTER TABLE predictions ADD COLUMN model_name VARCHAR DEFAULT 'GPU_Failure_XGBoost'"))
                if "created_at" not in existing_cols:
                    conn.execute(text("ALTER TABLE predictions ADD COLUMN created_at TIMESTAMP"))
    except Exception as e:
        print(f"Warning during init_db migration: {e}")

