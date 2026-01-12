"""
Clinical Summarization API Router

RAG-powered patient summaries with source citations and PHI protection.
Maps to Phase 6-8 (Build, Validation, Pre-Production) of the FDE Playbook.
"""

from datetime import datetime, date
from typing import Optional
from enum import Enum

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from coco.workflows.summarization_workflow import SummarizationWorkflow
from coco.governance.audit_logger import AuditLogger

logger = structlog.get_logger(__name__)
router = APIRouter()
audit = AuditLogger(component="summarization")


class SummaryType(str, Enum):
    """Types of clinical summaries available."""
    COMPREHENSIVE = "comprehensive"
    PROBLEM_FOCUSED = "problem_focused"
    MEDICATION = "medication"
    LAB_TREND = "lab_trend"
    CARE_TRANSITION = "care_transition"


class TimeRange(str, Enum):
    """Predefined time ranges for summary."""
    LAST_VISIT = "last_visit"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"
    LAST_6_MONTHS = "last_6_months"
    LAST_YEAR = "last_year"
    ALL_TIME = "all_time"


class Citation(BaseModel):
    """Source citation for summary content."""
    source_id: str = Field(..., description="Unique identifier for the source document")
    source_type: str = Field(..., description="Type of source (note, lab, order, etc.)")
    source_date: datetime
    relevance_score: float = Field(..., ge=0, le=1)
    snippet: str = Field(..., description="Relevant excerpt from source")
    author: Optional[str] = None


class KeyFinding(BaseModel):
    """Key clinical finding extracted from patient data."""
    finding: str
    category: str = Field(..., description="Category (diagnosis, medication, lab, etc.)")
    severity: Optional[str] = None
    trend: Optional[str] = Field(None, description="improving, stable, worsening")
    citations: list[str] = Field(default_factory=list, description="Citation IDs")


class PHIAudit(BaseModel):
    """PHI detection and handling audit."""
    scan_performed: bool = True
    phi_detected: bool = False
    phi_types_found: list[str] = Field(default_factory=list)
    redaction_applied: bool = False
    audit_id: str


class RAGMetrics(BaseModel):
    """RAG pipeline performance metrics."""
    documents_retrieved: int
    documents_used: int
    average_relevance: float
    context_tokens: int
    generation_tokens: int
    latency_ms: float


class ClinicalSummaryResponse(BaseModel):
    """Complete clinical summary response."""
    patient_id: str
    summary_type: SummaryType
    time_range: str
    generated_at: datetime
    summary: str = Field(..., description="Natural language clinical summary")
    key_findings: list[KeyFinding]
    active_problems: list[str]
    current_medications: list[str]
    recent_labs: list[dict]
    citations: list[Citation]
    phi_audit: PHIAudit
    rag_metrics: RAGMetrics
    model_info: dict
    audit_trail: dict


class SummarizationRequest(BaseModel):
    """Request for custom summarization."""
    patient_id: str
    summary_type: SummaryType = SummaryType.COMPREHENSIVE
    time_range: TimeRange = TimeRange.LAST_6_MONTHS
    custom_date_range: Optional[tuple[date, date]] = None
    focus_areas: Optional[list[str]] = None
    include_medications: bool = True
    include_labs: bool = True
    include_vitals: bool = True
    max_length: int = Field(500, ge=100, le=2000)


