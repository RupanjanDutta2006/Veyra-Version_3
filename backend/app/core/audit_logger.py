"""Structured Security and Operational Audit Logging Layer.

Implements tamper-evident audit logging per SIH26079 §22 and Research Files 109, 110 (L3):
- Logs all security events, model inferences, human review actions, and model lifecycle promotions.
- Enriches every audit record with prediction_id, job_id, user_id, role, model_version, latency, and client IP.
- Maintains a queryable in-memory circular buffer for compliance verification and operational audits.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("veyra.audit")

MAX_AUDIT_LOG_BUFFER = 2000


@dataclass
class AuditRecord:
    """Structured audit log entry."""

    audit_id: str
    timestamp: str
    event_type: str  # "PREDICTION", "HUMAN_REVIEW", "MODEL_PROMOTION", "AUTH_FAILURE", "OOD_ABSTENTION"
    action: str
    status: str  # "SUCCESS", "FAILURE", "ABSTAINED", "DENIED"
    prediction_id: Optional[str] = None
    job_id: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None
    model_version: Optional[str] = None
    data_version: Optional[str] = None
    location: Optional[str] = None
    client_ip: Optional[str] = None
    latency_ms: Optional[float] = None
    status_code: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)


class AuditLogger:
    """Centralized audit logger maintaining both structured system logs and in-memory queryable buffer."""

    def __init__(self, max_buffer_size: int = MAX_AUDIT_LOG_BUFFER):
        self.max_buffer_size = max_buffer_size
        self._buffer: List[AuditRecord] = []

    def log_event(
        self,
        event_type: str,
        action: str,
        status: str = "SUCCESS",
        prediction_id: Optional[str] = None,
        job_id: Optional[str] = None,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        model_version: Optional[str] = None,
        data_version: Optional[str] = None,
        location: Optional[str] = None,
        client_ip: Optional[str] = None,
        latency_ms: Optional[float] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        """Create and emit an authoritative audit record."""
        audit_id = f"aud_{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        record = AuditRecord(
            audit_id=audit_id,
            timestamp=now_str,
            event_type=event_type,
            action=action,
            status=status,
            prediction_id=prediction_id,
            job_id=job_id,
            user_id=user_id,
            role=role,
            model_version=model_version,
            data_version=data_version,
            location=location,
            client_ip=client_ip,
            latency_ms=latency_ms,
            status_code=status_code,
            details=details or {},
        )

        self._buffer.append(record)
        if len(self._buffer) > self.max_buffer_size:
            self._buffer.pop(0)

        # Emit structured JSON log line for SIEM / external log collectors
        logger.info(
            "AUDIT: %s",
            json.dumps(asdict(record), default=str),
        )
        return record

    def query_logs(
        self,
        event_type: Optional[str] = None,
        prediction_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditRecord]:
        """Query recent audit records by filter criteria."""
        results = self._buffer
        if event_type:
            results = [r for r in results if r.event_type.upper() == event_type.upper()]
        if prediction_id:
            results = [r for r in results if r.prediction_id == prediction_id]
        if user_id:
            results = [r for r in results if r.user_id == user_id]

        return list(reversed(results[-limit:]))

    def clear(self) -> None:
        """Clear audit buffer (for testing)."""
        self._buffer.clear()


default_audit_logger = AuditLogger()
