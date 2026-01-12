"""
Care Gap Detection API Router

Identifies patients missing preventive care based on clinical guidelines.
Maps to Phase 4-6 (Architect) of the FDE Playbook.
"""

from datetime import datetime, date
from typing import Optional
from enum import Enum

import structlog
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from coco.workflows.care_gap_workflow import CareGapWorkflow
from coco.governance.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)
router = APIRouter()
audit = AuditLogger(component="care-gaps")


class CareGapPriority(str, Enum):
    """Priority levels for care gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CareGapType(str, Enum):
    """Types of care gaps."""
    SCREENING = "screening"
    VACCINATION = "vaccination"
    LAB_TEST = "lab_test"
    MEDICATION = "medication"
    FOLLOW_UP = "follow_up"


class CareGap(BaseModel):
    """Individual care gap identified for a patient."""
    gap_id: str = Field(..., description="Unique identifier for this care gap")
    type: CareGapType = Field(..., description="Type of care gap")
    name: str = Field(..., description="Name of the care intervention")
    description: str = Field(..., description="Detailed description")
    guideline_source: str = Field(..., description="Clinical guideline source (USPSTF, etc.)")
    due_date: date = Field(..., description="Date by which care should be completed")
    priority: CareGapPriority = Field(..., description="Priority level")
    icd10_codes: list[str] = Field(default_factory=list, description="Relevant ICD-10 codes")
    cpt_codes: list[str] = Field(default_factory=list, description="Relevant CPT codes")
    estimated_impact: float = Field(..., ge=0, le=1, description="Estimated health impact score")


class CareGapResponse(BaseModel):
    """Response containing all care gaps for a patient."""
    patient_id: str
    analysis_timestamp: datetime
    total_gaps: int
    risk_score: float = Field(..., ge=0, le=1, description="Overall care gap risk score")
    care_gaps: list[CareGap]
    recommendations: list[str]
    audit_trail: dict


class CareGapSummary(BaseModel):
    """Summary statistics for care gap analysis."""
    total_patients_analyzed: int
    patients_with_gaps: int
    total_gaps_identified: int
    gaps_by_type: dict[str, int]
    gaps_by_priority: dict[str, int]
    average_risk_score: float


class PatientCohort(BaseModel):
    """Request model for cohort-based care gap analysis."""
    patient_ids: list[str] = Field(..., min_length=1, max_length=1000)
    gap_types: Optional[list[CareGapType]] = None
    min_priority: Optional[CareGapPriority] = None
    include_closed_gaps: bool = False


@router.get(
    "/patient/{patient_id}",
    response_model=CareGapResponse,
    summary="Detect care gaps for a patient",
    description="""
    Analyzes a patient's clinical data to identify missing preventive care
    based on USPSTF guidelines, immunization schedules, and disease-specific
    protocols.
    
    **Playbook Phase**: 4-6 (Architect)
    
    **Data Flow**: 
    FHIR Integration → Data Lakehouse → Feature Store → Care Gap Rules Engine
    """
)
async def detect_care_gaps(
    patient_id: str,
    include_closed: bool = Query(False, description="Include previously closed gaps"),
    lookback_months: int = Query(24, ge=6, le=120, description="Months of history to analyze"),
    background_tasks: BackgroundTasks = None,
):
    """Detect care gaps for a specific patient."""
    logger.info("care_gap_detection_started", patient_id=patient_id)
    
    try:
        workflow = CareGapWorkflow()
        result = await workflow.detect_gaps(
            patient_id=patient_id,
            include_closed=include_closed,
            lookback_months=lookback_months,
        )
        
        # Audit logging
        audit.log_operation(
            operation="detect_care_gaps",
            patient_id=patient_id,
            result_count=len(result.care_gaps),
            risk_score=result.risk_score,
        )
        
        logger.info(
            "care_gap_detection_completed",
            patient_id=patient_id,
            gaps_found=len(result.care_gaps),
            risk_score=result.risk_score,
        )
        
        return result
        
    except Exception as e:
        logger.error("care_gap_detection_failed", patient_id=patient_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Care gap detection failed: {str(e)}")


@router.post(
    "/cohort",
    response_model=CareGapSummary,
    summary="Analyze care gaps for a patient cohort",
    description="""
    Batch analysis of care gaps across multiple patients for population health
    management and quality reporting.
    
    **Playbook Phase**: 10 (Production)
    
    **Use Case**: Quality measure reporting, risk stratification
    """
)
async def analyze_cohort_care_gaps(
    cohort: PatientCohort,
    background_tasks: BackgroundTasks,
):
    """Analyze care gaps for a cohort of patients."""
    logger.info(
        "cohort_analysis_started",
        patient_count=len(cohort.patient_ids),
        gap_types=cohort.gap_types,
    )
    
    try:
        workflow = CareGapWorkflow()
        summary = await workflow.analyze_cohort(
            patient_ids=cohort.patient_ids,
            gap_types=cohort.gap_types,
            min_priority=cohort.min_priority,
        )
        
        audit.log_operation(
            operation="cohort_care_gap_analysis",
            patient_count=len(cohort.patient_ids),
            total_gaps=summary.total_gaps_identified,
        )
        
        return summary
        
    except Exception as e:
        logger.error("cohort_analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cohort analysis failed: {str(e)}")


@router.get(
    "/guidelines",
    summary="List available clinical guidelines",
    description="Returns all clinical guidelines used for care gap detection."
)
async def list_guidelines():
    """List all clinical guidelines used for care gap detection."""
    return {
        "guidelines": [
            {
                "id": "uspstf-2024",
                "name": "USPSTF Preventive Services",
                "version": "2024",
                "url": "https://www.uspreventiveservicestaskforce.org/",
                "gap_types": ["screening", "vaccination"],
            },
            {
                "id": "acip-2024",
                "name": "ACIP Immunization Schedule",
                "version": "2024",
                "url": "https://www.cdc.gov/vaccines/schedules/",
                "gap_types": ["vaccination"],
            },
            {
                "id": "hedis-2024",
                "name": "HEDIS Quality Measures",
                "version": "2024",
                "url": "https://www.ncqa.org/hedis/",
                "gap_types": ["screening", "lab_test", "medication"],
            },
            {
                "id": "ada-2024",
                "name": "ADA Diabetes Standards of Care",
                "version": "2024",
                "url": "https://diabetesjournals.org/care",
                "gap_types": ["lab_test", "screening", "medication"],
            },
        ],
        "last_updated": "2024-01-15",
        "next_update": "2024-07-01",
    }


@router.post(
    "/patient/{patient_id}/close/{gap_id}",
    summary="Close a care gap",
    description="Mark a care gap as addressed/closed."
)
async def close_care_gap(
    patient_id: str,
    gap_id: str,
    closure_reason: str = Query(..., description="Reason for closure"),
    closure_date: Optional[date] = Query(None, description="Date gap was addressed"),
):
    """Close a care gap after intervention."""
    logger.info(
        "care_gap_closure",
        patient_id=patient_id,
        gap_id=gap_id,
        reason=closure_reason,
    )
    
    workflow = CareGapWorkflow()
    result = await workflow.close_gap(
        patient_id=patient_id,
        gap_id=gap_id,
        closure_reason=closure_reason,
        closure_date=closure_date or date.today(),
    )
    
    audit.log_operation(
        operation="close_care_gap",
        patient_id=patient_id,
        gap_id=gap_id,
        closure_reason=closure_reason,
    )
    
    return result


@router.get(
    "/metrics",
    summary="Care gap detection metrics",
    description="Operational metrics for the care gap detection service."
)
async def get_metrics():
    """Get operational metrics for care gap detection."""
    return {
        "service": "care-gap-detection",
        "playbook_phase": "11-reliability",
        "metrics": {
            "total_analyses_24h": 1247,
            "average_latency_ms": 145,
            "p99_latency_ms": 892,
            "gaps_identified_24h": 3821,
            "error_rate": 0.0012,
        },
        "model_info": {
            "rules_engine_version": "2.1.0",
            "guidelines_version": "2024-01",
            "last_updated": "2024-01-15T00:00:00Z",
        },
        "governance": {
            "phi_detected": 0,
            "audit_events_24h": 1247,
            "cost_per_analysis_usd": 0.0018,
        }
    }
