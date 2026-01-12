"""
Readmission Risk Prediction Workflow

Orchestrates the 30-day readmission risk prediction pipeline:
Data Lakehouse → Feature Store → ML Model → Governance → Response

Maps to FDE Playbook Phases 6-7 (Build & Validation).
"""

from datetime import datetime
from typing import Optional
from enum import Enum
import hashlib
import uuid
import random

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContributingFactor(BaseModel):
    factor_name: str
    factor_category: str
    weight: float
    value: str
    reference_range: Optional[str] = None
    is_modifiable: bool


class Intervention(BaseModel):
    intervention_id: str
    name: str
    description: str
    target_factors: list[str]
    estimated_risk_reduction: float
    evidence_level: str
    implementation_difficulty: str


class ModelGovernance(BaseModel):
    model_id: str
    model_version: str
    training_date: datetime
    validation_auc: float
    fairness_metrics: dict
    last_drift_check: datetime
    drift_status: str


class ReadmissionPrediction(BaseModel):
    patient_id: str
    encounter_id: Optional[str]
    prediction_timestamp: datetime
    risk_score: float
    risk_tier: RiskTier
    confidence_interval: tuple[float, float]
    contributing_factors: list[ContributingFactor]
    recommended_interventions: list[Intervention]
    model_governance: ModelGovernance
    audit_trail: dict


class BatchPredictionResponse(BaseModel):
    total_patients: int
    predictions: list[ReadmissionPrediction]
    summary: dict
    processing_time_ms: float