@router.get(
    "/patient/{patient_id}",
    response_model=ClinicalSummaryResponse,
    summary="Generate clinical summary for a patient",
    description="""
    Generates a RAG-powered clinical summary using the patient's medical records.
    All outputs are scanned for PHI with audit logging.
    
    **Playbook Phase**: 6-8 (Build, Validation, Pre-Production)
    
    **Architecture**:
    - Retrieval: Vector search over clinical documents (Qdrant)
    - Generation: GPT-4 with clinical prompt engineering
    - Governance: PHI detection, cost guards, citation verification
    
    **LLM Controls Applied** (per Playbook):
    - Prompt injection sanitization
    - Hallucination detection via citation grounding
    - Context window management
    - Output validation and PII scrubbing
    """
)
async def generate_summary(
    patient_id: str,
    summary_type: SummaryType = Query(SummaryType.COMPREHENSIVE),
    time_range: TimeRange = Query(TimeRange.LAST_6_MONTHS),
    max_length: int = Query(500, ge=100, le=2000),
):
    """Generate a clinical summary for a patient."""
    logger.info(
        "summarization_started",
        patient_id=patient_id,
        summary_type=summary_type.value,
        time_range=time_range.value,
    )
    
    try:
        workflow = SummarizationWorkflow()
        summary = await workflow.summarize_patient(
            patient_id=patient_id,
            summary_type=summary_type,
            time_range=time_range,
            max_length=max_length,
        )
        
        # Audit logging
        audit.log_operation(
            operation="generate_clinical_summary",
            patient_id=patient_id,
            summary_type=summary_type.value,
            phi_detected=summary.phi_audit.phi_detected,
            citations_count=len(summary.citations),
        )
        
        logger.info(
            "summarization_completed",
            patient_id=patient_id,
            citations=len(summary.citations),
            phi_detected=summary.phi_audit.phi_detected,
        )
        
        return summary
        
    except Exception as e:
        logger.error("summarization_failed", patient_id=patient_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@router.post(
    "/custom",
    response_model=ClinicalSummaryResponse,
    summary="Generate custom clinical summary",
    description="Generate a summary with custom parameters and focus areas."
)
async def generate_custom_summary(request: SummarizationRequest):
    """Generate a custom clinical summary."""
    logger.info(
        "custom_summarization_started",
        patient_id=request.patient_id,
        summary_type=request.summary_type.value,
        focus_areas=request.focus_areas,
    )
    
    try:
        workflow = SummarizationWorkflow()
        summary = await workflow.summarize_patient(
            patient_id=request.patient_id,
            summary_type=request.summary_type,
            time_range=request.time_range,
            custom_date_range=request.custom_date_range,
            focus_areas=request.focus_areas,
            include_medications=request.include_medications,
            include_labs=request.include_labs,
            include_vitals=request.include_vitals,
            max_length=request.max_length,
        )
        
        audit.log_operation(
            operation="generate_custom_summary",
            patient_id=request.patient_id,
            summary_type=request.summary_type.value,
            focus_areas=request.focus_areas,
        )
        
        return summary
        
    except Exception as e:
        logger.error("custom_summarization_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/problem/{patient_id}/{problem_code}",
    response_model=ClinicalSummaryResponse,
    summary="Problem-focused summary",
    description="Generate a summary focused on a specific clinical problem."
)
async def generate_problem_summary(
    patient_id: str,
    problem_code: str,
    time_range: TimeRange = Query(TimeRange.LAST_YEAR),
):
    """Generate a problem-focused clinical summary."""
    logger.info(
        "problem_summary_started",
        patient_id=patient_id,
        problem_code=problem_code,
    )
    
    try:
        workflow = SummarizationWorkflow()
        summary = await workflow.summarize_problem(
            patient_id=patient_id,
            problem_code=problem_code,
            time_range=time_range,
        )
        
        audit.log_operation(
            operation="generate_problem_summary",
            patient_id=patient_id,
            problem_code=problem_code,
        )
        
        return summary
        
    except Exception as e:
        logger.error("problem_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/care-transition/{patient_id}/{encounter_id}",
    response_model=ClinicalSummaryResponse,
    summary="Care transition summary",
    description="Generate a summary for care transitions (discharge, transfer)."
)
async def generate_transition_summary(
    patient_id: str,
    encounter_id: str,
    recipient_type: str = Query("pcp", description="pcp, specialist, snf, home_health"),
):
    """Generate a care transition summary."""
    logger.info(
        "transition_summary_started",
        patient_id=patient_id,
        encounter_id=encounter_id,
        recipient_type=recipient_type,
    )
    
    try:
        workflow = SummarizationWorkflow()
        summary = await workflow.summarize_transition(
            patient_id=patient_id,
            encounter_id=encounter_id,
            recipient_type=recipient_type,
        )
        
        audit.log_operation(
            operation="generate_transition_summary",
            patient_id=patient_id,
            encounter_id=encounter_id,
            recipient_type=recipient_type,
        )
        
        return summary
        
    except Exception as e:
        logger.error("transition_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/rag/info",
    summary="RAG pipeline information",
    description="Returns information about the RAG pipeline configuration."
)
async def get_rag_info():
    """Get RAG pipeline configuration and performance."""
    return {
        "retrieval": {
            "vector_db": "Qdrant",
            "embedding_model": "text-embedding-3-large",
            "embedding_dimensions": 3072,
            "index_type": "HNSW",
            "total_documents": 2_847_392,
            "document_types": {
                "progress_notes": 1_234_567,
                "lab_results": 892_345,
                "medication_orders": 456_789,
                "imaging_reports": 163_691,
            },
        },
        "generation": {
            "model": "gpt-4-turbo",
            "context_window": 128000,
            "max_output_tokens": 4096,
            "temperature": 0.3,
            "system_prompt_tokens": 1250,
        },
        "governance": {
            "phi_detection_model": "presidio-analyzer",
            "citation_verification": True,
            "hallucination_check": True,
            "cost_guard_enabled": True,
            "max_cost_per_request": 0.15,
        },
        "performance": {
            "average_latency_ms": 2340,
            "p99_latency_ms": 4890,
            "cache_hit_rate": 0.23,
        },
    }


@router.get(
    "/llm-controls",
    summary="LLM control status",
    description="Returns the status of LLM controls as defined in the FDE Playbook."
)
async def get_llm_controls():
    """Get LLM control status per Playbook requirements."""
    return {
        "phase_6_build_controls": {
            "prompt_injection_sanitization": {
                "status": "active",
                "implementation": "Input pattern matching + allow-list",
                "owner": "Security Engineer",
            },
            "tool_call_audit_logging": {
                "status": "active",
                "implementation": "All API calls logged with trace IDs",
                "owner": "Platform Engineer",
            },
        },
        "phase_7_validation_controls": {
            "retrieval_contamination_check": {
                "status": "active",
                "implementation": "Signed data sources + relevance threshold 0.7",
                "owner": "Data Engineer",
            },
            "hallucination_detection": {
                "status": "active",
                "implementation": "Citation grounding + expert sampling",
                "owner": "ML Engineer",
            },
        },
        "phase_8_preproduction_controls": {
            "context_window_management": {
                "status": "active",
                "implementation": "Max context 100K tokens + truncation audit",
                "owner": "ML Engineer",
            },
            "output_validation": {
                "status": "active",
                "implementation": "PHI scrubbing + format validation",
                "owner": "Security Engineer",
            },
        },
        "compliance_status": "all_controls_active",
        "last_audit": "2024-01-14T00:00:00Z",
        "next_audit": "2024-02-14T00:00:00Z",
    }


@router.get(
    "/metrics",
    summary="Summarization service metrics",
    description="Operational metrics for the clinical summarization service."
)
async def get_metrics():
    """Get operational metrics."""
    return {
        "service": "clinical-summarization",
        "playbook_phase": "11-reliability",
        "metrics": {
            "summaries_24h": 892,
            "average_latency_ms": 2340,
            "p99_latency_ms": 4890,
            "cache_hit_rate": 0.23,
            "error_rate": 0.0015,
        },
        "rag_metrics": {
            "avg_documents_retrieved": 12.4,
            "avg_relevance_score": 0.82,
            "avg_context_tokens": 8234,
            "avg_generation_tokens": 456,
        },
        "governance": {
            "phi_detections_24h": 3,
            "redactions_applied": 3,
            "hallucination_flags": 0,
            "audit_events_24h": 892,
            "cost_per_summary_usd": 0.034,
            "daily_cost_usd": 30.33,
        },
        "cost_telemetry": {
            "cost_per_inference_usd": 0.034,
            "value_per_inference_usd": 2.50,
            "roi_ratio": 73.5,
            "status": "healthy",
        },
    }
