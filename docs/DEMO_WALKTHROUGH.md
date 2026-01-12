# CoCo Demo Walkthrough

This document explains what the demo script does, what success looks like, and how to troubleshoot common failures.

---

## Quick Start

```bash
# Full demo (includes synthetic data generation)
./scripts/demo.sh

# Quick demo (skip data generation)
./scripts/demo.sh --quick
```

---

## What the Demo Does

The demo executes all three clinical workflows end-to-end:

| Step | Workflow | Endpoint | What It Proves |
|------|----------|----------|----------------|
| 1-2 | Setup | - | Docker services start and pass health checks |
| 3 | Data Generation | - | FHIR-compliant synthetic patients created |
| 4 | Care Gap Detection | `/api/v1/care-gaps/patient/{id}` | Rules engine identifies preventive care gaps |
| 5 | Readmission Risk | `/api/v1/readmission/predict/{id}` | ML model returns risk score + SHAP factors |
| 6 | Summarization | `/api/v1/summarize/patient/{id}` | RAG pipeline generates cited summary |
| 7 | Governance | `/api/v1/governance/status` | Phase gates and cost telemetry operational |
| 8 | Audit | `/api/v1/audit/verify` | Hash chain integrity verified |

---

## Expected Output

### Care Gap Detection

```json
{
  "patient_id": "P12345678",
  "gaps_identified": 3,
  "gaps": [
    {
      "gap_type": "screening",
      "gap_name": "Colorectal Cancer Screening",
      "guideline_source": "USPSTF",
      "priority": "high",
      "recommendation": "Schedule colonoscopy - patient is 52, last screening >10 years ago",
      "due_date": "2024-03-01"
    },
    {
      "gap_type": "immunization",
      "gap_name": "Influenza Vaccine",
      "guideline_source": "ACIP",
      "priority": "medium",
      "recommendation": "Annual flu shot due",
      "due_date": "2024-10-01"
    }
  ],
  "audit_id": "aud_abc123",
  "computed_at": "2024-12-01T10:30:00Z"
}
```

**Success criteria:**
- Response contains `patient_id`
- `gaps` array is present (may be empty for healthy patients)
- `audit_id` is present (proves audit logging works)

### Readmission Risk Prediction

```json
{
  "patient_id": "P12345678",
  "encounter_id": "E98765",
  "risk_score": 0.34,
  "risk_tier": "moderate",
  "confidence_interval": {
    "lower": 0.28,
    "upper": 0.41
  },
  "contributing_factors": [
    {
      "feature": "prior_admissions_12m",
      "value": 2,
      "shap_contribution": 0.142
    },
    {
      "feature": "length_of_stay",
      "value": 7,
      "shap_contribution": 0.098
    },
    {
      "feature": "charlson_comorbidity_index",
      "value": 4,
      "shap_contribution": 0.087
    }
  ],
  "recommended_interventions": [
    "Schedule 48-hour post-discharge call",
    "Arrange home health visit within 7 days"
  ],
  "model_version": "readmission_risk_v2.1.0",
  "audit_id": "aud_def456"
}
```

**Success criteria:**
- `risk_score` is between 0.0 and 1.0
- `risk_tier` is one of: `low`, `moderate`, `high`, `critical`
- `contributing_factors` array has SHAP values
- `model_version` is present (proves model governance)

### Clinical Summarization

```json
{
  "patient_id": "P12345678",
  "summary_type": "discharge",
  "time_range": "last_admission",
  "summary": "62-year-old male admitted for CHF exacerbation. Treated with IV diuretics with good response. Echo showed EF 35%. Discharged on optimized heart failure regimen.",
  "key_findings": [
    "CHF exacerbation",
    "EF 35% on echo",
    "Responded to IV diuretics"
  ],
  "citations": [
    {
      "claim": "EF 35% on echo",
      "source_document": "Echo Report 2024-11-28",
      "confidence": 0.94
    }
  ],
  "phi_audit": {
    "phi_detected": false,
    "scan_timestamp": "2024-12-01T10:31:00Z"
  },
  "rag_metrics": {
    "documents_retrieved": 12,
    "documents_used": 5,
    "avg_relevance_score": 0.87
  },
  "audit_id": "aud_ghi789"
}
```

