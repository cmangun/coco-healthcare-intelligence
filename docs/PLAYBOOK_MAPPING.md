# CoCo Playbook Mapping

This document maps CoCo's components to the [Forward Deployed Engineering AI Systems Production Playbook](https://enterprise-ai-playbook-demo.vercel.app/).

## Playbook Overview

The FDE Playbook defines a 12-phase methodology for shipping production AI systems:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FDE AI SYSTEMS PRODUCTION PLAYBOOK                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Q1 DIAGNOSTICS              Q2 ARCHITECT                                    │
│  ┌─────┐ ┌─────┐ ┌─────┐    ┌─────┐ ┌─────┐ ┌─────┐                        │
│  │  1  │ │  2  │ │  3  │    │  4  │ │  5  │ │  6  │                        │
│  │Onto-│ │Prob-│ │Disc-│    │Align│ │Integ│ │Build│                        │
│  │logy │ │lem  │ │overy│    │ment │ │rati-│ │     │                        │
│  └──┬──┘ └──┬──┘ └──┬──┘    └──┬──┘ └──┬──┘ └──┬──┘                        │
│     │       │       │          │       │       │                            │
│     ▼       ▼       ▼          ▼       ▼       ▼                            │
│  ┌──────────────────────┐  ┌──────────────────────┐                         │
│  │ Problem & success    │  │ Architecture review   │                        │
│  │ definition locked    │  │ Security/compliance   │                        │
│  │ Baseline approved    │  │ accepted              │                        │
│  └──────────────────────┘  └──────────────────────┘                         │
│                                                                              │
│  Q3 ENGINEER                 Q4 ENABLE                                       │
│  ┌─────┐ ┌─────┐ ┌─────┐    ┌─────┐ ┌─────┐ ┌─────┐                        │
│  │  7  │ │  8  │ │  9  │    │ 10  │ │ 11  │ │ 12  │                        │
│  │Valid│ │Pre- │ │Hyper│    │Prod-│ │Reli-│ │Cont-│                        │
│  │ation│ │Prod │ │care │    │ucti-│ │abil-│ │inuo-│                        │
│  └──┬──┘ └──┬──┘ └──┬──┘    └──┬──┘ └──┬──┘ └──┬──┘                        │
│     │       │       │          │       │       │                            │
│     ▼       ▼       ▼          ▼       ▼       ▼                            │
│  ┌──────────────────────┐  ┌──────────────────────┐                         │
│  │ Validation suite     │  │ Production ready      │                        │
│  │ green; risk controls │  │ Monitoring live       │                        │
│  │ implemented          │  │ Owner assigned        │                        │
│  └──────────────────────┘  └──────────────────────┘                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Repository Mapping

CoCo integrates 10 healthcare AI repositories, each mapped to specific playbook phases:

### Q1: Diagnostics (Phases 1-3)

| Repository | Phase | Playbook Alignment |
|------------|-------|-------------------|
| `fhir-integration-service` | 1: Ontology | FHIR R4 defines the conceptual foundation—Patient, Encounter, Observation entities and their relationships |
| `healthcare-data-lakehouse` | 2: Problem Space | Delta Lake schema defines data boundaries; lineage tracking validates assumptions |

**Phase Exit Contracts:**
- Truth: FHIR schema validated against real EHR exports
- Economic: Data ingestion cost < $0.001/record
- Risk: PHI detection enabled on all data paths
- Ownership: Data Engineer owns schema evolution

### Q2: Architect (Phases 4-6)

| Repository | Phase | Playbook Alignment |
|------------|-------|-------------------|
| `feature-store-healthcare` | 4: Alignment & Design | Feature registry locks stakeholder agreement on what signals matter |
| `clinical-nlp-pipeline` | 6: Build | Entity recognition model with reproducibility proof |
| `healthcare-rag-platform` | 6: Build | RAG pipeline with baseline retrieval metrics |

**Phase Exit Contracts:**
- Truth: Feature definitions approved by clinical SME
- Economic: ROI pack approved (Phase 4 gate)
- Risk: Bias baseline established for clinical models
- Ownership: ML Engineer owns model training

### Q3: Engineer (Phases 7-9)

| Repository | Phase | Playbook Alignment |
|------------|-------|-------------------|
| `compliance-automation-suite` | 7: Validation | HIPAA/MLR validation suite with automated checks |
| `model-governance-framework` | 7: Validation | Bias detection, fairness metrics, model cards |
| `llm-observability-platform` | 8: Pre-Production | Cost telemetry, latency tracking, token accounting |

**Phase Exit Contracts:**
- Truth: Red team report approved
- Economic: Cost telemetry contract signed (CT-1)
- Risk: Pen test findings remediated
- Ownership: Security Engineer owns validation

### Q4: Enable (Phases 10-12)

| Repository | Phase | Playbook Alignment |
|------------|-------|-------------------|
| `mlops-healthcare-platform` | 10: Production | Model registry, deployment automation, scaling |
| `agentic-workflow-engine` | 12: Continuous Improvement | Workflow automation, tool orchestration |

**Phase Exit Contracts:**
- Truth: Autoscaling proof under load
- Economic: ROI validation quarterly
- Risk: Kill drill completed successfully
- Ownership: SRE owns production operations

---

## Clinical Use Case Mapping

### Use Case 1: Care Gap Detection

**Playbook Phases Traversed:**

```
Phase 1 (Ontology) → Phase 4 (Alignment) → Phase 6 (Build) → Phase 10 (Production)
       ↓                    ↓                    ↓                    ↓
   FHIR entities      Clinical guidelines   Rules engine      API deployment
   Patient, Condition  USPSTF, HEDIS        Gap detection     Real-time serving
```

