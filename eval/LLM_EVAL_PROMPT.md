# LLM Evaluation Prompt

Use this prompt to have another LLM evaluate the CoCo repository.

---

## System Prompt

```
You are a senior Healthcare AI platform reviewer evaluating a portfolio repository for a Forward Deployed Engineer position. You are thorough, skeptical, and evidence-based.

Your evaluation should:
1. Verify claims with specific file content
2. Quote evidence for each criterion
3. Be strict on existence checks, fair on quality
4. Identify both strengths and gaps
5. Provide actionable recommendations

Output format: Structured markdown report with scores per section.
```

---

## User Prompt Template

```
Evaluate the CoCo Healthcare Intelligence repository against the FDE portfolio criteria.

Repository: https://github.com/cmangun/coco-healthcare-intelligence
Target: 100/100 Healthcare AI Forward-Deployed Engineer Portfolio

## Evaluation Framework

For each section below, verify the criteria and assign points. Quote specific evidence.

### SECTION 1: Repository Structure (10 points)

**1.1 Core Files (5 points)**
Check these files exist at root:
- [ ] README.md (1 pt)
- [ ] RUNBOOK.md (1 pt)
- [ ] SECURITY.md (1 pt)
- [ ] THREAT_MODEL.md (1 pt)
- [ ] docker-compose.yml (1 pt)

**1.2 Directory Structure (5 points)**
- [ ] .github/workflows/ has CI yml (1 pt)
- [ ] coco/api/ has 2+ Python files (1 pt)
- [ ] coco/governance/ has 2+ Python files (1 pt)
- [ ] coco/workflows/ has 3+ workflow files (1 pt)
- [ ] tests/ has 2+ test files (1 pt)

### SECTION 2: Clinical Workflows (15 points)

**2.1 Care Gap Detection - coco/workflows/care_gap_workflow.py (5 pts)**
- [ ] File exists (1 pt)
- [ ] References USPSTF/HEDIS/ACIP guidelines (1 pt)
- [ ] Has typed Pydantic models (1 pt)
- [ ] Calls audit logging (1 pt)
- [ ] Has docstring (1 pt)

**2.2 Readmission Risk - coco/workflows/readmission_workflow.py (5 pts)**
- [ ] File exists (1 pt)
- [ ] Returns risk_score (0-1) (1 pt)
- [ ] Includes SHAP/contributing factors (1 pt)
- [ ] Tracks model version (1 pt)
- [ ] Has confidence interval (1 pt)

**2.3 Summarization - coco/workflows/summarization_workflow.py (5 pts)**
- [ ] File exists (1 pt)
- [ ] Implements RAG (retrieval + generation) (1 pt)
- [ ] Tracks citations (1 pt)
- [ ] Has PHI detection (1 pt)
- [ ] Addresses hallucination (1 pt)

### SECTION 3: Governance Framework (15 points)

**3.1 Phase Gates - coco/governance/phase_gates.py (5 pts)**
- [ ] File exists (1 pt)
- [ ] Defines 8+ phases (1 pt)
- [ ] Has exit criteria (1 pt)
- [ ] Has kill criteria (1 pt)
- [ ] Has owner concept (1 pt)

**3.2 Cost Telemetry - coco/governance/cost_telemetry.py (5 pts)**
- [ ] File exists (1 pt)
- [ ] Tracks cost per inference (1 pt)
- [ ] Has cost ceiling (1 pt)
- [ ] Calculates ROI (1 pt)
- [ ] Exports Prometheus metrics (1 pt)

**3.3 Audit Logging - coco/governance/audit_logger.py (5 pts)**
- [ ] File exists (1 pt)
- [ ] Implements hash chain (1 pt)
- [ ] Logs PHI access with reason (1 pt)
- [ ] Is append-only/immutable (1 pt)
- [ ] Has verification method (1 pt)

### SECTION 4: Regulatory Documentation (15 points)

**4.1 HIPAA Mapping - regulatory/hipaa-mapping.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] Cites §164.312 (1 pt)
- [ ] Has 4-column table (Req→Control→Impl→Evidence) (1 pt)
- [ ] Links to code files (1 pt)
- [ ] Covers all 5 technical safeguards (1 pt)

**4.2 FDA Change Control - regulatory/fda-ml-change-control.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] References FDA AI/ML guidance (1 pt)
- [ ] Defines allowed vs excluded changes (1 pt)
- [ ] Specifies validation requirements (1 pt)
- [ ] Has rollback procedure (1 pt)

**4.3 Audit Evidence Index - regulatory/audit-evidence-index.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] Organized by control domain (1 pt)
- [ ] Links to specific evidence (1 pt)
- [ ] Covers HIPAA, FDA, SOC2 (1 pt)
- [ ] Has retention schedule (1 pt)

### SECTION 5: Operational Readiness (15 points)

**5.1 Runbook - RUNBOOK.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] Has start/stop procedures (1 pt)
- [ ] Has debugging guide (1 pt)
- [ ] Defines severity/escalation (1 pt)
- [ ] Has "don't do this" section (1 pt)

**5.2 Demo Script - scripts/demo.sh (5 pts)**
- [ ] File exists (1 pt)
- [ ] Starts docker services (1 pt)
- [ ] Runs all 3 workflows (1 pt)
- [ ] Outputs JSON (1 pt)
- [ ] Has status indicators (1 pt)

**5.3 Demo Walkthrough - docs/DEMO_WALKTHROUGH.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] Shows expected JSON output (1 pt)
- [ ] Defines success criteria (1 pt)
- [ ] Lists failure modes (1 pt)
- [ ] Has verification commands (1 pt)

### SECTION 6: Security (10 points)

**6.1 Security Policy - SECURITY.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] Has reporting process (1 pt)
- [ ] Defines severity levels (1 pt)
- [ ] Has response timeline (1 pt)
- [ ] Lists security controls (1 pt)

**6.2 Threat Model - THREAT_MODEL.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] Uses STRIDE framework (1 pt)
- [ ] Has threat/mitigation table (1 pt)
- [ ] Identifies top threats (1 pt)
- [ ] Defines trust boundaries (1 pt)

### SECTION 7: Evaluation & Metrics (10 points)

**7.1 Evaluation Doc - docs/EVALUATION.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] Labels data as synthetic (1 pt)
- [ ] Reports specific metrics (1 pt)
- [ ] Acknowledges limitations (1 pt)
- [ ] Has reproducibility instructions (1 pt)

**7.2 README Outcomes (5 pts)**
- [ ] Has "Measured Outcomes" section (1 pt)
- [ ] Reports metrics for all 3 workflows (1 pt)
- [ ] Labels data source (1 pt)
- [ ] Has caveats (1 pt)
- [ ] Links to EVALUATION.md (1 pt)

### SECTION 8: Incident Response (5 points)

**8.1 Postmortem - postmortems/*.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] Has timeline (1 pt)
- [ ] Has 5-whys/root cause (1 pt)
- [ ] Documents fix (1 pt)
- [ ] Has sign-offs (1 pt)

### SECTION 9: CI/CD (5 points)

**9.1 GitHub Actions - .github/workflows/ci.yml (5 pts)**
- [ ] File exists (1 pt)
- [ ] Runs linting (1 pt)
- [ ] Runs tests (1 pt)
- [ ] Runs security scan (1 pt)
- [ ] Builds Docker image (1 pt)

### SECTION 10: Thought Leadership - BONUS (5 points)

**10.1 Position Paper - docs/WHY_THIS_EXISTS.md (5 pts)**
- [ ] File exists (1 pt)
- [ ] Identifies industry problems (1 pt)
- [ ] Explains what CoCo proves (1 pt)
- [ ] Addresses multiple audiences (1 pt)
- [ ] Has clear thesis (1 pt)

---

## Output Format

Provide your evaluation as:

```markdown
# CoCo Repository Evaluation Report

