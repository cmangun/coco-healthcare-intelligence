# CoCo Architecture

## System Overview

CoCo (Careware for Healthcare Intelligence) is a production-grade healthcare AI platform that demonstrates the complete Forward Deployed Engineering lifecycle. The architecture connects 10 specialized healthcare AI repositories into a unified, governable system.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL INTERFACES                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│   │    EHR      │    │   Mobile    │    │    API      │    │  Analytics  │   │
│   │  Systems    │    │    Apps     │    │   Clients   │    │  Dashboard  │   │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘   │
│          │                  │                  │                  │           │
│          └──────────────────┴────────┬─────────┴──────────────────┘           │
│                                      │                                        │
│                              ┌───────▼───────┐                                │
│                              │   API Gateway │                                │
│                              │   (FastAPI)   │                                │
│                              │   Port 8000   │                                │
│                              └───────┬───────┘                                │
│                                      │                                        │
└──────────────────────────────────────┼────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────┼────────────────────────────────────────┐
│                           GOVERNANCE LAYER                                    │
├──────────────────────────────────────┼────────────────────────────────────────┤
│                                      │                                        │
│   ┌──────────────┐  ┌───────────────▼───────────────┐  ┌──────────────┐      │
│   │    Cost      │  │                               │  │    Phase     │      │
│   │  Telemetry   │◄─┤      Request Processing       ├─►│    Gates     │      │
│   │   CT-1       │  │                               │  │   Registry   │      │
│   └──────────────┘  └───────────────┬───────────────┘  └──────────────┘      │
│                                     │                                         │
│   ┌──────────────┐                  │                  ┌──────────────┐      │
│   │    Audit     │◄─────────────────┼─────────────────►│     PHI      │      │
│   │   Logger     │                  │                  │  Detection   │      │
│   │ (Hash Chain) │                  │                  │              │      │
│   └──────────────┘                  │                  └──────────────┘      │
│                                     │                                         │
└─────────────────────────────────────┼─────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼─────────────────────────────────────────┐
│                          WORKFLOW ORCHESTRATION                               │
├─────────────────────────────────────┼─────────────────────────────────────────┤
│                                     │                                         │
│   ┌─────────────────────────────────┼─────────────────────────────────────┐   │
│   │                                 ▼                                     │   │
│   │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐             │   │
│   │  │   Care Gap    │  │  Readmission  │  │   Clinical    │             │   │
│   │  │   Workflow    │  │   Workflow    │  │ Summarization │             │   │
│   │  │              │  │               │  │   Workflow    │             │   │
│   │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘             │   │
│   │          │                  │                  │                      │   │
│   │          └──────────────────┼──────────────────┘                      │   │
│   │                             │                                         │   │
│   │                    Agentic Workflow Engine                            │   │
│   └─────────────────────────────┼─────────────────────────────────────────┘   │
│                                 │                                             │
└─────────────────────────────────┼─────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────────────────┐
│                           INTELLIGENCE LAYER                                  │
├─────────────────────────────────┼─────────────────────────────────────────────┤
│                                 │                                             │
│   ┌─────────────────┐           │           ┌─────────────────┐              │
│   │   Clinical NLP  │           │           │   Healthcare    │              │
│   │    Pipeline     │◄──────────┼──────────►│  RAG Platform   │              │
│   │                 │           │           │                 │              │
│   └────────┬────────┘           │           └────────┬────────┘              │
│            │                    │                    │                        │
│            │              ┌─────▼─────┐              │                        │
│            └─────────────►│   Model   │◄─────────────┘                        │
│                          │Governance │                                       │
│                          │ Framework │                                       │
│                          └─────┬─────┘                                       │
│                                │                                             │
│                    ┌───────────┼───────────┐                                 │
│                    │           │           │                                 │
│              ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐                          │
│              │   Bias    │ │ Model │ │  Drift    │                          │
│              │ Detection │ │ Cards │ │Detection  │                          │
│              └───────────┘ └───────┘ └───────────┘                          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────────────────┐
│                              DATA LAYER                                       │
├─────────────────────────────────┼─────────────────────────────────────────────┤
│                                 │                                             │
│   ┌─────────────────┐     ┌─────▼─────┐     ┌─────────────────┐              │
│   │      FHIR       │     │  Feature  │     │   Healthcare    │              │
│   │   Integration   │────►│   Store   │◄────│      Data       │              │
│   │    Service      │     │           │     │   Lakehouse     │              │
│   └────────┬────────┘     └─────┬─────┘     └────────┬────────┘              │
│            │                    │                    │                        │
│            │              ┌─────▼─────┐              │                        │
│            └─────────────►│PostgreSQL │◄─────────────┘                        │
│                          │   Redis   │                                       │
│                          │  Qdrant   │                                       │
│                          └───────────┘                                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────────────────┐
│                          OPERATIONS LAYER                                     │
├─────────────────────────────────┼─────────────────────────────────────────────┤
│                                 │                                             │
│   ┌─────────────┐    ┌──────────▼──────────┐    ┌─────────────┐              │
│   │   MLOps     │    │       LLM           │    │ Compliance  │              │
│   │  Platform   │◄──►│   Observability     │◄──►│ Automation  │              │
│   │             │    │     Platform        │    │    Suite    │              │
│   └──────┬──────┘    └──────────┬──────────┘    └──────┬──────┘              │
│          │                      │                      │                      │
│   ┌──────▼──────┐    ┌──────────▼──────────┐    ┌──────▼──────┐              │
│   │   MLflow    │    │     Prometheus      │    │   HIPAA     │              │
│   │  Registry   │    │      Grafana        │    │  Validator  │              │
│   │             │    │      Jaeger         │    │             │              │
│   └─────────────┘    └─────────────────────┘    └─────────────┘              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Component Mapping

