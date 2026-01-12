# Postmortem: LLM Hallucination in Clinical Summarization

**Incident ID:** INC-2024-007  
**Date:** 2024-09-14  
**Severity:** P2 (High - Patient Safety Impact)  
**Status:** Resolved  
**Author:** ML Platform Team  

---

## Executive Summary

A clinical summarization request generated a medication dosage that did not exist in the source documents. The hallucinated dosage (Metformin 2500mg) exceeded maximum safe limits. The error was caught by the downstream pharmacist review but exposed a gap in our output validation controls.

**No patient harm occurred.** The incident triggered immediate remediation and permanent control improvements.

---

## Timeline (All times UTC)

| Time | Event |
|------|-------|
| 14:23 | Summarization request for patient P-8472 processed |
| 14:24 | Summary generated with medication section |
| 14:31 | Pharmacist flagged "Metformin 2500mg daily" as impossible |
| 14:35 | Escalation to on-call ML engineer |
| 14:42 | LLM output compared to source documents - hallucination confirmed |
| 14:48 | Feature flag disabled for medication summarization |
| 14:52 | Incident declared, war room opened |
| 15:30 | Root cause identified: context window truncation |
| 16:00 | Temporary mitigation deployed (mandatory citation check) |
| 17:30 | All summaries from past 24h reviewed - no other hallucinations found |
| 18:00 | Incident downgraded, monitoring continues |

---

## Impact

| Metric | Value |
|--------|-------|
| Patients Affected | 1 (no harm) |
| Summaries with Hallucination | 1 of 847 (0.12%) |
| Time to Detection | 8 minutes |
| Time to Mitigation | 25 minutes |
| Feature Downtime | 4 hours |

---

## Root Cause Analysis

### Direct Cause
The LLM generated a medication dosage that was not grounded in the retrieved documents.

### Contributing Factors

1. **Context Window Truncation**
   - Patient had 127 clinical notes
   - RAG retrieved 15 documents (4,200 tokens)
   - Medication list was in document #14, near truncation boundary
   - LLM "filled in" missing information with plausible but incorrect dosage

2. **Insufficient Citation Enforcement**
   - Summary generation did not require explicit citation per medication
   - Post-hoc citation matching allowed uncited statements to pass

3. **Missing Output Validation**
   - No semantic check comparing output claims to source documents
   - No medication dosage range validation against reference database

### 5 Whys

1. Why was the dosage wrong? → LLM hallucinated it
2. Why did the LLM hallucinate? → Source document was truncated from context
3. Why was it truncated? → Patient had too many notes for context window
4. Why wasn't this caught? → No citation requirement for medication statements
5. Why no citation requirement? → Original design assumed RAG grounding was sufficient

---

## Detection

**How we found it:**
- Human pharmacist review (existing workflow)
- Pharmacist knew Metformin max is 2000mg/day

**Why automated detection failed:**
- Citation system only checked that *some* citation existed
- Did not verify citation *supported the specific claim*

---

## Mitigation

### Immediate (Day 0)
- [x] Feature flag disabled for medication summarization
- [x] All summaries from past 24h manually reviewed
- [x] Alerted clinical leadership

### Short-term (Week 1)
- [x] Added mandatory per-claim citation verification
- [x] Implemented medication dosage range check against RxNorm
- [x] Added confidence threshold (reject if < 0.85)

### Long-term (Month 1)
- [x] Deployed semantic entailment check (claim → source)
- [x] Added "hallucination score" to observability dashboard
- [x] Implemented document priority scoring (medications always included)
- [x] Created synthetic test suite with known hallucination triggers

---

## Preventive Controls Added

| Control | Type | Location |
|---------|------|----------|
| Per-claim citation verification | Automated | `summarization_workflow.py` |
| Medication dosage range validation | Automated | `validators/medication.py` |
| Semantic entailment check | Automated | `governance/hallucination_detector.py` |
| Confidence threshold gate | Automated | `governance/llm_controls.py` |
| Hallucination score metric | Observability | Grafana dashboard |
| Document priority scoring | RAG | `rag/retriever.py` |

---

## Lessons Learned

### What Went Well
- Human-in-the-loop caught the error before patient impact
- Time to detection was fast (8 minutes)
- Team responded quickly and decisively
- No finger-pointing; focus on systemic fixes

### What Went Poorly
- Over-reliance on RAG grounding without verification
- Medication summarization was high-risk but treated as standard
- No synthetic test cases for hallucination scenarios

### What We'll Do Differently
1. **Risk-tier features**: Medication, dosage, allergy = highest scrutiny
2. **Citation-required claims**: Specific claim types require explicit grounding
3. **Semantic verification**: Output claims must be entailed by source
4. **Failure injection drills**: Monthly hallucination simulation exercises

---

## Action Items

| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| Deploy per-claim citation check | @ml-platform | 2024-09-15 | ✅ Done |
| Add medication range validation | @ml-platform | 2024-09-16 | ✅ Done |
| Implement entailment checker | @ml-platform | 2024-09-21 | ✅ Done |
| Create hallucination test suite | @qa | 2024-09-28 | ✅ Done |
| Update LLM control documentation | @docs | 2024-09-30 | ✅ Done |
| Conduct team retrospective | @eng-mgr | 2024-10-01 | ✅ Done |
| Schedule monthly failure drills | @sre | 2024-10-15 | ✅ Done |

---

## Appendix: Code Changes

### Citation Verification (Added)

```python
def verify_claim_citations(claim: str, citations: list[Document]) -> bool:
    """Verify that claim is semantically entailed by cited documents."""
    for doc in citations:
        entailment_score = entailment_model.predict(
            premise=doc.content,
            hypothesis=claim
        )
        if entailment_score > ENTAILMENT_THRESHOLD:
            return True
    return False
```

### Medication Validation (Added)

```python
def validate_medication_dosage(medication: str, dosage: str) -> bool:
    """Check dosage against RxNorm reference ranges."""
    rxnorm_entry = rxnorm_db.lookup(medication)
    if rxnorm_entry:
        max_daily = rxnorm_entry.max_daily_dose
        parsed_dose = parse_dosage(dosage)
        return parsed_dose <= max_daily
    return False  # Unknown medication = flag for review
```

---

## Sign-off

| Role | Name | Date |
|------|------|------|
| Incident Commander | ML Platform Lead | 2024-09-14 |
| Clinical Safety | Chief Medical Officer | 2024-09-15 |
| Engineering | VP Engineering | 2024-09-15 |
| Compliance | HIPAA Officer | 2024-09-16 |

---

*This postmortem follows the blameless incident review process. The goal is systemic improvement, not individual accountability.*
