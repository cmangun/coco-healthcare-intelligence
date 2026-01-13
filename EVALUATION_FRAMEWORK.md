# CoCo Repository Evaluation Framework

## Purpose

This document provides a structured evaluation framework for validating the CoCo Healthcare Intelligence repository. It is designed to be executed by an LLM, automated CI system, or human reviewer.

**Target Score:** 100/100 Healthcare AI Forward-Deployed Engineer Portfolio

---

## Evaluation Instructions

For each section:
1. **Existence Check**: Verify the file/content exists
2. **Quality Check**: Evaluate against the rubric
3. **Score**: Assign points based on criteria
4. **Evidence**: Quote specific content that justifies the score

Report format:
```
## [Section Name]
- Existence: ✅/❌
- Quality Score: X/Y
- Evidence: [quoted content or file excerpt]
- Notes: [any issues or observations]
```

---

## SECTION 1: Repository Structure (10 points)

### 1.1 Core Files Exist (5 points)

Check that these files exist at the specified paths:

| File | Path | Points |
|------|------|--------|
| README | `README.md` | 1 |
| Runbook | `RUNBOOK.md` | 1 |
| Security Policy | `SECURITY.md` | 1 |
| Threat Model | `THREAT_MODEL.md` | 1 |
| Docker Compose | `docker-compose.yml` | 1 |

**Scoring:** 1 point per file that exists.

### 1.2 Directory Structure (5 points)

Check that these directories exist and contain files:

| Directory | Required Contents | Points |
|-----------|-------------------|--------|
| `.github/workflows/` | At least 1 `.yml` file | 1 |
| `coco/api/` | `main.py` + router files | 1 |
| `coco/governance/` | At least 2 `.py` files | 1 |
| `coco/workflows/` | At least 3 workflow files | 1 |
| `tests/` | At least 2 test files | 1 |

**Scoring:** 1 point per directory with correct contents.

---

## SECTION 2: Clinical Workflows (15 points)

### 2.1 Care Gap Detection (5 points)

**File:** `coco/workflows/care_gap_workflow.py`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| References clinical guidelines (USPSTF/HEDIS/ACIP) | 1 | Search for guideline names in code/comments |
| Has typed input/output models | 1 | Look for Pydantic models or type hints |
| Includes audit logging call | 1 | Search for audit/log function calls |
| Has docstring explaining clinical purpose | 1 | Check for module/function docstrings |

### 2.2 Readmission Risk (5 points)

**File:** `coco/workflows/readmission_workflow.py`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Returns risk score (0-1 range) | 1 | Look for score calculation/normalization |
| Includes contributing factors/SHAP | 1 | Search for "factor", "shap", "contribution" |
| Has model version tracking | 1 | Look for version string or model registry call |
| Includes confidence interval | 1 | Search for "confidence", "interval", "uncertainty" |

### 2.3 Clinical Summarization (5 points)

**File:** `coco/workflows/summarization_workflow.py`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Implements RAG pattern | 1 | Look for retrieval + generation flow |
| Includes citation tracking | 1 | Search for "citation", "source", "reference" |
| Has PHI detection/filtering | 1 | Search for "phi", "pii", "redact", "filter" |
| Includes hallucination mitigation | 1 | Search for "hallucination", "grounding", "verify" |

---

## SECTION 3: Governance Framework (15 points)

### 3.1 Phase Gates (5 points)

**File:** `coco/governance/phase_gates.py`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Defines multiple phases (8+) | 1 | Count phase definitions |
| Has exit criteria per phase | 1 | Look for criteria/requirements per phase |
| Includes kill criteria | 1 | Search for "kill", "abort", "stop" criteria |
| Has named owner concept | 1 | Search for "owner", "responsible", "accountable" |

### 3.2 Cost Telemetry (5 points)

**File:** `coco/governance/cost_telemetry.py`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Tracks cost per inference | 1 | Look for cost calculation logic |
| Has cost ceiling/threshold | 1 | Search for "ceiling", "threshold", "limit" |
| Calculates ROI | 1 | Search for "roi", "return", "value" |
| Exports metrics (Prometheus format) | 1 | Look for metric export/gauge/counter |

### 3.3 Audit Logging (5 points)

**File:** `coco/governance/audit_logger.py`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Implements hash chain | 1 | Search for "hash", "chain", "previous" |
| Logs PHI access with reason | 1 | Look for access logging with justification |
| Is append-only/immutable | 1 | Look for immutability enforcement |
| Includes verification method | 1 | Search for "verify", "validate", "integrity" |

---

## SECTION 4: Regulatory Documentation (15 points)

### 4.1 HIPAA Mapping (5 points)

