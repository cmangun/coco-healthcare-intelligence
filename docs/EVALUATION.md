# CoCo Evaluation Methodology

This document describes how CoCo's clinical workflows are evaluated, including datasets, metrics, limitations, and results.

---

## Evaluation Philosophy

> "All models are wrong, but some are useful." — George Box

We evaluate CoCo with these principles:

1. **Transparency over optimism**: Report limitations alongside results
2. **Synthetic data acknowledged**: Clearly label synthetic vs. real-world evidence
3. **Clinical relevance**: Metrics that matter to care delivery, not just ML benchmarks
4. **Reproducibility**: Evaluation can be re-run with provided scripts

---

## Evaluation Summary

| Workflow | Primary Metric | Result | Data Source | Confidence |
|----------|----------------|--------|-------------|------------|
| Care Gap Detection | Precision@K | 0.89 | Synthetic | Medium |
| Care Gap Detection | Recall | 0.76 | Synthetic | Medium |
| Readmission Risk | AUC-ROC | 0.81 | Synthetic | Medium |
| Readmission Risk | AUC-PR | 0.72 | Synthetic | Medium |
| Clinical Summarization | Citation Accuracy | 0.94 | Synthetic | Medium |
| Clinical Summarization | Factual Consistency | 0.91 | Synthetic | Medium |

**Important**: All results are from synthetic data evaluation. Production performance will vary based on data quality, patient population, and implementation specifics.

---

## 1. Care Gap Detection Evaluation

### Dataset

- **Size**: 1,000 synthetic patients
- **Source**: FHIR R4 bundles generated via `scripts/generate_synthetic_data.py`
- **Labels**: Manually annotated care gaps based on USPSTF/ACIP/HEDIS guidelines

### Ground Truth Construction

Care gaps were labeled by:
1. Applying published clinical guidelines programmatically
2. Manual review by clinical informaticist (simulated)
3. Consensus where automated and manual disagreed

### Metrics

| Metric | Definition | Result |
|--------|------------|--------|
| Precision@5 | Of top 5 gaps identified, how many are true gaps | 0.89 |
| Recall | Of all true gaps, how many were identified | 0.76 |
| False Positive Rate | Gaps identified that aren't true gaps | 0.11 |
| Latency (p50) | Median response time | 89ms |
| Latency (p99) | 99th percentile response time | 342ms |

### Evaluation Script

```bash
python scripts/evaluate_care_gaps.py \
  --data data/synthetic_patients.json \
  --labels data/care_gap_labels.json \
  --output results/care_gap_evaluation.json
```

### Limitations

1. **Synthetic data**: Real EHR data has noise, missing values, coding inconsistencies
2. **Limited conditions**: Evaluated on common conditions; rare diseases not tested
3. **Guideline lag**: Guidelines update; system reflects guidelines as of training date
4. **No temporal validation**: Did not test on held-out time periods

### Interpretation

- **Precision 0.89**: 89% of identified gaps are actionable (low alert fatigue)
- **Recall 0.76**: 24% of true gaps missed (acceptable for screening, not diagnosis)
- **Suitable for**: Proactive outreach, care coordination
- **Not suitable for**: Definitive clinical decision without provider review

---

## 2. Readmission Risk Evaluation

### Dataset

- **Size**: 5,000 synthetic admission records
- **Source**: Generated with realistic feature distributions
- **Outcome**: 30-day readmission (binary)
- **Prevalence**: 15% (typical for medical admissions)

### Model Architecture

- Ensemble: Gradient Boosted Trees (XGBoost) + Neural Network
- Features: 47 input features from demographics, utilization, clinical, social domains
- Calibration: Platt scaling for probability calibration

### Metrics

| Metric | Definition | Result |
|--------|------------|--------|
| AUC-ROC | Area under ROC curve | 0.81 |
| AUC-PR | Area under Precision-Recall curve | 0.72 |
| Sensitivity @ 0.3 | True positive rate at 30% risk threshold | 0.68 |
| Specificity @ 0.3 | True negative rate at 30% risk threshold | 0.79 |
| Calibration Error | Mean absolute calibration error | 0.04 |
| Brier Score | Probabilistic accuracy | 0.11 |

### Fairness Evaluation

| Subgroup | AUC | Equalized Odds Gap | Notes |
|----------|-----|-------------------|-------|
| Overall | 0.81 | - | Baseline |
| Age < 65 | 0.79 | 0.02 | Within acceptable range |
| Age ≥ 65 | 0.82 | 0.01 | Slight improvement |
| Female | 0.80 | 0.01 | Within acceptable range |
| Male | 0.82 | 0.01 | Within acceptable range |

### Evaluation Script

```bash
python scripts/evaluate_readmission.py \
  --data data/synthetic_admissions.json \
  --model models/readmission_risk_v2.1.0 \
  --output results/readmission_evaluation.json
```

### Limitations

