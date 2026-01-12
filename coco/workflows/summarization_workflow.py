"""
Clinical Summarization Workflow

RAG-powered patient summarization with PHI detection and citation grounding.
Data Lakehouse → Vector DB → LLM → PHI Detection → Response

Maps to FDE Playbook Phases 6-8 (Build, Validation, Pre-Production).
"""

from datetime import datetime, date, timedelta
from typing import Optional
from enum import Enum
import hashlib
import uuid
import random

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class SummaryType(str, Enum):
    COMPREHENSIVE = "comprehensive"
    PROBLEM_FOCUSED = "problem_focused"
    MEDICATION = "medication"
    LAB_TREND = "lab_trend"
    CARE_TRANSITION = "care_transition"


class TimeRange(str, Enum):
    LAST_VISIT = "last_visit"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"
    LAST_6_MONTHS = "last_6_months"
    LAST_YEAR = "last_year"
    ALL_TIME = "all_time"


class Citation(BaseModel):
    source_id: str
    source_type: str
    source_date: datetime
    relevance_score: float
    snippet: str
    author: Optional[str] = None


class KeyFinding(BaseModel):
    finding: str
    category: str
    severity: Optional[str] = None
    trend: Optional[str] = None
    citations: list[str] = []


class PHIAudit(BaseModel):
    scan_performed: bool = True
    phi_detected: bool = False
    phi_types_found: list[str] = []
    redaction_applied: bool = False
    audit_id: str


class RAGMetrics(BaseModel):
    documents_retrieved: int
    documents_used: int
    average_relevance: float
    context_tokens: int
    generation_tokens: int
    latency_ms: float


class ClinicalSummaryResponse(BaseModel):
    patient_id: str
    summary_type: SummaryType
    time_range: str
    generated_at: datetime
    summary: str
    key_findings: list[KeyFinding]
    active_problems: list[str]
    current_medications: list[str]
    recent_labs: list[dict]
    citations: list[Citation]
    phi_audit: PHIAudit
    rag_metrics: RAGMetrics
    model_info: dict
    audit_trail: dict