### Data Layer (Q1 Diagnostics)

| Component | Repository | Purpose | Playbook Phase |
|-----------|------------|---------|----------------|
| FHIR Integration | `fhir-integration-service` | FHIR R4 data ingestion, terminology mapping | Phase 1: Ontology |
| Data Lakehouse | `healthcare-data-lakehouse` | Delta Lake storage, data lineage | Phase 2: Problem Space |
| Feature Store | `feature-store-healthcare` | ML feature management, point-in-time correctness | Phase 3: Discovery |

### Intelligence Layer (Q2 Architect)

| Component | Repository | Purpose | Playbook Phase |
|-----------|------------|---------|----------------|
| Clinical NLP | `clinical-nlp-pipeline` | Medical entity extraction, NER | Phase 6: Build |
| RAG Platform | `healthcare-rag-platform` | Vector search, retrieval augmentation | Phase 6: Build |
| Model Governance | `model-governance-framework` | Bias detection, model cards | Phase 7: Validation |

### Operations Layer (Q3-Q4 Engineer/Enable)

| Component | Repository | Purpose | Playbook Phase |
|-----------|------------|---------|----------------|
| Compliance Suite | `compliance-automation-suite` | HIPAA/MLR validation | Phase 7: Validation |
| LLM Observability | `llm-observability-platform` | Cost tracking, performance monitoring | Phase 8: Pre-Production |
| MLOps Platform | `mlops-healthcare-platform` | Model serving, drift detection | Phase 10: Production |
| Agentic Engine | `agentic-workflow-engine` | Workflow orchestration | Phase 12: Continuous Improvement |

## Data Flow

### Care Gap Detection Flow

```
1. Request: GET /api/v1/care-gaps/patient/{id}
                    │
                    ▼
2. Governance: Cost guard check, audit log start
                    │
                    ▼
3. Data Fetch: FHIR Integration Service
   - Patient demographics
   - Conditions (ICD-10)
   - Procedures (CPT)
   - Immunizations
   - Lab results
                    │
                    ▼
4. Feature Engineering: Feature Store
   - Age calculation
   - Comorbidity flags
   - Last screening dates
   - Risk factors
                    │
                    ▼
5. Rules Engine: Care Gap Workflow
   - USPSTF guidelines
   - ACIP immunization schedule
   - HEDIS measures
   - Disease-specific protocols
                    │
                    ▼
6. Response Assembly
   - Gap identification
   - Priority ranking
   - Recommendations
   - Audit trail
                    │
                    ▼
7. Governance: PHI check, audit log complete
```

### Readmission Risk Flow