**File:** `regulatory/hipaa-mapping.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Maps to §164.312 safeguards | 1 | Look for specific CFR citations |
| Has 4-column table (Requirement→Control→Implementation→Evidence) | 1 | Verify table structure |
| Links to code files | 1 | Check for file path references |
| Covers all 5 technical safeguards | 1 | Access, Audit, Integrity, Auth, Transmission |

### 4.2 FDA Change Control (5 points)

**File:** `regulatory/fda-ml-change-control.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| References FDA AI/ML guidance | 1 | Look for FDA guidance citations |
| Defines allowed vs. excluded changes | 1 | Check for change categorization |
| Includes validation requirements | 1 | Look for validation/testing requirements |
| Has rollback procedure | 1 | Search for "rollback", "revert", "previous version" |

### 4.3 Audit Evidence Index (5 points)

**File:** `regulatory/audit-evidence-index.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Organizes by control domain | 1 | Look for categorized sections |
| Links to specific evidence locations | 1 | Check for file paths, test names |
| Covers multiple audit types (HIPAA, FDA, SOC2) | 1 | Look for different audit categories |
| Includes retention schedule | 1 | Search for retention periods |

---

## SECTION 5: Operational Readiness (15 points)

### 5.1 Runbook (5 points)

**File:** `RUNBOOK.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Has start/stop procedures | 1 | Look for startup and shutdown sections |
| Has debugging guide | 1 | Look for troubleshooting/debug section |
| Defines severity levels and escalation | 1 | Search for P1/P2/P3 or severity definitions |
| Has "what not to change" section | 1 | Look for anti-patterns or forbidden changes |

### 5.2 Demo Script (5 points)

**File:** `scripts/demo.sh`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists and is executable | 1 | Check file exists with execute permission |
| Starts services | 1 | Look for docker compose or service start |
| Runs all 3 workflows | 1 | Check for care gap, readmission, summarization calls |
| Prints JSON output | 1 | Look for curl commands with output |
| Has success/failure indicators | 1 | Look for colored output or status messages |

### 5.3 Demo Walkthrough (5 points)

**File:** `docs/DEMO_WALKTHROUGH.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Shows expected JSON output | 1 | Look for code blocks with JSON |
| Defines success criteria | 1 | Look for "success", "expected", "should" |
| Lists common failure modes | 1 | Look for troubleshooting section |
| Has verification commands | 1 | Look for curl or test commands |

---

## SECTION 6: Security (10 points)

### 6.1 Security Policy (5 points)

**File:** `SECURITY.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Has vulnerability reporting process | 1 | Look for reporting instructions |
| Defines severity levels | 1 | Look for critical/high/medium/low |
| Includes response timeline | 1 | Look for SLA or response times |
| Lists security controls | 1 | Look for control descriptions |

### 6.2 Threat Model (5 points)

**File:** `THREAT_MODEL.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Uses STRIDE framework | 1 | Look for S/T/R/I/D/E categories |
| Has threat/mitigation table | 1 | Look for structured threat listing |
| Identifies top 10 threats | 1 | Look for prioritized threat list |
| Includes trust boundaries | 1 | Look for boundary definitions |

---

## SECTION 7: Evaluation & Metrics (10 points)

### 7.1 Evaluation Methodology (5 points)

**File:** `docs/EVALUATION.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Clearly labels synthetic data | 1 | Search for "synthetic", "simulated" |
| Reports metrics with methodology | 1 | Look for metric definitions |
| Acknowledges limitations | 1 | Look for "limitations", "caveats" |
| Includes reproducibility instructions | 1 | Look for commands to re-run evaluation |

### 7.2 README Measured Outcomes (5 points)

**File:** `README.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| Has "Measured Outcomes" section | 1 | Search for outcomes table |
| Reports metrics for all 3 workflows | 1 | Check care gap, readmission, summarization |
| Labels data source (synthetic/benchmark) | 1 | Look for data source labels |
| Includes appropriate caveats | 1 | Look for "will vary", "synthetic" |
| Links to detailed evaluation doc | 1 | Check for EVALUATION.md link |

---

## SECTION 8: Incident Response (5 points)

### 8.1 Postmortem (5 points)

**File:** `postmortems/2024-llm-hallucination-event.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Has timeline of events | 1 | Look for timestamps or sequence |
| Includes root cause analysis (5 whys) | 1 | Search for "why" analysis |
| Documents fix and prevention | 1 | Look for remediation steps |
| Has sign-offs or review | 1 | Look for reviewer names/roles |

---

## SECTION 9: CI/CD (5 points)

### 9.1 GitHub Actions (5 points)