**Components Used:**
- `fhir-integration-service`: Patient data ingestion
- `healthcare-data-lakehouse`: Historical data storage
- `feature-store-healthcare`: Feature retrieval
- `compliance-automation-suite`: HIPAA compliance checks

### Use Case 2: Readmission Risk Prediction

**Playbook Phases Traversed:**

```
Phase 2 (Problem) → Phase 6 (Build) → Phase 7 (Validation) → Phase 11 (Reliability)
       ↓                  ↓                   ↓                      ↓
   Risk definition   ML model training   Bias testing          Drift detection
   30-day readmit    GBT + NN ensemble   Fairness metrics      Auto-retrain
```

**Components Used:**
- `healthcare-data-lakehouse`: Training data
- `feature-store-healthcare`: Real-time features
- `model-governance-framework`: Bias detection, model cards
- `mlops-healthcare-platform`: Model serving, drift monitoring
- `llm-observability-platform`: Performance tracking

### Use Case 3: Clinical Summarization

**Playbook Phases Traversed:**

```
Phase 6 (Build) → Phase 7 (Validation) → Phase 8 (Pre-Prod) → Phase 10 (Production)
       ↓                  ↓                    ↓                     ↓
   RAG pipeline      Hallucination test    PHI detection         API serving
   Vector search     Citation grounding    Output validation     Cost guards
```

**Components Used:**
- `healthcare-rag-platform`: Document retrieval, vector search
- `clinical-nlp-pipeline`: Entity extraction
- `compliance-automation-suite`: PHI detection
- `llm-observability-platform`: LLM cost tracking, token accounting

---

## Governance Controls

### Cost Telemetry Contract (CT-1)

Per Playbook requirements, each cost metric has a named owner:

| Metric | Owner | Refresh | Kill Trigger |
|--------|-------|---------|--------------|
| Cost per inference | Engineering Manager | Daily | >1.0× value for 2 months |
| Error cost per month | Product Manager | Weekly | >$50K/month |
| Human review cost | Operations Lead | Weekly | >30% of inference cost |
| Compute cost per 1K | Platform Engineer | Real-time | >2× baseline for 1 week |
| Retraining cost | ML Engineer | Per event | >1 month of value |

### Kill Criteria

| ID | Trigger | Action | Owner |
|----|---------|--------|-------|
| KILL-001 | Cost > value for 2 months | Sunset review | CTO + CFO |
| KILL-002 | Error cost > $50K/month | Incident review | CTO |
| KILL-003 | Compliance gap | Halt deployment | General Counsel |
| KILL-004 | Accuracy decay > 15% | Retrain/rollback | ML Lead |
| KILL-005 | PHI exposure | System halt | CISO |

### LLM-Specific Controls (Playbook Appendix)

CoCo implements all LLM controls specified in the playbook:

**Phase 6 (Build):**
- ✅ Prompt injection sanitization
- ✅ Tool call audit logging

**Phase 7 (Validation):**
- ✅ Retrieval contamination checks
- ✅ Hallucination detection via citation grounding

**Phase 8 (Pre-Production):**
- ✅ Context window management
- ✅ Output validation with PHI scrubbing

---

## Phase Exit Evidence

### Evidence Pack Structure

Each phase requires an evidence pack for exit approval:

```
evidence/
├── PH1-EVID-1/
│   ├── expert_stakeholder_map.md
│   ├── concept_glossary.json
│   ├── relationship_diagram.mermaid
│   └── contested_concept_log.md
├── PH4-EVID-1/
│   ├── architecture_roi_pack.xlsx
│   ├── stakeholder_signoff_matrix.pdf
│   └── risk_acceptance_docs/
├── PH6-EVID-1/
│   ├── baseline_model_metrics.json
│   ├── telemetry_contract.md
│   └── reproducibility_proof/
└── ...
```

### Audit Trail Requirements

Every operation is logged with:
- Unique ID
- Timestamp
- Component
- Operation type
- Actor
- Details (PHI redacted)
- Hash (chain integrity)

---

## Implementation Status

| Phase | Status | Evidence Pack | Last Review |
|-------|--------|---------------|-------------|
| 1: Ontology | ✅ Complete | PH1-EVID-1 | 2024-01-05 |
| 2: Problem Space | ✅ Complete | PH2-EVID-1 | 2024-01-08 |
| 3: Discovery | ✅ Complete | PH3-EVID-1 | 2024-01-10 |
| 4: Alignment | ✅ Complete | PH4-EVID-1 | 2024-01-12 |
| 5: Integration | ✅ Complete | PH5-EVID-1 | 2024-01-14 |
| 6: Build | ✅ Complete | PH6-EVID-1 | 2024-01-16 |
| 7: Validation | ✅ Complete | PH7-EVID-1 | 2024-01-18 |
| 8: Pre-Production | ✅ Complete | PH8-EVID-1 | 2024-01-20 |
| 9: Hypercare | ✅ Complete | PH9-EVID-1 | 2024-01-22 |
| 10: Production | ✅ Complete | PH10-EVID-1 | 2024-01-24 |
| 11: Reliability | 🔄 In Progress | PH11-EVID-1 | - |
| 12: Continuous Improvement | ⏳ Not Started | - | - |

---

## References

- [FDE AI Systems Production Playbook](https://enterprise-ai-playbook-demo.vercel.app/)
- [GitHub Portfolio](https://github.com/cmangun)
- [Healthcare AI Consultant](https://healthcare-ai-consultant.com)