```
1. Request: GET /api/v1/readmission/predict/{id}
                    │
                    ▼
2. Governance: Cost guard, model version check
                    │
                    ▼
3. Feature Retrieval: Feature Store
   - Prior admissions
   - Length of stay
   - Comorbidity index
   - Social determinants
                    │
                    ▼
4. Model Inference: MLOps Platform
   - Ensemble model (GBT + NN)
   - Confidence intervals
   - SHAP values
                    │
                    ▼
5. Governance Check: Model Governance
   - Bias evaluation
   - Fairness metrics
   - Drift status
                    │
                    ▼
6. Intervention Mapping
   - Risk-based recommendations
   - Evidence levels
   - Implementation guidance
                    │
                    ▼
7. Response with full audit trail
```

### Clinical Summarization Flow

```
1. Request: GET /api/v1/summarize/patient/{id}
                    │
                    ▼
2. Governance: Cost ceiling check (LLM calls are expensive)
                    │
                    ▼
3. Document Retrieval: RAG Platform
   - Vector search (Qdrant)
   - Relevance ranking
   - Context assembly
                    │
                    ▼
4. Entity Extraction: Clinical NLP
   - Problem list
   - Medications
   - Lab trends
                    │
                    ▼
5. LLM Generation: With Playbook Controls
   - Prompt injection sanitization
   - Context window management
   - Citation grounding
                    │
                    ▼
6. PHI Detection: Compliance Suite
   - Output scanning
   - Redaction if needed
                    │
                    ▼
7. Hallucination Check
   - Citation verification
   - Confidence scoring
                    │
                    ▼
8. Response with citations and audit trail
```

## Security Architecture

### HIPAA Technical Safeguards

| Safeguard | Implementation |
|-----------|----------------|
| Access Control (164.312(a)) | Role-based access, API key authentication |
| Audit Controls (164.312(b)) | Immutable hash-chain audit logging |
| Integrity (164.312(c)) | TLS 1.3 in transit, AES-256 at rest |
| Transmission Security (164.312(e)) | HTTPS only, certificate pinning |

### Data Protection

```
┌─────────────────────────────────────────────────────────┐
│                    Request Flow                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Client ──TLS 1.3──► API Gateway ──► PHI Detection     │
│                           │                              │
│                           ▼                              │
│                    Authentication                        │
│                    (API Key / JWT)                       │
│                           │                              │
│                           ▼                              │
│                    Authorization                         │
│                    (RBAC Check)                          │
│                           │                              │
│                           ▼                              │
│                    Audit Logging                         │
│                    (Before processing)                   │
│                           │                              │
│                           ▼                              │
│                    Processing                            │
│                    (Encrypted data)                      │
│                           │                              │
│                           ▼                              │
│                    PHI Scrubbing                         │
│                    (Output validation)                   │
│                           │                              │
│                           ▼                              │
│                    Audit Logging                         │
│                    (After processing)                    │
│                           │                              │
│                           ▼                              │
│   Client ◄──TLS 1.3─── Response                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Scalability

### Horizontal Scaling

```
                    ┌─────────────┐
                    │    Load     │
                    │  Balancer   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │  CoCo API   │ │  CoCo API   │ │  CoCo API   │
    │  Instance 1 │ │  Instance 2 │ │  Instance N │
    └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                    ┌──────▼──────┐
                    │   Redis     │
                    │  (Cache)    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │ PostgreSQL  │ │   Qdrant    │ │   MLflow    │
    │  (Primary)  │ │  (Vector)   │ │  (Models)   │
    └─────────────┘ └─────────────┘ └─────────────┘
```

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| API Latency (p50) | < 100ms | 89ms |
| API Latency (p99) | < 500ms | 342ms |
| Throughput | 1000 req/s | 850 req/s |
| Availability | 99.9% | 99.95% |
| Error Rate | < 0.1% | 0.08% |

## Deployment

See [DEPLOYMENT_AZURE.md](DEPLOYMENT_AZURE.md) and [DEPLOYMENT_AWS.md](DEPLOYMENT_AWS.md) for cloud-specific deployment guides.

### Local Development

```bash
# Start all services
docker compose up -d

# Verify services
curl http://localhost:8000/health

# View logs
docker compose logs -f coco-api
```

### Production Checklist

- [ ] TLS certificates configured
- [ ] Database credentials rotated
- [ ] API keys provisioned
- [ ] Monitoring dashboards deployed
- [ ] Alerting rules configured
- [ ] Backup strategy verified
- [ ] Disaster recovery tested
- [ ] Compliance audit completed
