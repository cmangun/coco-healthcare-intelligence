# FDA ML/AI Change Control Framework

This document outlines the change control process for ML models in CoCo, aligned with FDA guidance on AI/ML-based Software as a Medical Device (SaMD).

---

## Regulatory Context

### Applicable Guidance
- FDA: Artificial Intelligence and Machine Learning in Software as a Medical Device (2021)
- FDA: Predetermined Change Control Plan (PCCP) Draft Guidance (2023)
- FDA: 21 CFR Part 11 (Electronic Records)
- FDA: 21 CFR Part 820 (Quality System Regulation)

### Risk Classification

| CoCo Component | SaMD Category | Risk Level | Rationale |
|----------------|---------------|------------|-----------|
| Care Gap Detection | IIa | Medium | Clinical decision support, not direct diagnosis |
| Readmission Risk | IIa | Medium | Risk stratification, provider review required |
| Clinical Summarization | I | Low | Information display, no clinical recommendation |

---

## Predetermined Change Control Plan (PCCP)

### Covered Changes (Pre-Authorized)

These changes do NOT require new regulatory submission:

| Change Type | Scope | Conditions | Documentation |
|-------------|-------|------------|---------------|
| Performance Improvement | AUC improvement ≤ 5% | Same intended use, no new risks | Model card update |
| Retraining on New Data | Same feature set | Distribution shift < 10% PSI | Drift report |
| Hyperparameter Tuning | Existing model architecture | Performance within spec | Training log |
| Bug Fixes | Non-algorithmic | No change to outputs | Release notes |

### Excluded Changes (Require Submission)

These changes require regulatory notification or submission:

| Change Type | Why Excluded | Required Action |
|-------------|--------------|-----------------|
| New Intended Use | Expands clinical scope | 510(k) or De Novo |
| New Patient Population | Different risk profile | Supplement |
| Architecture Change | Algorithm fundamentally different | New validation |
| New Risk Introduced | Safety profile changed | Hazard analysis |

---

## Model Change Control Process

### 1. Change Request

```
┌─────────────────────────────────────────────────────────────┐
│                    CHANGE REQUEST FORM                       │
├─────────────────────────────────────────────────────────────┤
│ CR-ID: CR-2024-XXX                                          │
│ Model: [readmission_risk_v2.1.0]                            │
│ Requested By: [Name]                                        │
│ Date: [YYYY-MM-DD]                                          │
├─────────────────────────────────────────────────────────────┤
│ CHANGE DESCRIPTION                                          │
│ [Describe the proposed change]                              │
├─────────────────────────────────────────────────────────────┤
│ CHANGE TYPE                                                 │
│ [ ] Performance Improvement                                 │
│ [ ] Retraining                                              │
│ [ ] Bug Fix                                                 │
│ [ ] New Feature                                             │
│ [ ] Architecture Change                                     │
├─────────────────────────────────────────────────────────────┤
│ PCCP ELIGIBILITY                                            │
│ [ ] Covered by PCCP (pre-authorized)                        │
│ [ ] Not covered (requires regulatory review)                │
├─────────────────────────────────────────────────────────────┤
│ RISK ASSESSMENT                                             │
│ Does this change introduce new risks? [ ] Yes [ ] No        │
│ Does this change affect intended use? [ ] Yes [ ] No        │
│ Does this change affect patient population? [ ] Yes [ ] No  │
└─────────────────────────────────────────────────────────────┘
```

### 2. Impact Assessment

| Assessment Area | Criteria | Pass/Fail |
|-----------------|----------|-----------|
| Performance Bounds | Within ±5% of baseline | |
| Fairness Metrics | No degradation by subgroup | |
| Safety Hazards | No new hazards identified | |
| Intended Use | Unchanged | |
| Input/Output Spec | Compatible with existing | |

### 3. Validation Requirements

#### For PCCP-Covered Changes

| Validation | Requirement | Evidence |
|------------|-------------|----------|
| Unit Tests | 100% pass | CI/CD log |
| Integration Tests | 100% pass | CI/CD log |
| Performance Tests | Within spec | Benchmark report |
| Bias Evaluation | No degradation | Fairness report |
| Regression Tests | No regressions | Test report |