**Success criteria:**
- `summary` is present and non-empty
- `citations` array links claims to sources
- `phi_audit.phi_detected` is `false` (proves PHI scrubbing)
- `rag_metrics` shows retrieval worked

### Governance Status

```json
{
  "playbook_version": "v7.5",
  "current_phase": 11,
  "current_phase_name": "Reliability",
  "phases_completed": 10,
  "total_phases": 12,
  "cost_telemetry": {
    "contract_id": "CT-1",
    "status": "healthy",
    "roi": 65.2,
    "cost_per_inference_usd": 0.0023
  },
  "kill_criteria": {
    "any_triggered": false,
    "triggers_checked": 5
  }
}
```

**Success criteria:**
- `phases_completed` ≥ 10
- `cost_telemetry.status` is `healthy`
- `kill_criteria.any_triggered` is `false`

### Audit Verification

```json
{
  "valid": true,
  "events_verified": 47,
  "chain_head": "a3f8c9d2e1b4...",
  "verified_at": "2024-12-01T10:32:00Z"
}
```

**Success criteria:**
- `valid` is `true`
- `events_verified` > 0
- `chain_head` is a valid SHA-256 prefix

---

## Common Failure Modes

### 1. API Not Starting

**Symptom:**
```
[ERROR] API failed to start after 30 attempts
```

**Causes:**
- Port 8000 already in use
- Docker not running
- Missing environment variables

**Fix:**
```bash
# Check what's using port 8000
lsof -i :8000

# Restart Docker
docker compose down
docker compose up -d

# Check logs
docker compose logs coco-api
```

### 2. Database Connection Failed

**Symptom:**
```json
{"detail": "Database connection failed"}
```

**Causes:**
- PostgreSQL container not ready
- Wrong connection string

**Fix:**
```bash
# Check PostgreSQL status
docker compose logs postgres

# Wait for healthy
docker compose exec postgres pg_isready
```

### 3. Model Not Found

**Symptom:**
```json
{"detail": "Model 'readmission_risk_v2.1.0' not found"}
```

**Causes:**
- MLflow not initialized
- Model not registered

**Fix:**
```bash
# Check MLflow
curl http://localhost:5000/health

# Register models
python scripts/register_models.py
```

### 4. RAG Retrieval Empty

**Symptom:**
```json
{
  "rag_metrics": {
    "documents_retrieved": 0
  }
}
```

**Causes:**
- Qdrant not running
- No documents indexed

**Fix:**
```bash
# Check Qdrant
curl http://localhost:6333/health

# Index documents
python scripts/index_documents.py
```

### 5. Audit Chain Invalid

**Symptom:**
```json
{
  "valid": false,
  "error": "Chain broken at event 23"
}
```

**Causes:**
- Database corruption
- Manual event modification (forbidden)

**Fix:**
```bash
# This should never happen in production
# Investigate before proceeding
docker compose logs coco-api | grep audit
```

---

## Verifying Success

Run the verification script:

```bash
python -c "
import requests
import sys

endpoints = [
    ('Health', 'http://localhost:8000/health'),
    ('Care Gaps', 'http://localhost:8000/api/v1/care-gaps/patient/P12345678'),
    ('Readmission', 'http://localhost:8000/api/v1/readmission/predict/P12345678'),
    ('Summarize', 'http://localhost:8000/api/v1/summarize/patient/P12345678'),
]

all_pass = True
for name, url in endpoints:
    try:
        r = requests.get(url, timeout=10)
        status = '✓' if r.status_code == 200 else '✗'
        print(f'{status} {name}: {r.status_code}')
        if r.status_code != 200:
            all_pass = False
    except Exception as e:
        print(f'✗ {name}: {e}')
        all_pass = False

sys.exit(0 if all_pass else 1)
"
```

---

## Next Steps After Demo

1. **Explore Dashboards**: Open Grafana at http://localhost:3000
2. **View Traces**: Check Jaeger at http://localhost:16686
3. **Inspect Models**: Browse MLflow at http://localhost:5000
4. **Run Tests**: `pytest tests/ -v`
5. **Read the Runbook**: `cat RUNBOOK.md`