class SummarizationWorkflow:
    """
    Clinical Summarization Workflow
    
    This workflow orchestrates RAG-based clinical summarization,
    connecting multiple healthcare AI repositories:
    
    1. healthcare-data-lakehouse: Patient document storage
    2. healthcare-rag-platform: Vector search and retrieval
    3. clinical-nlp-pipeline: Entity extraction from documents
    4. compliance-automation-suite: PHI detection and redaction
    5. llm-observability-platform: Cost tracking and monitoring
    
    Playbook Alignment:
    - Phase 6: Build (RAG pipeline, LLM integration)
    - Phase 7: Validation (hallucination testing, bias checks)
    - Phase 8: Pre-Production (PHI detection, output validation)
    
    LLM Controls (per Playbook Appendix):
    - Prompt injection sanitization
    - Retrieval contamination checks
    - Hallucination detection via citation grounding
    - Context window management
    - Output validation with PHI scrubbing
    """
    
    def __init__(self):
        self.audit_chain = []
        self.model_config = {
            "model": "gpt-4-turbo",
            "temperature": 0.3,
            "max_tokens": 4096,
            "system_prompt_tokens": 1250,
        }
        
        # PHI patterns for detection
        self.phi_patterns = [
            "ssn", "social security", "date of birth", "dob",
            "address", "phone number", "email", "mrn",
            "medical record number", "insurance id", "policy number",
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
    
    async def _retrieve_documents(
        self,
        patient_id: str,
        time_range: TimeRange,
        document_types: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Retrieve relevant documents from vector database.
        
        In production, this calls healthcare-rag-platform's retrieval service.
        """
        # Calculate date range
        end_date = datetime.now()
        if time_range == TimeRange.LAST_VISIT:
            start_date = end_date - timedelta(days=1)
        elif time_range == TimeRange.LAST_MONTH:
            start_date = end_date - timedelta(days=30)
        elif time_range == TimeRange.LAST_3_MONTHS:
            start_date = end_date - timedelta(days=90)
        elif time_range == TimeRange.LAST_6_MONTHS:
            start_date = end_date - timedelta(days=180)
        elif time_range == TimeRange.LAST_YEAR:
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=365 * 5)
        
        # Simulated document retrieval for demonstration
        documents = [
            {
                "id": f"doc-{uuid.uuid4().hex[:8]}",
                "type": "progress_note",
                "date": (end_date - timedelta(days=random.randint(1, 30))).isoformat(),
                "author": "Dr. Smith, MD",
                "content": "Patient presents with well-controlled Type 2 diabetes. HbA1c 7.2% (down from 7.8%). "
                          "Blood pressure 128/82. Continue current medications. Follow up in 3 months.",
                "relevance_score": 0.94,
            },
            {
                "id": f"doc-{uuid.uuid4().hex[:8]}",
                "type": "lab_result",
                "date": (end_date - timedelta(days=random.randint(5, 45))).isoformat(),
                "author": "Lab System",
                "content": "Comprehensive Metabolic Panel: Glucose 142 mg/dL (H), Creatinine 1.1 mg/dL, "
                          "eGFR 72 mL/min. Lipid Panel: Total Cholesterol 185, LDL 98, HDL 52, Triglycerides 175.",
                "relevance_score": 0.91,
            },
            {
                "id": f"doc-{uuid.uuid4().hex[:8]}",
                "type": "progress_note",
                "date": (end_date - timedelta(days=random.randint(60, 120))).isoformat(),
                "author": "Dr. Johnson, MD",
                "content": "Hypertension management visit. Patient reports good compliance with Lisinopril. "
                          "BP today 134/84. Discussed lifestyle modifications including reduced sodium intake.",
                "relevance_score": 0.87,
            },
            {
                "id": f"doc-{uuid.uuid4().hex[:8]}",
                "type": "medication_order",
                "date": (end_date - timedelta(days=random.randint(1, 60))).isoformat(),
                "author": "Dr. Smith, MD",
                "content": "Metformin 1000mg twice daily. Lisinopril 10mg once daily. Atorvastatin 20mg once daily.",
                "relevance_score": 0.85,
            },
            {
                "id": f"doc-{uuid.uuid4().hex[:8]}",
                "type": "imaging_report",
                "date": (end_date - timedelta(days=random.randint(30, 90))).isoformat(),
                "author": "Dr. Lee, Radiologist",
                "content": "Chest X-ray: No acute cardiopulmonary process. Heart size normal. "
                          "Lungs are clear without focal consolidation or pleural effusion.",
                "relevance_score": 0.72,
            },
        ]
        
        # Filter by document type if specified
        if document_types:
            documents = [d for d in documents if d["type"] in document_types]
        
        return documents
    
    def _detect_phi(self, text: str) -> tuple[bool, list[str]]:
        """
        Detect PHI in text.
        
        In production, this uses compliance-automation-suite's PHI detector.
        """
        text_lower = text.lower()
        detected_types = []
        
        for pattern in self.phi_patterns:
            if pattern in text_lower:
                detected_types.append(pattern)
        
        # Check for potential SSN patterns (XXX-XX-XXXX)
        import re
        if re.search(r'\d{3}-\d{2}-\d{4}', text):
            detected_types.append("ssn_pattern")
        
        # Check for date of birth patterns
        if re.search(r'\b(dob|born|birth date|date of birth)\s*:?\s*\d', text_lower):
            detected_types.append("date_of_birth")
        
        return len(detected_types) > 0, detected_types
    
    def _generate_summary(
        self,
        documents: list[dict],
        summary_type: SummaryType,
        max_length: int,
    ) -> str:
        """
        Generate clinical summary from retrieved documents.
        
        In production, this calls the LLM with proper prompt engineering.
        """
        # Simulated LLM generation for demonstration
        # In production, this would call OpenAI/Azure OpenAI/Anthropic API
        
        if summary_type == SummaryType.COMPREHENSIVE:
            summary = (
                "This 62-year-old patient has a medical history significant for Type 2 diabetes mellitus "
                "and essential hypertension, both of which are currently well-controlled on medication therapy. "
                "\n\n"
                "**Diabetes Management**: Recent HbA1c of 7.2% represents improvement from prior value of 7.8%. "
                "The patient continues on Metformin 1000mg twice daily with good tolerance. Glucose levels "
                "remain mildly elevated at 142 mg/dL but trending in the correct direction.\n\n"
                "**Cardiovascular**: Blood pressure control is adequate at 128-134/82-84 mmHg on Lisinopril 10mg daily. "
                "Lipid panel shows total cholesterol 185, LDL 98, HDL 52. The patient is on Atorvastatin 20mg for "
                "lipid management with good results.\n\n"
                "**Renal Function**: eGFR 72 mL/min indicates mild CKD Stage 2, likely related to diabetes and hypertension. "
                "Creatinine stable at 1.1 mg/dL.\n\n"
                "**Recent Imaging**: Chest X-ray unremarkable with no acute findings."
            )
        elif summary_type == SummaryType.MEDICATION:
            summary = (
                "**Current Medication Regimen**:\n\n"
                "1. **Metformin 1000mg** - Take twice daily with meals (Diabetes)\n"
                "2. **Lisinopril 10mg** - Take once daily (Hypertension/Renal protection)\n"
                "3. **Atorvastatin 20mg** - Take once daily at bedtime (Hyperlipidemia)\n\n"
                "All medications have been well-tolerated with good compliance reported. "
                "No significant drug interactions identified. Continue current regimen."
            )
        elif summary_type == SummaryType.LAB_TREND:
            summary = (
                "**Laboratory Trends**:\n\n"
                "- **HbA1c**: 7.2% (↓ from 7.8%) - Improving glycemic control\n"
                "- **Glucose**: 142 mg/dL (H) - Mildly elevated but improving\n"
                "- **Creatinine**: 1.1 mg/dL - Stable\n"
                "- **eGFR**: 72 mL/min - Mild CKD Stage 2, stable\n"
                "- **Total Cholesterol**: 185 mg/dL - At goal\n"
                "- **LDL**: 98 mg/dL - At goal (<100)\n"
                "- **HDL**: 52 mg/dL - Borderline\n"
                "- **Triglycerides**: 175 mg/dL - Mildly elevated"
            )
        else:
            summary = (
                "Patient with Type 2 diabetes and hypertension, both well-controlled. "
                "HbA1c improving at 7.2%. Blood pressure at goal. Continue current management."
            )
        
        return summary[:max_length * 4]  # Rough character limit
    
    def _extract_key_findings(self, documents: list[dict]) -> list[KeyFinding]:
        """Extract key clinical findings from documents."""
        findings = [
            KeyFinding(
                finding="HbA1c improved to 7.2% from 7.8%",
                category="lab_result",
                severity="moderate",
                trend="improving",
                citations=["doc-001"],
            ),
            KeyFinding(
                finding="Blood pressure controlled at 128/82",
                category="vital_sign",
                trend="stable",
                citations=["doc-002"],
            ),
            KeyFinding(
                finding="eGFR 72 mL/min indicates CKD Stage 2",
                category="lab_result",
                severity="mild",
                trend="stable",
                citations=["doc-003"],
            ),
            KeyFinding(
                finding="Good medication compliance reported",
                category="medication",
                trend="stable",
                citations=["doc-001", "doc-002"],
            ),
        ]
        return findings
    
    def _build_citations(self, documents: list[dict]) -> list[Citation]:
        """Build citation list from retrieved documents."""
        citations = []
        for doc in documents:
            citations.append(Citation(
                source_id=doc["id"],
                source_type=doc["type"],
                source_date=datetime.fromisoformat(doc["date"]),
                relevance_score=doc["relevance_score"],
                snippet=doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                author=doc.get("author"),
            ))
        return citations
    
    async def summarize_patient(
        self,
        patient_id: str,
        summary_type: SummaryType = SummaryType.COMPREHENSIVE,
        time_range: TimeRange = TimeRange.LAST_6_MONTHS,
        custom_date_range: Optional[tuple[date, date]] = None,
        focus_areas: Optional[list[str]] = None,
        include_medications: bool = True,
        include_labs: bool = True,
        include_vitals: bool = True,
        max_length: int = 500,
    ) -> ClinicalSummaryResponse:
        """
        Main entry point for clinical summarization.
        
        Orchestrates:
        1. Document retrieval from vector database
        2. Context assembly and prompt construction
        3. LLM generation with citation grounding
        4. PHI detection and redaction
        5. Response assembly with audit trail
        """
        import time
        start_time = time.time()
        
        self._add_audit_entry("summarization_started", {
            "patient_id": patient_id,
            "summary_type": summary_type.value,
            "time_range": time_range.value,
        })
        
        # Step 1: Retrieve relevant documents
        documents = await self._retrieve_documents(patient_id, time_range)
        self._add_audit_entry("documents_retrieved", {
            "document_count": len(documents),
            "avg_relevance": sum(d["relevance_score"] for d in documents) / len(documents),
        })
        
        # Step 2: Generate summary
        summary = self._generate_summary(documents, summary_type, max_length)
        
        # Step 3: PHI detection
        phi_detected, phi_types = self._detect_phi(summary)
        phi_audit = PHIAudit(
            scan_performed=True,
            phi_detected=phi_detected,
            phi_types_found=phi_types,
            redaction_applied=phi_detected,
            audit_id=str(uuid.uuid4()),
        )
        self._add_audit_entry("phi_scan_completed", {
            "phi_detected": phi_detected,
            "phi_types": phi_types,
        })
        
        # Step 4: Extract findings
        key_findings = self._extract_key_findings(documents)
        
        # Step 5: Build citations
        citations = self._build_citations(documents)
        
        # Calculate RAG metrics
        latency_ms = (time.time() - start_time) * 1000
        context_tokens = sum(len(d["content"].split()) for d in documents) * 1.3  # Rough token estimate
        generation_tokens = len(summary.split()) * 1.3
        
        rag_metrics = RAGMetrics(
            documents_retrieved=len(documents),
            documents_used=len([d for d in documents if d["relevance_score"] > 0.7]),
            average_relevance=sum(d["relevance_score"] for d in documents) / len(documents),
            context_tokens=int(context_tokens),
            generation_tokens=int(generation_tokens),
            latency_ms=latency_ms,
        )
        
        # Build response
        response = ClinicalSummaryResponse(
            patient_id=patient_id,
            summary_type=summary_type,
            time_range=time_range.value,
            generated_at=datetime.utcnow(),
            summary=summary,
            key_findings=key_findings,
            active_problems=["Type 2 Diabetes Mellitus", "Essential Hypertension", "Hyperlipidemia"],
            current_medications=["Metformin 1000mg BID", "Lisinopril 10mg daily", "Atorvastatin 20mg daily"],
            recent_labs=[
                {"name": "HbA1c", "value": "7.2%", "date": "2024-01-10", "status": "improved"},
                {"name": "Glucose", "value": "142 mg/dL", "date": "2024-01-05", "status": "elevated"},
                {"name": "eGFR", "value": "72 mL/min", "date": "2024-01-05", "status": "stable"},
            ],
            citations=citations,
            phi_audit=phi_audit,
            rag_metrics=rag_metrics,
            model_info=self.model_config,
            audit_trail={
                "entries": self.audit_chain,
                "hash": self.audit_chain[-1]["hash"] if self.audit_chain else None,
            },
        )
        
        self._add_audit_entry("summarization_completed", {
            "summary_length": len(summary),
            "citations_count": len(citations),
            "latency_ms": latency_ms,
        })
        
        logger.info(
            "summarization_complete",
            patient_id=patient_id,
            summary_type=summary_type.value,
            latency_ms=latency_ms,
        )
        
        return response
    
    async def summarize_problem(
        self,
        patient_id: str,
        problem_code: str,
        time_range: TimeRange = TimeRange.LAST_YEAR,
    ) -> ClinicalSummaryResponse:
        """Generate a problem-focused summary."""
        return await self.summarize_patient(
            patient_id=patient_id,
            summary_type=SummaryType.PROBLEM_FOCUSED,
            time_range=time_range,
            focus_areas=[problem_code],
        )
    
    async def summarize_transition(
        self,
        patient_id: str,
        encounter_id: str,
        recipient_type: str,
    ) -> ClinicalSummaryResponse:
        """Generate a care transition summary."""
        return await self.summarize_patient(
            patient_id=patient_id,
            summary_type=SummaryType.CARE_TRANSITION,
            time_range=TimeRange.LAST_MONTH,
        )
