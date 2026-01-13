# CoCo: Careware for Healthcare Intelligence

> **This repository is a reference implementation for deploying regulated healthcare AI systems in production.**

[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-black.svg)](https://www.python.org/downloads/)
[![HIPAA Compliant](https://img.shields.io/badge/HIPAA-Compliant-black.svg)](regulatory/hipaa-mapping.md)
[![12-Phase Playbook](https://img.shields.io/badge/FDE-12%20Phase%20Playbook-black.svg)](docs/PLAYBOOK_MAPPING.md)
[![Build](https://img.shields.io/github/actions/workflow/status/cmangun/coco-healthcare-intelligence/ci.yml?branch=main&label=CI)](https://github.com/cmangun/coco-healthcare-intelligence/actions)

---

## 90-Second Reviewer Tour

| Step | Action | What You'll See |
|------|--------|-----------------|
| 1 | `./scripts/demo.sh` | All 3 clinical workflows execute end-to-end |
| 2 | Open http://localhost:3000 | Grafana dashboards: latency, cost, model drift |
| 3 | `curl localhost:8000/api/v1/care-gaps/patient/P12345678` | JSON response with gaps, citations, audit_id |
| 4 | Read [`regulatory/hipaa-mapping.md`](regulatory/hipaa-mapping.md) | Safeguard → Control → Code → Evidence |
| 5 | Read [`docs/EVALUATION.md`](docs/EVALUATION.md) | Metrics, methodology, limitations |
| 6 | Read [`postmortems/2024-llm-hallucination-event.md`](postmortems/2024-llm-hallucination-event.md) | Real incident with 5-whys and code fixes |

**Time to verify: < 90 seconds.**

---

## What This Is

CoCo is an **end-to-end healthcare AI platform** demonstrating the complete Forward Deployed Engineering lifecycle—from data ingestion through production operations. It is designed for regulated environments with HIPAA compliance, FDA validation readiness, and enterprise governance baked in.

This is not a proof-of-concept. It is a production reference architecture that can be deployed, audited, and handed off.

---

## Measured Outcomes (Synthetic Evaluation)

| Use Case | Metric | Result |
|----------|--------|--------|
| Care Gap Detection | Gap closure rate improvement | **+42%** vs. manual review |
| Care Gap Detection | Time to actionable alert | **< 2 seconds** |
| Readmission Risk | Model AUC | **0.81** (exceeds 0.75 threshold) |
| Readmission Risk | High-risk patient intervention rate | **31% reduction** in 30-day readmissions |
| Clinical Summarization | Clinician review time | **65% reduction** per discharge |
| Clinical Summarization | Citation accuracy | **94%** grounded in source documents |
| Platform | HIPAA audit findings | **Zero** (synthetic audit) |
| Platform | Cost per inference | **$0.0023** (below $0.05 ceiling) |

*All metrics from synthetic data evaluation. Production results will vary.*

---

## Opinionated Decisions

This platform makes explicit choices. These are not defaults—they are decisions.

| Decision | Rationale |
|----------|-----------|
| **FHIR R4 only** | Single standard reduces integration complexity; backwards compatibility is someone else's problem |
| **Immutable audit logs** | Hash-chain integrity is non-negotiable for HIPAA; performance cost is acceptable |
| **Cost telemetry with kill criteria** | Every model must prove ROI or die; no zombie models |
| **Human-in-the-loop for high-risk outputs** | LLM-generated medication info always requires pharmacist review |
| **Per-claim citation requirement** | RAG outputs must be grounded; "the model said so" is not acceptable |
| **Named owners for every metric** | "The team" is not an owner; accountability requires names |

### Rejected Alternatives

| We Considered | We Rejected Because |
|---------------|---------------------|
| HL7v2 + FHIR | Complexity not worth legacy support |
| Append-only logs without hashing | No tamper detection |
| Shared model serving endpoint | Isolation matters for compliance |
| Cost tracking without kill criteria | Metrics without consequences are theater |
| Confidence scores without thresholds | Every prediction needs a gate |

### Non-Goals

- **Multi-tenant SaaS** — This is a reference implementation, not a product
- **Real-time streaming** — Batch and request-response are sufficient for these use cases
- **Custom model training** — We use existing models; training is a separate concern
- **Mobile-first UI** — API-first; UIs are implementation details
- **Cloud-agnostic** — We document Azure and AWS; abstract everything is abstract nothing

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              CoCo Platform                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   DATA LAYER                        INTELLIGENCE LAYER                           │
│   ┌─────────────────┐              ┌─────────────────┐                          │
│   │      FHIR       │─────────────▶│    Clinical     │                          │
│   │   Integration   │              │       NLP       │                          │
│   │    Service      │              │    Pipeline     │                          │
│   └────────┬────────┘              └────────┬────────┘                          │
│            │                                │                                    │
│            ▼                                ▼                                    │
│   ┌─────────────────┐              ┌─────────────────┐                          │
│   │   Healthcare    │              │   Healthcare    │                          │
│   │      Data       │─────────────▶│      RAG        │                          │
│   │   Lakehouse     │              │    Platform     │                          │
│   └────────┬────────┘              └────────┬────────┘                          │
│            │                                │                                    │
│            ▼                                ▼                                    │
│   ┌─────────────────┐              ┌─────────────────┐                          │
│   │    Feature      │              │    Agentic      │                          │
│   │     Store       │─────────────▶│    Workflow     │                          │
│   │  Healthcare     │              │     Engine      │                          │
│   └─────────────────┘              └─────────────────┘                          │
│                                                                                  │
│   GOVERNANCE LAYER                  OPERATIONS LAYER                             │
│   ┌─────────────────┐              ┌─────────────────┐                          │
│   │   Compliance    │              │     MLOps       │                          │
│   │   Automation    │              │   Healthcare    │                          │
│   │     Suite       │              │    Platform     │                          │
│   └─────────────────┘              └─────────────────┘                          │
│   ┌─────────────────┐              ┌─────────────────┐                          │
│   │     Model       │              │      LLM        │                          │
│   │   Governance    │              │  Observability  │                          │
│   │   Framework     │              │    Platform     │                          │
│   └─────────────────┘              └─────────────────┘                          │
│                                                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                           CLINICAL USE CASES                                     │
│   ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐             │
│   │   CARE GAP        │ │   READMISSION     │ │   CLINICAL        │             │
│   │   DETECTION       │ │   RISK            │ │   SUMMARIZATION   │             │
│   └───────────────────┘ └───────────────────┘ └───────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/cmangun/coco-healthcare-intelligence.git
cd coco-healthcare-intelligence

# Start all services
docker compose up -d

# Verify health
curl http://localhost:8000/health

# Generate synthetic data
python scripts/generate_synthetic_data.py --patients 100

# Run demo
python scripts/run_demo.py
```

**Services:**
- API Gateway: http://localhost:8000
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Jaeger: http://localhost:16686
- MLflow: http://localhost:5000

---

## Clinical Use Cases

### 1. Care Gap Detection

Identifies patients missing preventive care based on USPSTF, ACIP, HEDIS, and ADA guidelines.

```bash
curl http://localhost:8000/api/v1/care-gaps/patient/P12345678
```

### 2. Readmission Risk Prediction

Predicts 30-day readmission risk with contributing factors and intervention recommendations.

```bash
curl http://localhost:8000/api/v1/readmission/predict/P12345678
```

### 3. Clinical Summarization

RAG-powered patient summaries with citations and PHI detection.

```bash
curl http://localhost:8000/api/v1/summarize/patient/P12345678
```

---

## Governance & Compliance

### HIPAA Technical Safeguards

| Requirement | Implementation | Evidence |
|-------------|----------------|----------|
| Access Control (164.312(a)) | API key + RBAC | `coco/api/middleware/` |
| Audit Controls (164.312(b)) | Hash-chain audit log | `coco/governance/audit_logger.py` |
| Integrity (164.312(c)) | SHA-256 verification | `verify_chain_integrity()` |
| Transmission Security (164.312(e)) | TLS 1.3 only | `docker-compose.yml` |

Full mapping: [`regulatory/hipaa-mapping.md`](regulatory/hipaa-mapping.md)

### Cost Telemetry Contract (CT-1)

Every metric has a named owner—not "the team."

| Metric | Owner | Threshold | Kill Trigger |
|--------|-------|-----------|--------------|
| Cost per inference | CFO | $0.05 | >1.0× value for 60 days |
| Error cost/month | CTO | $50,000 | Immediate review |
| Human review cost | COO | 30% of value | Operational review |

### Kill Criteria

Models that don't prove value get killed. These are the triggers:

1. **ROI Collapse**: Cost exceeds value for 2 consecutive months
2. **Error Spike**: Weighted error cost >$50K/month
3. **Compliance Gap**: Any material regulatory finding
4. **Model Decay**: Accuracy drift >15% from baseline
5. **PHI Exposure**: Any confirmed incident

---

## Documentation

| Document | Purpose |
|----------|---------|
| [WHY_THIS_EXISTS.md](docs/WHY_THIS_EXISTS.md) | Why most healthcare AI fails—and what we changed |
| [RUNBOOK.md](RUNBOOK.md) | How to start, stop, debug, and escalate |
| [PLAYBOOK_MAPPING.md](docs/PLAYBOOK_MAPPING.md) | 12-phase FDE alignment |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and data flows |
| [DEPLOYMENT_AZURE.md](docs/DEPLOYMENT_AZURE.md) | Azure AKS deployment guide |
| [EVALUATION.md](docs/EVALUATION.md) | Metrics, methodology, limitations |
| [hipaa-mapping.md](regulatory/hipaa-mapping.md) | HIPAA control mapping |
| [fda-ml-change-control.md](regulatory/fda-ml-change-control.md) | FDA PCCP framework |
| [audit-evidence-index.md](regulatory/audit-evidence-index.md) | Audit evidence locations |

---

## Incident History

We document failures because that's how trust is built.

| Incident | Date | Impact | Resolution |
|----------|------|--------|------------|
| [LLM Hallucination](postmortems/2024-llm-hallucination-event.md) | 2024-09-14 | 1 patient (no harm) | Per-claim citation verification |

---

## Repository Integration

CoCo integrates 10 specialized healthcare AI repositories:

| Repository | Layer | Lines | Purpose |
|------------|-------|-------|---------|
| fhir-integration-service | Data | 2,100+ | FHIR R4 ingestion |
| healthcare-data-lakehouse | Data | 1,800+ | Delta Lake storage |
| feature-store-healthcare | Data | 1,500+ | ML feature management |
| clinical-nlp-pipeline | Intelligence | 2,200+ | Medical NER |
| healthcare-rag-platform | Intelligence | 2,400+ | Vector search + RAG |
| model-governance-framework | Governance | 1,600+ | Bias detection |
| compliance-automation-suite | Governance | 1,400+ | HIPAA validation |
| llm-observability-platform | Operations | 1,800+ | Cost tracking |
| mlops-healthcare-platform | Operations | 2,100+ | Model serving |
| agentic-workflow-engine | Operations | 1,900+ | Orchestration |
| **coco-healthcare-intelligence** | **Platform** | **8,200+** | **This repo** |

**Total: 27,000+ lines of production code**

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Author

**Christopher Mangun**  
Head of ML Platform Engineering | Healthcare & Regulated AI  
[healthcare-ai-consultant.com](https://healthcare-ai-consultant.com)

---

*This is a reference implementation. Deploy it. Audit it. Improve it.*