**File:** `.github/workflows/ci.yml`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Runs linting | 1 | Look for lint/ruff/eslint step |
| Runs tests | 1 | Look for pytest/test step |
| Runs security scan | 1 | Look for security/dependency scan |
| Builds Docker image | 1 | Look for docker build step |

---

## SECTION 10: Thought Leadership (Bonus - 5 points)

### 10.1 Position Paper

**File:** `docs/WHY_THIS_EXISTS.md`

| Criterion | Points | How to Verify |
|-----------|--------|---------------|
| File exists | 1 | File present at path |
| Identifies industry problems | 1 | Look for problem statements |
| Explains what CoCo proves | 1 | Look for proof/demonstration claims |
| Addresses multiple audiences | 1 | Look for exec/engineer/platform sections |
| Has clear thesis statement | 1 | Look for main argument |

---

## Scoring Summary

| Section | Max Points |
|---------|------------|
| 1. Repository Structure | 10 |
| 2. Clinical Workflows | 15 |
| 3. Governance Framework | 15 |
| 4. Regulatory Documentation | 15 |
| 5. Operational Readiness | 15 |
| 6. Security | 10 |
| 7. Evaluation & Metrics | 10 |
| 8. Incident Response | 5 |
| 9. CI/CD | 5 |
| **Base Total** | **100** |
| 10. Thought Leadership (Bonus) | +5 |
| **Maximum Total** | **105** |

---

## Pass/Fail Thresholds

| Score | Rating | Interpretation |
|-------|--------|----------------|
| 95-105 | **Exceptional** | Production-ready, reference implementation |
| 85-94 | **Strong** | Minor gaps, ready for most reviews |
| 70-84 | **Adequate** | Significant gaps, needs improvement |
| <70 | **Insufficient** | Major gaps, not ready for review |

---

## Quality Signals to Look For

### Positive Signals (add confidence)
- [ ] Code has type hints throughout
- [ ] Functions have docstrings
- [ ] Tests cover happy path and error cases
- [ ] Documentation links to specific code
- [ ] Commit messages are descriptive
- [ ] No secrets in code (uses env vars)
- [ ] Error handling is explicit
- [ ] Logging includes context (request_id, patient_id_hash)

### Negative Signals (reduce confidence)
- [ ] Empty files or stub-only implementations
- [ ] TODO comments without tracking
- [ ] Hardcoded credentials
- [ ] No error handling
- [ ] Missing type hints in public APIs
- [ ] Documentation contradicts code
- [ ] Tests only check existence, not behavior
- [ ] No comments on complex logic

---

## Sample Evaluation Output

```markdown
# CoCo Repository Evaluation Report

**Evaluated:** 2024-12-01T10:00:00Z
**Evaluator:** [LLM/Human/CI]
**Repository:** https://github.com/cmangun/coco-healthcare-intelligence
**Commit:** abc123

## Summary
- **Total Score:** 98/100 (+5 bonus = 103/105)
- **Rating:** Exceptional
- **Recommendation:** Ready for production review

## Section Scores
| Section | Score | Notes |
|---------|-------|-------|
| 1. Repository Structure | 10/10 | All files present |
| 2. Clinical Workflows | 15/15 | Full implementations |
| 3. Governance Framework | 15/15 | Complete with kill criteria |
| 4. Regulatory Documentation | 15/15 | HIPAA + FDA + Evidence |
| 5. Operational Readiness | 15/15 | Runbook + Demo complete |
| 6. Security | 10/10 | STRIDE threat model |
| 7. Evaluation & Metrics | 10/10 | Properly labeled synthetic |
| 8. Incident Response | 5/5 | Real postmortem with 5-whys |
| 9. CI/CD | 3/5 | Missing security scan |
| 10. Thought Leadership | 5/5 | Strong position paper |

## Detailed Findings
[... section-by-section evidence ...]

## Recommendations
1. Add dependency scanning to CI pipeline
2. Consider adding integration test job
```

---

## Execution Instructions

### For LLM Evaluators

1. Clone or access the repository
2. For each section, verify existence first
3. For quality checks, read the actual file content
4. Quote specific evidence for each criterion
5. Be strict on existence, fair on quality
6. Report any ambiguous cases

### For Automated CI

```bash
# Run existence checks
./scripts/run_eval_existence.sh

# Run quality checks (requires LLM API)
python scripts/run_eval_quality.py --model gpt-4

# Generate report
python scripts/generate_eval_report.py
```

### For Human Reviewers

1. Use this document as a checklist
2. Time budget: 30-45 minutes for full evaluation
3. Focus on sections 2-5 (core value)
4. Spot-check code quality in 2-3 files
5. Read WHY_THIS_EXISTS.md for context

---

*Evaluation Framework Version: 1.0.0*
*Last Updated: 2024-12-01*