#### For Non-PCCP Changes

All above, plus:
- Clinical validation study
- Hazard analysis update
- Risk management file update
- Regulatory submission preparation

### 4. Approval Workflow

```
Change Request
      │
      ▼
┌─────────────┐
│   QA/RA     │──── Not Covered ──── Regulatory Review
│   Review    │
└──────┬──────┘
       │ Covered
       ▼
┌─────────────┐
│  Technical  │
│   Review    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validation │
│   Testing   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Release   │
│   Approval  │
└──────┬──────┘
       │
       ▼
   Deployment
```

---

## Model Version Control

### Rollback Procedure

If a model change causes performance degradation or safety issues, immediate rollback is required:

| Trigger | Action | Timeline |
|---------|--------|----------|
| Performance below threshold | Automatic rollback to previous version | Immediate |
| Safety signal detected | Manual rollback + investigation | < 4 hours |
| Fairness degradation | Rollback + bias analysis | < 24 hours |
| User-reported issue | Triage + potential rollback | < 48 hours |

**Rollback Steps:**
1. **Detect**: Monitoring alerts or user reports trigger investigation
2. **Assess**: Confirm issue is model-related (not data or infrastructure)
3. **Revert**: Deploy previous known-good model version from MLflow Registry
4. **Verify**: Confirm rollback successful via health checks
5. **Document**: Create incident report with root cause analysis
6. **Prevent**: Update test suite to catch similar issues

**Rollback Commands:**
```bash
# Automatic rollback (triggered by monitoring)
coco model rollback --to-version <previous_version> --reason "performance_regression"

# Manual rollback (operator-initiated)
coco model rollback --to-version <version> --reason "safety_concern" --operator <name>
```

### Versioning Scheme

```
MAJOR.MINOR.PATCH

MAJOR: Architecture change (requires regulatory review)
MINOR: Retraining or performance improvement (PCCP covered if criteria met)
PATCH: Bug fix (PCCP covered)
```

### Model Card Requirements

Each model version must have an updated model card including:

- Version number and date
- Training data description
- Performance metrics (AUC, sensitivity, specificity)
- Fairness metrics by demographic
- Known limitations
- Change history

### Artifact Retention

| Artifact | Retention Period | Location |
|----------|------------------|----------|
| Model weights | Life of product + 2 years | MLflow Registry |
| Training data reference | Life of product + 2 years | Data catalog |
| Validation reports | Life of product + 2 years | Document management |
| Change requests | Life of product + 2 years | QMS |

---

## Implementation in CoCo

### Model Registry Integration

```python
# coco/governance/model_governance.py

class ModelGovernance:
    def check_change_eligibility(self, old_model, new_model) -> dict:
        """Check if model change is covered by PCCP."""
        checks = {
            "performance_within_bounds": self._check_performance(old_model, new_model),
            "same_architecture": self._check_architecture(old_model, new_model),
            "same_intended_use": self._check_intended_use(old_model, new_model),
            "fairness_preserved": self._check_fairness(old_model, new_model),
            "no_new_risks": self._check_risks(old_model, new_model),
        }
        return {
            "pccp_eligible": all(checks.values()),
            "checks": checks,
        }
```

### Automated Checks in CI/CD

```yaml
# .github/workflows/model-change.yml
- name: PCCP Eligibility Check
  run: python -m coco.governance.check_pccp $OLD_VERSION $NEW_VERSION
  
- name: Performance Bounds Check
  run: python -m coco.governance.check_performance --threshold 0.05

- name: Fairness Evaluation
  run: python -m coco.governance.check_fairness --no-degradation
```

---

## References

- [FDA AI/ML SaMD Action Plan](https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-and-machine-learning-software-medical-device)
- [PCCP Draft Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial)
- [IMDRF SaMD Framework](https://www.imdrf.org/documents/software-medical-device-samd-key-definitions)

---

Last Updated: 2024-12-01  
Document Owner: Regulatory Affairs  
Review Cycle: Annual
