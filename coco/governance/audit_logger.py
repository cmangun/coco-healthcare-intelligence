"""
Audit Logger

Implements immutable audit logging with hash chain integrity.
Per FDE Playbook: Every operation must be auditable.

HIPAA Technical Safeguard: Audit controls (§164.312(b))
"""

from datetime import datetime
from typing import Any, Optional
import hashlib
import json
import uuid

import structlog

logger = structlog.get_logger(__name__)


class AuditEntry:
    """Single audit log entry with hash chain."""
    
    def __init__(
        self,
        entry_id: str,
        timestamp: datetime,
        component: str,
        operation: str,
        actor: str,
        details: dict,
        previous_hash: str,
    ):
        self.entry_id = entry_id
        self.timestamp = timestamp
        self.component = component
        self.operation = operation
        self.actor = actor
        self.details = details
        self.previous_hash = previous_hash
        self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of entry."""
        content = json.dumps({
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "operation": self.operation,
            "actor": self.actor,
            "details": self.details,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "operation": self.operation,
            "actor": self.actor,
            "details": self.details,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }


class AuditLogger:
    """
    Audit logger with hash chain for tamper detection.
    
    Features:
    - Immutable append-only log
    - Hash chain for integrity verification
    - HIPAA-compliant audit trail
    - Structured logging with context
    
    Per FDE Playbook Phase 6:
    "Tool call audit logging: Every tool call with prompt, result,
    timing goes to tamper-evident log (owner: Platform Engineer)"
    """
    
    # Class-level chain for cross-component integrity
    _global_chain: list[AuditEntry] = []
    _genesis_hash = "genesis_0000000000000000"
    
    def __init__(self, component: str, actor: str = "system"):
        self.component = component
        self.actor = actor
        self.local_chain: list[AuditEntry] = []
    
    def _get_previous_hash(self) -> str:
        """Get hash of previous entry in chain."""
        if AuditLogger._global_chain:
            return AuditLogger._global_chain[-1].hash
        return AuditLogger._genesis_hash
    
    def log_operation(
        self,
        operation: str,
        actor: Optional[str] = None,
        **details: Any,
    ) -> AuditEntry:
        """
        Log an auditable operation.
        
        Args:
            operation: Operation type (e.g., "predict_readmission")
            actor: Who/what performed the operation
            **details: Additional context
        
        Returns:
            AuditEntry with hash
        """
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            component=self.component,
            operation=operation,
            actor=actor or self.actor,
            details=self._sanitize_details(details),
            previous_hash=self._get_previous_hash(),
        )
        
        # Append to chains
        self.local_chain.append(entry)
        AuditLogger._global_chain.append(entry)
        
        # Log to structured logger
        logger.info(
            "audit_entry",
            entry_id=entry.entry_id,
            component=entry.component,
            operation=entry.operation,
            actor=entry.actor,
            hash=entry.hash[:16],  # Truncate for readability
        )
        
        return entry
    
    def _sanitize_details(self, details: dict) -> dict:
        """
        Sanitize details to remove sensitive information.
        
        Per HIPAA: PHI should not appear in audit logs in clear text.
        """
        sanitized = {}
        sensitive_keys = {
            "ssn", "social_security", "dob", "date_of_birth",
            "address", "phone", "email", "mrn", "insurance_id",
        }
        
        for key, value in details.items():
            key_lower = key.lower()
            if any(s in key_lower for s in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 1000:
                sanitized[key] = f"[TRUNCATED:{len(value)} chars]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def log_phi_access(
        self,
        patient_id: str,
        data_type: str,
        purpose: str,
        actor: Optional[str] = None,
    ) -> AuditEntry:
        """
        Log PHI access per HIPAA requirements.
        
        § 164.312(b): Audit controls
        § 164.312(d): Person or entity authentication
        """
        return self.log_operation(
            operation="phi_access",
            actor=actor,
            patient_id=patient_id,
            data_type=data_type,
            purpose=purpose,
            hipaa_category="access_control",
        )
    
    def log_phi_disclosure(
        self,
        patient_id: str,
        recipient: str,
        data_types: list[str],
        purpose: str,
        actor: Optional[str] = None,
    ) -> AuditEntry:
        """
        Log PHI disclosure per HIPAA requirements.
        
        § 164.528: Accounting of disclosures
        """
        return self.log_operation(
            operation="phi_disclosure",
            actor=actor,
            patient_id=patient_id,
            recipient=recipient,
            data_types=data_types,
            purpose=purpose,
            hipaa_category="disclosure",
        )
    
    def log_model_inference(
        self,
        model_id: str,
        model_version: str,
        input_hash: str,
        output_summary: str,
        latency_ms: float,
        cost_usd: float,
        actor: Optional[str] = None,
    ) -> AuditEntry:
        """
        Log model inference per FDE Playbook.
        
        Phase 6 requirement: All tool/model calls logged.
        """
        return self.log_operation(
            operation="model_inference",
            actor=actor,
            model_id=model_id,
            model_version=model_version,
            input_hash=input_hash,
            output_summary=output_summary,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
        )
    
    def log_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        cost_usd: float,
        purpose: str,
        actor: Optional[str] = None,
    ) -> AuditEntry:
        """
        Log LLM API call per FDE Playbook LLM Controls.
        
        Tracks: model, tokens, latency, cost for observability.
        """
        return self.log_operation(
            operation="llm_call",
            actor=actor,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            purpose=purpose,
        )
    
    def verify_chain(self) -> dict:
        """
        Verify integrity of audit chain.
        
        Returns:
            Verification result with any integrity failures.
        """
        failures = []
        
        for i, entry in enumerate(AuditLogger._global_chain):
            # Verify hash computation
            expected_hash = entry._compute_hash()
            if entry.hash != expected_hash:
                failures.append({
                    "entry_id": entry.entry_id,
                    "error": "hash_mismatch",
                    "position": i,
                })
            
            # Verify chain linkage
            if i > 0:
                expected_prev = AuditLogger._global_chain[i - 1].hash
                if entry.previous_hash != expected_prev:
                    failures.append({
                        "entry_id": entry.entry_id,
                        "error": "chain_break",
                        "position": i,
                    })
        
        return {
            "verified": len(failures) == 0,
            "entries_checked": len(AuditLogger._global_chain),
            "failures": failures,
            "verified_at": datetime.utcnow().isoformat(),
        }
    
    def get_entries(
        self,
        component: Optional[str] = None,
        operation: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Query audit entries with filters.
        
        Args:
            component: Filter by component
            operation: Filter by operation type
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum entries to return
        
        Returns:
            List of matching audit entries
        """
        entries = AuditLogger._global_chain
        
        if component:
            entries = [e for e in entries if e.component == component]
        if operation:
            entries = [e for e in entries if e.operation == operation]
        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]
        if end_time:
            entries = [e for e in entries if e.timestamp <= end_time]
        
        return [e.to_dict() for e in entries[-limit:]]
    
    def get_audit_summary(self) -> dict:
        """Get summary statistics of audit log."""
        entries = AuditLogger._global_chain
        
        if not entries:
            return {
                "total_entries": 0,
                "components": {},
                "operations": {},
            }
        
        # Count by component
        components = {}
        operations = {}
        for entry in entries:
            components[entry.component] = components.get(entry.component, 0) + 1
            operations[entry.operation] = operations.get(entry.operation, 0) + 1
        
        return {
            "total_entries": len(entries),
            "first_entry": entries[0].timestamp.isoformat(),
            "last_entry": entries[-1].timestamp.isoformat(),
            "components": components,
            "operations": operations,
            "chain_verified": self.verify_chain()["verified"],
        }


# Global audit logger instance
_default_logger: Optional[AuditLogger] = None


def get_audit_logger(component: str = "default") -> AuditLogger:
    """Get or create audit logger for a component."""
    global _default_logger
    if _default_logger is None:
        _default_logger = AuditLogger(component)
    return AuditLogger(component)
