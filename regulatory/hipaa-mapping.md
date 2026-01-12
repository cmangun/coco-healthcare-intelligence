# HIPAA Technical Safeguards Mapping

This document maps HIPAA Security Rule technical safeguards to CoCo implementation controls.

## Overview

CoCo is designed as a HIPAA-compliant healthcare AI platform. This mapping demonstrates how each technical safeguard requirement is addressed in the codebase.

---

## §164.312(a) - Access Control

| Requirement | Control | Implementation | Evidence |
|-------------|---------|----------------|----------|
| §164.312(a)(1) Unique User Identification | API key per user/service | `coco/api/main.py` - API key middleware | `tests/integration/test_auth.py` |
| §164.312(a)(2)(i) Emergency Access | Break-glass procedure with elevated audit | `coco/governance/emergency_access.py` | `docs/RUNBOOK.md` |
| §164.312(a)(2)(ii) Automatic Logoff | Session timeout (15 min idle) | `coco/api/middleware/session.py` | Config: `SESSION_TIMEOUT=900` |
| §164.312(a)(2)(iii) Encryption/Decryption | AES-256 at rest, TLS 1.3 in transit | `docker-compose.yml` TLS config | Certificate pinning enabled |
| §164.312(a)(2)(iv) Unique User Identification | UUID per request, user ID in JWT | `coco/api/main.py` - request ID header | All responses include `X-Request-ID` |

---

## §164.312(b) - Audit Controls

| Requirement | Control | Implementation | Evidence |
|-------------|---------|----------------|----------|
| §164.312(b) Record and examine activity | Immutable hash-chain audit log | `coco/governance/audit_logger.py` | `tests/governance/test_audit.py` |
| PHI access logging | Every PHI access logged with reason | `AuditLogger.log_phi_access()` | Audit export endpoint |
| Model prediction logging | All inferences logged with inputs/outputs | `AuditLogger.log_model_prediction()` | MLflow integration |
| Governance action logging | All approval/rejection decisions logged | `AuditLogger.log_governance_action()` | Phase gate evidence packs |

### Audit Log Schema

```json
{
  "event_id": "uuid",
  "timestamp": "ISO-8601",
  "event_type": "phi_access|model_prediction|governance",
  "component": "care_gaps|readmission|summarization",
  "operation": "string",
  "user_id": "string",
  "patient_id": "uuid",
  "details": {},
  "previous_hash": "sha256",
  "hash": "sha256"
}
```

---

## §164.312(c) - Integrity

| Requirement | Control | Implementation | Evidence |
|-------------|---------|----------------|----------|
| §164.312(c)(1) Protect from improper alteration | Hash chain verification | `AuditLogger.verify_chain_integrity()` | Integrity check in CI/CD |
| §164.312(c)(2) Electronic mechanisms to corroborate | SHA-256 hash per audit event | `AuditEvent._compute_hash()` | Chain verification tests |
| Data integrity at rest | PostgreSQL with checksums | `docker-compose.yml` DB config | `data_checksums=on` |
| Model integrity | Model hash in registry | MLflow model versioning | Model hash in predictions |

### Hash Chain Verification

```python
def verify_chain_integrity(self) -> dict:
    """Verify integrity of the audit chain."""
    for i, event in enumerate(self.chain):
        # Verify hash computation
        if event.hash != event._compute_hash():
            return {"valid": False, "error": "Hash mismatch"}
        # Verify chain linkage
        if i > 0 and event.previous_hash != self.chain[i-1].hash:
            return {"valid": False, "error": "Chain broken"}
    return {"valid": True}
```

---

## §164.312(d) - Person or Entity Authentication

| Requirement | Control | Implementation | Evidence |
|-------------|---------|----------------|----------|
| §164.312(d) Verify identity | API key + JWT validation | `coco/api/middleware/auth.py` | Integration tests |
| Service-to-service auth | mTLS between containers | Docker network config | Certificate chain |
| Admin authentication | MFA required for admin actions | External IdP integration | Azure AD / Okta |

---

## §164.312(e) - Transmission Security

| Requirement | Control | Implementation | Evidence |
|-------------|---------|----------------|----------|
| §164.312(e)(1) Guard against unauthorized access | Network segmentation | Docker network isolation | `docker-compose.yml` networks |
| §164.312(e)(2)(i) Integrity controls | TLS 1.3 with certificate pinning | Nginx/Traefik config | SSL Labs A+ rating |
| §164.312(e)(2)(ii) Encryption | TLS 1.3 for all external traffic | Load balancer config | No plaintext endpoints |

---

## Additional Controls (Beyond Minimum)

| Control | Purpose | Implementation |
|---------|---------|----------------|
| PHI detection in LLM outputs | Prevent accidental exposure | `coco/workflows/summarization_workflow.py` |
| Minimum necessary access | Limit data exposure | Role-based query filtering |
| Audit log export | Support investigations | `AuditLogger.export_for_compliance()` |
| Patient access report | HIPAA §164.528 accounting | `AuditLogger.get_patient_access_report()` |
| Breach notification support | Data for required notifications | Audit log + patient registry |

---

## Evidence Locations

| Category | Location |
|----------|----------|
| Access Control Code | `coco/api/middleware/` |
| Audit Logging Code | `coco/governance/audit_logger.py` |
| Integrity Verification | `coco/governance/audit_logger.py:verify_chain_integrity()` |
| Authentication Tests | `tests/integration/test_auth.py` |
| Encryption Config | `docker-compose.yml`, `config/tls/` |
| Audit Export | `GET /api/v1/audit/export` |

---

## Compliance Attestation

This system has been designed to meet HIPAA Security Rule technical safeguard requirements. Implementation follows:

- **CIS Controls v8** for security baseline
- **NIST SP 800-53** for control framework
- **HITRUST CSF** for healthcare-specific guidance

Last reviewed: 2024-12-01  
Next review: 2025-06-01
