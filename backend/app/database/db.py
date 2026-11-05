"""
SENTINEL AI - Database Layer
SQLite schema & SQLAlchemy models for sensor states, security alerts, and simulation logs.
"""
from datetime import datetime, timezone
from typing import Generator
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# Engine setup
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SensorRecord(Base):
    """Stores sensor metadata, current operational state, and dynamic trust."""
    __tablename__ = "sensors"

    id = Column(String(50), primary_key=True, index=True)
    sensor_type = Column(String(50), nullable=False)   # level, pressure, flow, status
    unit = Column(String(20), nullable=False)          # m, L/s, binary
    description = Column(String(200), nullable=True)
    dataset = Column(String(50), default="batadal")
    
    current_value = Column(Float, nullable=True)
    trust_score = Column(Float, default=100.0)
    status = Column(String(20), default="Trusted")      # Trusted, Moderate, Suspicious, Critical
    anomaly_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_anomaly_time = Column(DateTime, nullable=True)
    trust_reasons = Column(Text, nullable=True)         # JSON string of diagnostic evidence


class SecurityAlert(Base):
    """Stores security alerts triggered by FDI detection or critical trust drops."""
    __tablename__ = "security_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(String(50), index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    dataset = Column(String(50), default="batadal")
    severity = Column(String(20), nullable=False)       # Low, Medium, High, Critical
    alert_type = Column(String(50), nullable=False)      # FDI, Statistical Anomaly, Physical Inconsistency
    
    observed_value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    trust_score = Column(Float, nullable=False)
    detection_methods = Column(String(200), nullable=False)  # e.g., "IsolationForest, RollingZScore"
    evidence = Column(Text, nullable=False)                  # Human-readable evidence list
    recommended_action = Column(Text, nullable=False)
    is_acknowledged = Column(Boolean, default=False)


class SimulationLog(Base):
    """Tracks synthetic FDI attack injection trials and detection benchmark results."""
    __tablename__ = "simulation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(String(50), nullable=False)
    attack_type = Column(String(50), nullable=False)     # value_manipulation, constant_value, replay, gradual_drift
    dataset = Column(String(50), default="batadal")
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    intensity = Column(Float, nullable=True)             # Magnitude or slope factor
    
    detected = Column(Boolean, default=False)
    detection_latency_steps = Column(Integer, nullable=True)
    min_trust_score = Column(Float, nullable=True)
    total_injected_points = Column(Integer, default=0)
    detected_points = Column(Integer, default=0)
    summary = Column(Text, nullable=True)


class TrustHistory(Base):
    """Historical timeline of sensor trust changes for auditability."""
    __tablename__ = "trust_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sensor_id = Column(String(50), index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    score = Column(Float, nullable=False)
    penalty_breakdown = Column(Text, nullable=True)      # JSON string breakdown


def init_db():
    """Initializes SQLite tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
