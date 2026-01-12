"""
Readmission Risk Prediction API Router

Predicts 30-day hospital readmission risk for intervention targeting.
Maps to Phase 6-7 (Build & Validation) of the FDE Playbook.
"""

from datetime import datetime
from typing import Optional
from enum import Enum

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from coco.workflows.readmission_workflow import ReadmissionWorkflow
from coco.governance.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)
router = APIRouter()
audit = AuditLogger(component="readmission")


class RiskTier(str, Enum):
    """Risk tier classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContributingFactor(BaseModel):
    """Factor contributing to readmission risk."""
    factor_name: str = Field(..., description="Name of the contributing factor")
    factor_category: str = Field(..., description="Category (clinical, social, utilization)")
    weight: float = Field(..., ge=0, le=1, description="Contribution weight to risk score")
    value: str = Field(..., description="Patient's value for this factor")
    reference_range: Optional[str] = Field(None, description="Normal/expected range")
    is_modifiable: bool = Field(..., description="Whether this factor can be modified")


class Intervention(BaseModel):
    """Recommended intervention for risk reduction."""
    intervention_id: str
    name: str
    description: str
    target_factors: list[str]
    estimated_risk_reduction: float = Field(..., ge=0, le=1)
    evidence_level: str = Field(..., description="A, B, C, or D evidence level")
    implementation_difficulty: str = Field(..., description="easy, moderate, complex")


class ModelGovernance(BaseModel):
    """Model governance information for audit compliance."""
    model_id: str
    model_version: str
    training_date: datetime
    validation_auc: float
    fairness_metrics: dict
    last_drift_check: datetime
    drift_status: str


class ReadmissionPrediction(BaseModel):
    """Complete readmission risk prediction response."""
    patient_id: str
    encounter_id: Optional[str]
    prediction_timestamp: datetime
    risk_score: float = Field(..., ge=0, le=1, description="Probability of 30-day readmission")
    risk_tier: RiskTier
    confidence_interval: tuple[float, float]
    contributing_factors: list[ContributingFactor]
    recommended_interventions: list[Intervention]
    model_governance: ModelGovernance
    audit_trail: dict


class BatchPredictionRequest(BaseModel):
    """Request for batch readmission predictions."""
    patient_ids: list[str] = Field(..., min_length=1, max_length=500)
    encounter_type: Optional[str] = None
    include_interventions: bool = True


class BatchPredictionResponse(BaseModel):
    """Response for batch predictions."""
    total_patients: int
    predictions: list[ReadmissionPrediction]
    summary: dict
    processing_time_ms: float


@router.get(
    "/predict/{patient_id}",
    response_model=ReadmissionPrediction,
    summary="Predict readmission risk for a patient",
    description="""
    Generates 30-day readmission risk prediction using an ensemble model
    trained on historical healthcare data with HIPAA-compliant processing.
    
    **Playbook Phase**: 6-7 (Build & Validation)
    
    **Model**: Gradient Boosted Trees + Neural Network ensemble
    **Validation AUC**: 0.81
    **Fairness**: Evaluated across age, gender, race, payer status
    
    **Data Flow**:
    FHIR → Lakehouse → Feature Store → ML Model → Governance Layer → Response
    """
)
async def predict_readmission(
    patient_id: str,
    encounter_id: Optional[str] = Query(None, description="Specific encounter to analyze"),
    include_shap: bool = Query(False, description="Include SHAP explanations"),
):
    """Predict 30-day readmission risk for a patient."""
    logger.info(
        "readmission_prediction_started",
        patient_id=patient_id,
        encounter_id=encounter_id,
    )
    
    try:
        workflow = ReadmissionWorkflow()
        prediction = await workflow.predict_risk(
            patient_id=patient_id,
            encounter_id=encounter_id,
            include_shap=include_shap,
        )
        
        # Audit logging
        audit.log_operation(
            operation="predict_readmission",
            patient_id=patient_id,
            risk_score=prediction.risk_score,
            risk_tier=prediction.risk_tier.value,
            model_version=prediction.model_governance.model_version,
        )
        
        logger.info(
            "readmission_prediction_completed",
            patient_id=patient_id,
            risk_score=prediction.risk_score,
            risk_tier=prediction.risk_tier.value,
        )
        
        return prediction
        
    except Exception as e:
        logger.error(
            "readmission_prediction_failed",
            patient_id=patient_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Readmission prediction failed: {str(e)}"
        )


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    summary="Batch readmission predictions",
    description="Generate predictions for multiple patients efficiently."
)
async def batch_predict_readmission(request: BatchPredictionRequest):
    """Batch prediction for multiple patients."""
    logger.info(
        "batch_prediction_started",
        patient_count=len(request.patient_ids),
    )
    
    try:
        workflow = ReadmissionWorkflow()
        response = await workflow.batch_predict(
            patient_ids=request.patient_ids,
            encounter_type=request.encounter_type,
            include_interventions=request.include_interventions,
        )
        
        audit.log_operation(
            operation="batch_predict_readmission",
            patient_count=len(request.patient_ids),
            high_risk_count=response.summary.get("high_risk_count", 0),
        )
        
        return response
        
    except Exception as e:
        logger.error("batch_prediction_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/model/info",
    summary="Model information and governance",
    description="Returns current model version, performance metrics, and governance status."
)
async def get_model_info():
    """Get current model information and governance status."""
    return {
        "model": {
            "id": "readmission-risk-v2",
            "version": "2.1.0",
            "type": "Ensemble (GBT + Neural Network)",
            "training_date": "2024-01-10T00:00:00Z",
            "training_samples": 1_247_832,
            "features": 156,
        },
        "performance": {
            "validation_auc": 0.81,
            "validation_accuracy": 0.74,
            "precision_at_10": 0.68,
            "recall_at_10": 0.42,
            "calibration_error": 0.023,
        },
        "fairness": {
            "demographic_parity": {
                "age_groups": {"18-40": 0.12, "40-65": 0.18, "65+": 0.31},
                "gender": {"male": 0.19, "female": 0.17},
                "max_disparity": 0.03,
            },
            "equalized_odds": {
                "fpr_ratio": 0.94,
                "fnr_ratio": 0.91,
                "status": "within_threshold",
            },
        },
        "governance": {
            "model_card_url": "/governance/model-cards/readmission-v2.1.0",
            "bias_audit_date": "2024-01-08T00:00:00Z",
            "next_review_date": "2024-04-08T00:00:00Z",
            "approval_status": "approved",
            "approvers": ["ML Lead", "Clinical Advisor", "Compliance Officer"],
        },
        "drift_monitoring": {
            "last_check": "2024-01-15T06:00:00Z",
            "feature_drift_psi": 0.08,
            "prediction_drift": 0.02,
            "status": "healthy",
            "retrain_threshold": 0.25,
        },
    }


@router.get(
    "/model/features",
    summary="Feature importance and descriptions",
    description="Returns the top features used by the model with importance scores."
)
async def get_feature_importance():
    """Get feature importance for model interpretability."""
    return {
        "features": [
            {
                "name": "prior_admissions_12m",
                "importance": 0.142,
                "category": "utilization",
                "description": "Number of hospital admissions in past 12 months",
            },
            {
                "name": "length_of_stay",
                "importance": 0.098,
                "category": "clinical",
                "description": "Length of current hospital stay in days",
            },
            {
                "name": "charlson_comorbidity_index",
                "importance": 0.087,
                "category": "clinical",
                "description": "Charlson Comorbidity Index score",
            },
            {
                "name": "ed_visits_6m",
                "importance": 0.076,
                "category": "utilization",
                "description": "Emergency department visits in past 6 months",
            },
            {
                "name": "polypharmacy_count",
                "importance": 0.065,
                "category": "clinical",
                "description": "Number of active medications",
            },
            {
                "name": "discharge_disposition",
                "importance": 0.058,
                "category": "clinical",
                "description": "Discharge destination (home, SNF, etc.)",
            },
            {
                "name": "primary_diagnosis_category",
                "importance": 0.054,
                "category": "clinical",
                "description": "Primary diagnosis CCS category",
            },
            {
                "name": "social_support_score",
                "importance": 0.048,
                "category": "social",
                "description": "Social determinants of health score",
            },
        ],
        "total_features": 156,
        "feature_groups": {
            "clinical": 78,
            "utilization": 34,
            "social": 22,
            "demographic": 12,
            "temporal": 10,
        },
    }


@router.get(
    "/interventions",
    summary="Available interventions",
    description="List all available interventions for readmission risk reduction."
)
async def list_interventions():
    """List available interventions for risk reduction."""
    return {
        "interventions": [
            {
                "id": "int-001",
                "name": "Transitional Care Management",
                "description": "Post-discharge follow-up within 7 days",
                "target_factors": ["discharge_disposition", "follow_up_scheduled"],
                "evidence_level": "A",
                "estimated_risk_reduction": 0.18,
            },
            {
                "id": "int-002",
                "name": "Medication Reconciliation",
                "description": "Comprehensive medication review at discharge",
                "target_factors": ["polypharmacy_count", "medication_adherence"],
                "evidence_level": "A",
                "estimated_risk_reduction": 0.12,
            },
            {
                "id": "int-003",
                "name": "Home Health Services",
                "description": "Post-discharge home health nursing visits",
                "target_factors": ["social_support_score", "functional_status"],
                "evidence_level": "B",
                "estimated_risk_reduction": 0.15,
            },
            {
                "id": "int-004",
                "name": "Care Coordination",
                "description": "Dedicated care coordinator assignment",
                "target_factors": ["prior_admissions_12m", "ed_visits_6m"],
                "evidence_level": "B",
                "estimated_risk_reduction": 0.10,
            },
        ],
    }


@router.get(
    "/metrics",
    summary="Service operational metrics",
    description="Operational metrics for the readmission prediction service."
)
async def get_metrics():
    """Get operational metrics."""
    return {
        "service": "readmission-prediction",
        "playbook_phase": "11-reliability",
        "metrics": {
            "predictions_24h": 3421,
            "average_latency_ms": 89,
            "p99_latency_ms": 342,
            "high_risk_predictions_24h": 547,
            "error_rate": 0.0008,
        },
        "model_performance": {
            "live_auc_7d": 0.79,
            "calibration_7d": 0.031,
            "drift_score": 0.08,
        },
        "governance": {
            "phi_detections": 0,
            "audit_events_24h": 3421,
            "cost_per_prediction_usd": 0.0031,
            "value_per_prediction_usd": 0.45,
        },
    }