**Date:** [date]
**Evaluator:** [your model name]
**Repository:** https://github.com/cmangun/coco-healthcare-intelligence

## Summary

| Metric | Value |
|--------|-------|
| Total Score | X/100 (+Y bonus) |
| Rating | [EXCEPTIONAL/STRONG/ADEQUATE/INSUFFICIENT] |
| Recommendation | [Ready for review / Needs work] |

## Section Scores

| Section | Score | Notes |
|---------|-------|-------|
| 1. Repository Structure | X/10 | ... |
| 2. Clinical Workflows | X/15 | ... |
| 3. Governance Framework | X/15 | ... |
| 4. Regulatory Docs | X/15 | ... |
| 5. Operational Readiness | X/15 | ... |
| 6. Security | X/10 | ... |
| 7. Evaluation & Metrics | X/10 | ... |
| 8. Incident Response | X/5 | ... |
| 9. CI/CD | X/5 | ... |
| 10. Thought Leadership | +X/5 | Bonus |

## Detailed Findings

### Section 1: Repository Structure
[For each criterion, quote specific evidence]

[Continue for all sections...]

## Recommendations
1. [If any improvements needed]

## Conclusion
[Final assessment]
```

---

Now read the repository and provide your evaluation.
```

---

## Alternative: Compact Evaluation Prompt

For faster evaluation, use this compact version:

```
Evaluate https://github.com/cmangun/coco-healthcare-intelligence

Check these files exist and contain expected content:

MUST HAVE (100 pts total):
- README.md: Measured Outcomes table, 90-second tour
- RUNBOOK.md: start/stop, debug, escalation
- SECURITY.md: reporting, severity levels
- THREAT_MODEL.md: STRIDE, top 10 threats
- regulatory/hipaa-mapping.md: §164.312, 4-column table
- regulatory/fda-ml-change-control.md: PCCP, rollback
- regulatory/audit-evidence-index.md: evidence locations
- postmortems/*.md: timeline, 5-whys, fix
- scripts/demo.sh: starts services, runs workflows
- docs/EVALUATION.md: metrics, limitations, synthetic label
- docs/DEMO_WALKTHROUGH.md: expected output, failures
- coco/governance/phase_gates.py: 12 phases, kill criteria
- coco/governance/cost_telemetry.py: ROI, ceiling
- coco/governance/audit_logger.py: hash chain
- coco/workflows/: care_gap, readmission, summarization
- .github/workflows/ci.yml: lint, test, security

BONUS (+5 pts):
- docs/WHY_THIS_EXISTS.md: thesis, problems, proof

Score thresholds:
- 95+: EXCEPTIONAL
- 85-94: STRONG
- 70-84: ADEQUATE
- <70: INSUFFICIENT

Output: Score, rating, key findings, recommendations.
```
