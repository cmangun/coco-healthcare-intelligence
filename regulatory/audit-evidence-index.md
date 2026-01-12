# Audit Evidence Index

This document serves as the central index for all compliance evidence in the CoCo platform. Use this index during audits to quickly locate required evidence.

---

## Quick Reference

| Audit Type | Primary Evidence | Location |
|------------|------------------|----------|
| HIPAA Security | Technical safeguards mapping | `/regulatory/hipaa-mapping.md` |
| HIPAA Privacy | Access logs, minimum necessary | `/api/v1/audit/export` |
| FDA SaMD | Model change control | `/regulatory/fda-ml-change-control.md` |
| SOC 2 Type II | Control effectiveness | This document |
| Internal Audit | Phase gate evidence | `/docs/PLAYBOOK_MAPPING.md` |

---

## Evidence by Control Domain

### 1. Access Control (AC)

| Control ID | Control Name | Evidence Type | Location | Frequency |
|------------|--------------|---------------|----------|-----------|
| AC-001 | User Authentication | API key validation logs | Audit log: `event_type=authentication` | Real-time |
| AC-002 | Role-Based Access | Permission matrix | `coco/api/middleware/rbac.py` | On change |
| AC-003 | Session Management | Session timeout config | `config/session.yml` | On change |
| AC-004 | Emergency Access | Break-glass audit trail | Audit log: `event_type=emergency_access` | Per event |

### 2. Audit Logging (AU)

| Control ID | Control Name | Evidence Type | Location | Frequency |
|------------|--------------|---------------|----------|-----------|
| AU-001 | PHI Access Logging | Audit events | `GET /api/v1/audit/export?event_type=phi_access` | Real-time |
| AU-002 | Model Prediction Logging | Inference records | `GET /api/v1/audit/export?event_type=model_prediction` | Real-time |
| AU-003 | Chain Integrity | Verification report | `GET /api/v1/audit/verify` | Daily |
| AU-004 | Log Retention | Backup confirmation | Infrastructure logs | Monthly |

### 3. Data Integrity (DI)

| Control ID | Control Name | Evidence Type | Location | Frequency |
|------------|--------------|---------------|----------|-----------|
| DI-001 | Hash Chain Verification | Integrity check | `coco/governance/audit_logger.py:verify_chain_integrity()` | Continuous |
| DI-002 | Database Checksums | PostgreSQL config | `docker-compose.yml` | On deploy |
| DI-003 | Model Hash Verification | MLflow registry | Model artifacts | Per model |
| DI-004 | Data Lineage | Lineage graph | Feature store metadata | Per pipeline |

### 4. Transmission Security (TS)

| Control ID | Control Name | Evidence Type | Location | Frequency |
|------------|--------------|---------------|----------|-----------|
| TS-001 | TLS Configuration | SSL Labs report | External scan | Monthly |
| TS-002 | Certificate Management | Cert inventory | `config/tls/` | Quarterly |
| TS-003 | Network Segmentation | Network diagram | `docs/ARCHITECTURE.md` | On change |
| TS-004 | API Gateway Security | WAF logs | Infrastructure logs | Real-time |

### 5. Model Governance (MG)

| Control ID | Control Name | Evidence Type | Location | Frequency |
|------------|--------------|---------------|----------|-----------|
| MG-001 | Model Registration | MLflow registry | `mlflow.yourdomain.com` | Per model |
| MG-002 | Bias Evaluation | Fairness report | Model card | Per version |
| MG-003 | Drift Detection | PSI scores | Monitoring dashboard | Daily |
| MG-004 | Change Control | CR documentation | QMS | Per change |
| MG-005 | Kill Criteria | Threshold status | `GET /api/v1/governance/kill-criteria` | Real-time |

### 6. Incident Response (IR)

| Control ID | Control Name | Evidence Type | Location | Frequency |
|------------|--------------|---------------|----------|-----------|
| IR-001 | Incident Documentation | Postmortem | `/postmortems/` | Per incident |
| IR-002 | Response Time | MTTR metrics | Monitoring dashboard | Per incident |
| IR-003 | Escalation Procedures | Runbook | `RUNBOOK.md` | On change |
| IR-004 | Root Cause Analysis | 5 Whys documentation | Postmortem | Per incident |

---

## Evidence Collection Procedures

### For HIPAA Audits

1. Export audit logs for date range:
   ```bash
   curl -X GET "https://api.coco.example.com/api/v1/audit/export?start_date=2024-01-01&end_date=2024-12-31" \
     -H "Authorization: Bearer $AUDIT_TOKEN" > hipaa_audit_export.json
   ```

2. Verify chain integrity:
   ```bash
   curl -X GET "https://api.coco.example.com/api/v1/audit/verify" \
     -H "Authorization: Bearer $AUDIT_TOKEN"
   ```

3. Generate patient access report:
   ```bash
   curl -X GET "https://api.coco.example.com/api/v1/audit/patient/{patient_id}" \
     -H "Authorization: Bearer $AUDIT_TOKEN"
   ```

### For FDA Audits

1. Export model change history:
   ```bash
   mlflow experiments search --filter "attribute.lifecycle_stage = 'production'"
   ```

2. Retrieve model card:
   ```bash
   mlflow models get-details -m "models:/readmission_risk/production"
   ```

3. Export validation reports:
   - Located in QMS under model version folder

### For SOC 2 Audits

1. Generate control effectiveness report:
   ```python
   from coco.governance import generate_soc2_report
   report = generate_soc2_report(
       start_date="2024-01-01",
       end_date="2024-12-31",
       controls=["AC", "AU", "DI", "TS", "MG", "IR"]
   )
   ```

2. Export system logs from infrastructure provider

3. Collect penetration test results from security team

---

## Evidence Retention Schedule

| Evidence Type | Retention Period | Storage Location | Destruction Method |
|---------------|------------------|------------------|-------------------|
| Audit Logs | 7 years | Encrypted cold storage | Secure deletion |
| Model Artifacts | Life of product + 2 years | MLflow + backup | Secure deletion |
| Incident Reports | 7 years | Document management | Secure deletion |
| Change Requests | Life of product + 2 years | QMS | Secure deletion |
| Training Data References | Life of product + 2 years | Data catalog | Secure deletion |
| Penetration Test Reports | 3 years | Security team vault | Secure deletion |

---

## Audit Preparation Checklist

### 30 Days Before Audit

- [ ] Confirm audit scope and date
- [ ] Identify evidence custodians
- [ ] Review previous audit findings
- [ ] Verify evidence accessibility

### 14 Days Before Audit

- [ ] Pre-pull all required evidence
- [ ] Verify chain integrity for audit period
- [ ] Prepare system access for auditors
- [ ] Brief relevant team members

### Day of Audit

- [ ] Confirm auditor credentials
- [ ] Provide secure workspace
- [ ] Assign escort for facility access
- [ ] Have evidence index available

### Post-Audit

- [ ] Document findings
- [ ] Create remediation plan
- [ ] Track remediation to closure
- [ ] Update controls as needed

---

## Contact Information

| Role | Name | Contact |
|------|------|---------|
| Compliance Officer | [Name] | compliance@example.com |
| Security Officer | [Name] | security@example.com |
| ML Platform Lead | [Name] | mlplatform@example.com |
| Legal Counsel | [Name] | legal@example.com |

---

Last Updated: 2024-12-01  
Document Owner: Compliance  
Review Cycle: Quarterly