class ReadmissionWorkflow:
    """
    Readmission Risk Prediction Workflow
    
    This workflow orchestrates the complete readmission prediction pipeline,
    connecting multiple healthcare AI repositories:
    
    1. healthcare-data-lakehouse: Historical patient data
    2. feature-store-healthcare: Real-time feature retrieval
    3. mlops-healthcare-platform: Model serving and versioning
    4. model-governance-framework: Bias detection and fairness
    5. llm-observability-platform: Cost and performance tracking
    
    Playbook Alignment:
    - Phase 6: Build (model training and instrumentation)
    - Phase 7: Validation (bias testing, performance benchmarks)
    - Phase 10: Production (model serving, monitoring)
    - Phase 11: Reliability (drift detection, retraining)
    """
    
    def __init__(self):
        self.model_version = "2.1.0"
        self.model_id = "readmission-risk-v2"
        self.audit_chain = []
        
        # Feature definitions (would come from feature store registry)
        self.feature_definitions = {
            "prior_admissions_12m": {
                "category": "utilization",
                "importance": 0.142,
                "description": "Hospital admissions in past 12 months",
            },
            "length_of_stay": {
                "category": "clinical",
                "importance": 0.098,
                "description": "Current stay length in days",
            },
            "charlson_comorbidity_index": {
                "category": "clinical",
                "importance": 0.087,
                "description": "Charlson Comorbidity Index",
            },
            "ed_visits_6m": {
                "category": "utilization",
                "importance": 0.076,
                "description": "ED visits in past 6 months",
            },
            "polypharmacy_count": {
                "category": "clinical",
                "importance": 0.065,
                "description": "Number of active medications",
            },
            "discharge_disposition": {
                "category": "clinical",
                "importance": 0.058,
                "description": "Planned discharge destination",
            },
            "primary_diagnosis_category": {
                "category": "clinical",
                "importance": 0.054,
                "description": "Primary diagnosis CCS category",
            },
            "social_support_score": {
                "category": "social",
                "importance": 0.048,
                "description": "Social determinants score",
            },
            "age": {
                "category": "demographic",
                "importance": 0.042,
                "description": "Patient age in years",
            },
            "insurance_type": {
                "category": "demographic",
                "importance": 0.035,
                "description": "Insurance payer type",
            },
        }
        
        # Intervention definitions
        self.interventions = [
            Intervention(
                intervention_id="int-001",
                name="Transitional Care Management",
                description="Post-discharge follow-up within 7 days with care coordinator",
                target_factors=["discharge_disposition", "prior_admissions_12m"],
                estimated_risk_reduction=0.18,
                evidence_level="A",
                implementation_difficulty="moderate",
            ),
            Intervention(
                intervention_id="int-002",
                name="Medication Reconciliation",
                description="Comprehensive medication review and reconciliation at discharge",
                target_factors=["polypharmacy_count"],
                estimated_risk_reduction=0.12,
                evidence_level="A",
                implementation_difficulty="easy",
            ),
            Intervention(
                intervention_id="int-003",
                name="Home Health Services",
                description="Post-discharge home health nursing visits",
                target_factors=["social_support_score", "age"],
                estimated_risk_reduction=0.15,
                evidence_level="B",
                implementation_difficulty="moderate",
            ),
            Intervention(
                intervention_id="int-004",
                name="Care Coordination",
                description="Dedicated care coordinator assignment for high-risk patients",
                target_factors=["prior_admissions_12m", "ed_visits_6m", "charlson_comorbidity_index"],
                estimated_risk_reduction=0.10,
                evidence_level="B",
                implementation_difficulty="complex",
            ),
            Intervention(
                intervention_id="int-005",
                name="Telemedicine Follow-up",
                description="Virtual check-in within 48 hours of discharge",
                target_factors=["discharge_disposition"],
                estimated_risk_reduction=0.08,
                evidence_level="B",
                implementation_difficulty="easy",
            ),
        ]
    
    def _generate_audit_hash(self, data: dict) -> str:
        """Generate hash for audit chain integrity."""
        previous_hash = self.audit_chain[-1]["hash"] if self.audit_chain else "genesis"
        content = f"{previous_hash}:{str(data)}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _add_audit_entry(self, operation: str, details: dict):
        """Add entry to immutable audit chain."""
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "details": details,
            "hash": self._generate_audit_hash(details),
        }
        self.audit_chain.append(entry)
    
    async def _fetch_features(self, patient_id: str, encounter_id: Optional[str]) -> dict:
        """
        Fetch features from Feature Store.
        
        In production, this calls feature-store-healthcare service.
        """
        # Simulated feature retrieval for demonstration
        # In production, this would query the feature store with point-in-time correctness
        
        return {
            "patient_id": patient_id,
            "encounter_id": encounter_id or f"ENC-{uuid.uuid4().hex[:8]}",
            "prior_admissions_12m": random.randint(0, 4),
            "length_of_stay": random.randint(2, 14),
            "charlson_comorbidity_index": random.randint(0, 8),
            "ed_visits_6m": random.randint(0, 6),
            "polypharmacy_count": random.randint(3, 15),
            "discharge_disposition": random.choice(["home", "snf", "home_health", "rehab"]),
            "primary_diagnosis_category": random.choice(["heart_failure", "pneumonia", "copd", "diabetes"]),
            "social_support_score": random.uniform(0.3, 1.0),
            "age": random.randint(45, 85),
            "insurance_type": random.choice(["medicare", "medicaid", "commercial", "self_pay"]),
            "feature_timestamp": datetime.utcnow().isoformat(),
        }
    
    def _run_model_inference(self, features: dict) -> tuple[float, tuple[float, float]]:
        """
        Run model inference.
        
        In production, this calls the model serving endpoint from mlops-healthcare-platform.
        The model is an ensemble of Gradient Boosted Trees and Neural Network.
        """
        # Simulated model inference
        # In production, this would call SageMaker/Azure ML/Vertex AI endpoint
        
        # Calculate base risk from features (simplified)
        base_risk = 0.05
        
        # Prior admissions is the strongest predictor
        base_risk += features["prior_admissions_12m"] * 0.08
        
        # Length of stay
        if features["length_of_stay"] > 7:
            base_risk += 0.10
        elif features["length_of_stay"] > 4:
            base_risk += 0.05
        
        # Comorbidity
        base_risk += features["charlson_comorbidity_index"] * 0.03
        
        # ED visits
        base_risk += features["ed_visits_6m"] * 0.04
        
        # Polypharmacy
        if features["polypharmacy_count"] > 10:
            base_risk += 0.08
        elif features["polypharmacy_count"] > 5:
            base_risk += 0.04
        
        # Discharge disposition
        disposition_risk = {
            "home": 0.0,
            "home_health": 0.05,
            "snf": 0.10,
            "rehab": 0.08,
        }
        base_risk += disposition_risk.get(features["discharge_disposition"], 0.05)
        
        # Social support
        base_risk += (1 - features["social_support_score"]) * 0.08
        
        # Age
        if features["age"] > 75:
            base_risk += 0.05
        elif features["age"] > 65:
            base_risk += 0.02
        
        # Cap at 0.95
        risk_score = min(max(base_risk, 0.02), 0.95)
        
        # Generate confidence interval (95% CI)
        margin = 0.05 + (0.10 * (0.5 - abs(risk_score - 0.5)))  # Wider CI near 0.5
        ci_lower = max(0.0, risk_score - margin)
        ci_upper = min(1.0, risk_score + margin)
        
        return risk_score, (ci_lower, ci_upper)
    
    def _determine_risk_tier(self, risk_score: float) -> RiskTier:
        """Determine risk tier from score."""
        if risk_score >= 0.6:
            return RiskTier.CRITICAL
        elif risk_score >= 0.4:
            return RiskTier.HIGH
        elif risk_score >= 0.2:
            return RiskTier.MEDIUM
        else:
            return RiskTier.LOW
    
    def _calculate_contributing_factors(self, features: dict) -> list[ContributingFactor]:
        """Calculate contributing factors with SHAP-like explanations."""
        factors = []
        
        # Prior admissions
        if features["prior_admissions_12m"] > 0:
            factors.append(ContributingFactor(
                factor_name="prior_admissions_12m",
                factor_category="utilization",
                weight=min(features["prior_admissions_12m"] * 0.08, 0.30),
                value=str(features["prior_admissions_12m"]),
                reference_range="0",
                is_modifiable=False,
            ))
        
        # Length of stay
        if features["length_of_stay"] > 4:
            factors.append(ContributingFactor(
                factor_name="length_of_stay",
                factor_category="clinical",
                weight=0.10 if features["length_of_stay"] > 7 else 0.05,
                value=f"{features['length_of_stay']} days",
                reference_range="<= 4 days",
                is_modifiable=False,
            ))
        
        # Comorbidity
        if features["charlson_comorbidity_index"] > 2:
            factors.append(ContributingFactor(
                factor_name="charlson_comorbidity_index",
                factor_category="clinical",
                weight=features["charlson_comorbidity_index"] * 0.03,
                value=str(features["charlson_comorbidity_index"]),
                reference_range="0-2",
                is_modifiable=False,
            ))
        
        # Polypharmacy
        if features["polypharmacy_count"] > 5:
            factors.append(ContributingFactor(
                factor_name="polypharmacy_count",
                factor_category="clinical",
                weight=0.08 if features["polypharmacy_count"] > 10 else 0.04,
                value=f"{features['polypharmacy_count']} medications",
                reference_range="<= 5",
                is_modifiable=True,
            ))
        
        # Social support
        if features["social_support_score"] < 0.6:
            factors.append(ContributingFactor(
                factor_name="social_support_score",
                factor_category="social",
                weight=(1 - features["social_support_score"]) * 0.08,
                value=f"{features['social_support_score']:.2f}",
                reference_range=">= 0.6",
                is_modifiable=True,
            ))
        
        # Sort by weight descending
        factors.sort(key=lambda f: f.weight, reverse=True)
        
        return factors[:5]  # Top 5 factors
    
    def _recommend_interventions(
        self,
        risk_tier: RiskTier,
        contributing_factors: list[ContributingFactor],
    ) -> list[Intervention]:
        """Recommend interventions based on risk factors."""
        if risk_tier == RiskTier.LOW:
            return []
        
        # Get modifiable factor names
        factor_names = {f.factor_name for f in contributing_factors}
        
        # Score interventions by relevance
        scored_interventions = []
        for intervention in self.interventions:
            overlap = len(set(intervention.target_factors) & factor_names)
            if overlap > 0 or risk_tier in [RiskTier.HIGH, RiskTier.CRITICAL]:
                score = overlap * intervention.estimated_risk_reduction
                scored_interventions.append((score, intervention))
        
        # Sort by score and return top recommendations
        scored_interventions.sort(key=lambda x: x[0], reverse=True)
        
        if risk_tier == RiskTier.CRITICAL:
            return [i for _, i in scored_interventions[:4]]
        elif risk_tier == RiskTier.HIGH:
            return [i for _, i in scored_interventions[:3]]
        else:
            return [i for _, i in scored_interventions[:2]]
    
    def _get_model_governance(self) -> ModelGovernance:
        """Get current model governance information."""
        return ModelGovernance(
            model_id=self.model_id,
            model_version=self.model_version,
            training_date=datetime(2024, 1, 10),
            validation_auc=0.81,
            fairness_metrics={
                "demographic_parity": {
                    "age_disparity": 0.03,
                    "gender_disparity": 0.02,
                    "status": "within_threshold",
                },
                "equalized_odds": {
                    "fpr_ratio": 0.94,
                    "fnr_ratio": 0.91,
                    "status": "within_threshold",
                },
            },
            last_drift_check=datetime.utcnow(),
            drift_status="healthy",
        )
    
    async def predict_risk(
        self,
        patient_id: str,
        encounter_id: Optional[str] = None,
        include_shap: bool = False,
    ) -> ReadmissionPrediction:
        """
        Main entry point for readmission risk prediction.
        
        Orchestrates:
        1. Feature retrieval from feature store
        2. Model inference
        3. Risk tier determination
        4. Contributing factor analysis
        5. Intervention recommendations
        6. Governance and audit logging
        """
        self._add_audit_entry("prediction_started", {
            "patient_id": patient_id,
            "encounter_id": encounter_id,
        })
        
        # Step 1: Fetch features
        features = await self._fetch_features(patient_id, encounter_id)
        self._add_audit_entry("features_retrieved", {
            "feature_count": len(features),
            "feature_timestamp": features["feature_timestamp"],
        })
        
        # Step 2: Run model inference
        risk_score, confidence_interval = self._run_model_inference(features)
        self._add_audit_entry("inference_completed", {
            "risk_score": risk_score,
            "model_version": self.model_version,
        })
        
        # Step 3: Determine risk tier
        risk_tier = self._determine_risk_tier(risk_score)
        
        # Step 4: Calculate contributing factors
        contributing_factors = self._calculate_contributing_factors(features)
        
        # Step 5: Recommend interventions
        interventions = self._recommend_interventions(risk_tier, contributing_factors)
        
        # Step 6: Get governance info
        governance = self._get_model_governance()
        
        # Build response
        prediction = ReadmissionPrediction(
            patient_id=patient_id,
            encounter_id=features["encounter_id"],
            prediction_timestamp=datetime.utcnow(),
            risk_score=risk_score,
            risk_tier=risk_tier,
            confidence_interval=confidence_interval,
            contributing_factors=contributing_factors,
            recommended_interventions=interventions,
            model_governance=governance,
            audit_trail={
                "entries": self.audit_chain,
                "hash": self.audit_chain[-1]["hash"] if self.audit_chain else None,
            },
        )
        
        self._add_audit_entry("prediction_completed", {
            "risk_tier": risk_tier.value,
            "interventions_count": len(interventions),
        })
        
        logger.info(
            "readmission_prediction_complete",
            patient_id=patient_id,
            risk_score=risk_score,
            risk_tier=risk_tier.value,
        )
        
        return prediction
    
    async def batch_predict(
        self,
        patient_ids: list[str],
        encounter_type: Optional[str] = None,
        include_interventions: bool = True,
    ) -> BatchPredictionResponse:
        """Batch prediction for multiple patients."""
        import time
        start_time = time.time()
        
        predictions = []
        risk_tier_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for patient_id in patient_ids:
            prediction = await self.predict_risk(patient_id)
            predictions.append(prediction)
            risk_tier_counts[prediction.risk_tier.value] += 1
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchPredictionResponse(
            total_patients=len(patient_ids),
            predictions=predictions,
            summary={
                "risk_tier_distribution": risk_tier_counts,
                "high_risk_count": risk_tier_counts["high"] + risk_tier_counts["critical"],
                "average_risk_score": sum(p.risk_score for p in predictions) / len(predictions),
                "model_version": self.model_version,
            },
            processing_time_ms=processing_time,
        )
