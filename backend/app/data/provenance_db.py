"""PostgreSQL / SQLAlchemy Provenance & Audit Metadata Store (SIH26079 §7.3, §16, C8).

Provides durable relational persistence for:
- Operational forecast cycles (ForecastCycleRecord).
- Prediction audit envelopes & verification lifecycle (PredictionAuditRecord).
- Dataset snapshots, license URIs & cryptographic checksums (DatasetSnapshotRecord).

Configurable for production PostgreSQL, with automatic SQLite fallback for
local testing and edge environments.
"""
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

Base = declarative_base()


class ForecastCycleRecord(Base):
    """Authoritative record of an ingested operational NWP cycle (§16)."""
    __tablename__ = "forecast_cycles"

    cycle_id = Column(String(64), primary_key=True, index=True)
    model_provider = Column(String(64), nullable=False, default="NOAA_GEFS")
    issue_time = Column(DateTime, nullable=False)
    max_lead_hours = Column(Integer, nullable=False, default=384)
    member_count = Column(Integer, nullable=False, default=31)
    sha256_checksum = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False, default="AVAILABLE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "model_provider": self.model_provider,
            "issue_time": self.issue_time.isoformat() if self.issue_time else None,
            "max_lead_hours": self.max_lead_hours,
            "member_count": self.member_count,
            "sha256_checksum": self.sha256_checksum,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PredictionAuditRecord(Base):
    """Authoritative audit record of a prediction instance and ground-truth verification (§16)."""
    __tablename__ = "prediction_audits"

    prediction_id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    location = Column(String(128), nullable=False)
    variable = Column(String(64), nullable=False, default="temperature_2m")
    lead_hours = Column(Integer, nullable=True)
    bust_probability = Column(Float, nullable=True)
    color_band = Column(String(16), nullable=False, default="GRAY")
    risk_level = Column(String(16), nullable=True)
    ood_score = Column(Float, nullable=True)
    claim_scope = Column(String(64), nullable=False, default="PUBLIC_PROXY_PROTOTYPE")
    truth_status = Column(String(32), nullable=False, default="PENDING")
    verified_outcome = Column(String(32), nullable=True)  # "BUST" or "NORMAL"
    reason_codes_csv = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "location": self.location,
            "variable": self.variable,
            "lead_hours": self.lead_hours,
            "bust_probability": self.bust_probability,
            "color_band": self.color_band,
            "risk_level": self.risk_level,
            "ood_score": self.ood_score,
            "claim_scope": self.claim_scope,
            "truth_status": self.truth_status,
            "verified_outcome": self.verified_outcome,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DatasetSnapshotRecord(Base):
    """Authoritative catalog of ingested dataset snapshots, licenses, and checksums (§16)."""
    __tablename__ = "dataset_snapshots"

    snapshot_id = Column(String(64), primary_key=True, index=True)
    dataset_name = Column(String(128), nullable=False)
    version = Column(String(32), nullable=False)
    storage_uri = Column(String(256), nullable=False)
    sha256_checksum = Column(String(64), nullable=False)
    license_uri = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False)  # "PREDICTOR_INPUT" or "VERIFICATION_ONLY"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "dataset_name": self.dataset_name,
            "version": self.version,
            "storage_uri": self.storage_uri,
            "sha256_checksum": self.sha256_checksum,
            "license_uri": self.license_uri,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProvenanceDatabase:
    """Database interface providing connection pooling, table initialization, and CRUD operations."""

    def __init__(self, db_url: Optional[str] = None):
        url = db_url or os.getenv("DATABASE_URL")
        if not url:
            # Safe SQLite fallback
            url = "sqlite:///./veyra_provenance.db"

        # Handle postgres:// -> postgresql:// for SQLAlchemy compatibility
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        self.engine = create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in url else {},
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        # Create all tables on startup
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()

    def record_forecast_cycle(
        self,
        cycle_id: str,
        model_provider: str = "NOAA_GEFS",
        issue_time: Optional[datetime] = None,
        max_lead_hours: int = 384,
        member_count: int = 31,
        sha256_checksum: Optional[str] = None,
        status: str = "AVAILABLE",
    ) -> ForecastCycleRecord:
        """Upsert an operational forecast cycle record."""
        session = self.get_session()
        try:
            record = session.query(ForecastCycleRecord).filter_by(cycle_id=cycle_id).first()
            if not record:
                record = ForecastCycleRecord(
                    cycle_id=cycle_id,
                    model_provider=model_provider,
                    issue_time=issue_time or datetime.now(timezone.utc),
                    max_lead_hours=max_lead_hours,
                    member_count=member_count,
                    sha256_checksum=sha256_checksum,
                    status=status,
                )
                session.add(record)
            else:
                record.status = status
                if sha256_checksum:
                    record.sha256_checksum = sha256_checksum
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def record_prediction_audit(
        self,
        prediction_id: str,
        location: str,
        bust_probability: Optional[float],
        color_band: str,
        variable: str = "temperature_2m",
        lead_hours: Optional[int] = None,
        risk_level: Optional[str] = None,
        ood_score: Optional[float] = None,
        claim_scope: str = "PUBLIC_PROXY_PROTOTYPE",
        truth_status: str = "PENDING",
        reason_codes: Optional[List[str]] = None,
    ) -> PredictionAuditRecord:
        """Persist a prediction audit trail entry."""
        session = self.get_session()
        try:
            record = PredictionAuditRecord(
                prediction_id=prediction_id,
                timestamp=datetime.now(timezone.utc),
                location=location,
                variable=variable,
                lead_hours=lead_hours,
                bust_probability=bust_probability,
                color_band=color_band,
                risk_level=risk_level,
                ood_score=ood_score,
                claim_scope=claim_scope,
                truth_status=truth_status,
                reason_codes_csv=",".join(reason_codes) if reason_codes else None,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()

    def update_truth_status(
        self,
        prediction_id: str,
        verified_outcome: str,  # "BUST" or "NORMAL"
    ) -> Optional[PredictionAuditRecord]:
        """Update ground-truth verification outcome once observation becomes available."""
        session = self.get_session()
        try:
            record = session.query(PredictionAuditRecord).filter_by(prediction_id=prediction_id).first()
            if record:
                record.truth_status = "VERIFIED"
                record.verified_outcome = verified_outcome.upper()
                session.commit()
                session.refresh(record)
            return record
        finally:
            session.close()

    def record_dataset_snapshot(
        self,
        snapshot_id: str,
        dataset_name: str,
        version: str,
        storage_uri: str,
        sha256_checksum: str,
        license_uri: str,
        role: str,
    ) -> DatasetSnapshotRecord:
        """Record dataset snapshot provenance."""
        session = self.get_session()
        try:
            record = session.query(DatasetSnapshotRecord).filter_by(snapshot_id=snapshot_id).first()
            if not record:
                record = DatasetSnapshotRecord(
                    snapshot_id=snapshot_id,
                    dataset_name=dataset_name,
                    version=version,
                    storage_uri=storage_uri,
                    sha256_checksum=sha256_checksum,
                    license_uri=license_uri,
                    role=role,
                )
                session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()