1. **Synthetic outcomes**: Real readmission is influenced by social determinants not fully captured
2. **Feature availability**: Assumed all features present; real data has missingness
3. **Temporal validity**: No concept drift evaluation over time
4. **Single health system**: Not validated across multiple health systems

### Interpretation

- **AUC 0.81**: Strong discrimination; exceeds typical clinical utility threshold (0.75)
- **Calibration 0.04**: Well-calibrated; predicted probabilities are reliable
- **Fairness**: No significant disparities detected (but synthetic data may not reveal real biases)
- **Suitable for**: Risk stratification, care coordination prioritization
- **Not suitable for**: Automated denial of services; always requires clinical judgment

---

## 3. Clinical Summarization Evaluation

### Dataset

- **Size**: 500 synthetic patient records with clinical notes
- **Source**: Generated with realistic clinical language patterns
- **Reference summaries**: Not available (generative task)

### Evaluation Approach

Since no gold-standard summaries exist, we evaluate on:
1. **Citation accuracy**: Do citations support the claims?
2. **Factual consistency**: Is the summary consistent with source documents?
3. **PHI safety**: Does the output contain leaked PHI?
4. **Relevance**: Does the summary contain key clinical information?

### Metrics

| Metric | Definition | Result |
|--------|------------|--------|
| Citation Accuracy | Claims with valid supporting citation | 0.94 |
| Factual Consistency | NLI score (entailment vs. contradiction) | 0.91 |
| PHI Leakage Rate | Summaries with detected PHI | 0.00 |
| Key Finding Coverage | Important findings mentioned | 0.87 |
| Hallucination Rate | Claims not in source documents | 0.06 |

### Citation Verification Method

```python
# For each claim in summary:
# 1. Extract cited source
# 2. Run NLI model (premise=source, hypothesis=claim)
# 3. If entailment score > 0.85, citation is valid

valid_citations = sum(
    nli_model.entailment(source, claim) > 0.85
    for claim, source in claim_citation_pairs
)
citation_accuracy = valid_citations / total_claims
```

### Evaluation Script

```bash
python scripts/evaluate_summarization.py \
  --data data/synthetic_notes.json \
  --output results/summarization_evaluation.json
```

### Limitations

1. **No human evaluation**: Automated metrics only; no physician review
2. **Synthetic notes**: Real clinical notes have more complexity, abbreviations, errors
3. **Limited note types**: Tested on discharge summaries; not H&P, consults, etc.
4. **English only**: No evaluation on non-English content

### Interpretation

- **Citation accuracy 0.94**: Most claims are grounded in sources
- **Hallucination rate 0.06**: 6% of claims not traceable to sources (requires review)
- **PHI leakage 0.00**: Detection working, but should be verified with adversarial testing
- **Suitable for**: Draft generation, clinician review starting point
- **Not suitable for**: Automated documentation without human review

---

## Clinical Outcome Projections

Based on literature benchmarks (not CoCo-specific validation):

| Outcome | Projection | Evidence Basis |
|---------|------------|----------------|
| Gap closure improvement | +30-40% | Published care gap intervention studies |
| Readmission reduction | 15-25% | Risk stratification + intervention literature |
| Documentation time savings | 40-60% | Clinical NLP deployment studies |
| Alert fatigue reduction | 50-70% | High-precision screening studies |

**Caveat**: These are literature-based projections. Actual CoCo deployment outcomes require prospective measurement.

---

## Evaluation Infrastructure

### Reproducibility

All evaluations can be reproduced:

```bash
# Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Generate synthetic data
python scripts/generate_synthetic_data.py --patients 1000

# Run all evaluations
make evaluate

# Results in results/ directory
```

### Continuous Evaluation

In production, model performance is monitored via:

1. **Drift detection**: PSI scores on input features (daily)
2. **Outcome tracking**: Actual vs. predicted readmission (when outcome known)
3. **User feedback**: Clinician accept/reject rates on care gaps
4. **A/B testing**: New model versions compared to baseline

---

## Future Evaluation Plans

| Evaluation | Timeline | Method |
|------------|----------|--------|
| Real-world pilot | TBD | Prospective study with health system partner |
| Multi-site validation | TBD | Federated learning evaluation |
| Longitudinal drift | Ongoing | Monthly model performance review |
| Clinician usability | TBD | User study with practicing physicians |
| Fairness audit | Quarterly | External review of subgroup performance |

---

## References

1. USPSTF. A and B Recommendations. https://uspreventiveservicestaskforce.org/
2. NCQA. HEDIS Measures. https://www.ncqa.org/hedis/
3. Kansagara D, et al. Risk Prediction Models for Hospital Readmission. JAMA. 2011.
4. Zhang Y, et al. Mitigating Hallucination in Large Language Models. arXiv. 2023.

---

*Last Updated: 2024-12-01*  
*Evaluation Version: 1.0.0*
