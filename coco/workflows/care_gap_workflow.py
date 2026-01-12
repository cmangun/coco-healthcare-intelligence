"""
Care Gap Detection Workflow

Orchestrates the care gap detection pipeline:
FHIR Integration → Data Lakehouse → Feature Store → Rules Engine → Response

Maps to FDE Playbook Phases 4-6 (Architect).
"""

from datetime import datetime, date, timedelta
from typing import Optional
from enum import Enum
import hashlib
import uuid

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CareGapPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CareGapType(str, Enum):
    SCREENING = "screening"
    VACCINATION = "vaccination"
    LAB_TEST = "lab_test"
    MEDICATION = "medication"
    FOLLOW_UP = "follow_up"


class CareGap(BaseModel):
    gap_id: str
    type: CareGapType
    name: str
    description: str
    guideline_source: str
    due_date: date
    priority: CareGapPriority
    icd10_codes: list[str] = []
    cpt_codes: list[str] = []
    estimated_impact: float


class CareGapResponse(BaseModel):
    patient_id: str
    analysis_timestamp: datetime
    total_gaps: int
    risk_score: float
    care_gaps: list[CareGap]
    recommendations: list[str]
    audit_trail: dict


class CareGapSummary(BaseModel):
    total_patients_analyzed: int
    patients_with_gaps: int
    total_gaps_identified: int
    gaps_by_type: dict[str, int]
    gaps_by_priority: dict[str, int]
    average_risk_score: float


class CareGapWorkflow:
    """
    Care Gap Detection Workflow
    
    This workflow orchestrates the complete care gap detection pipeline,
    connecting multiple healthcare AI repositories:
    
    1. fhir-integration-service: Patient data ingestion
    2. healthcare-data-lakehouse: Data storage and transformation
    3. feature-store-healthcare: Feature retrieval for gap detection
    4. compliance-automation-suite: HIPAA compliance checks
    
    Playbook Alignment:
    - Phase 4: Alignment & Design (pipeline architecture)
    - Phase 5: Integration (FHIR, feature store connections)
    - Phase 6: Build (rules engine implementation)
    """
    
    def __init__(self):
        self.guidelines = self._load_clinical_guidelines()
        self.audit_chain = []
        
    def _load_clinical_guidelines(self) -> dict:
        """Load clinical guidelines for gap detection."""
        return {
            "uspstf": {
                "colorectal_screening": {
                    "name": "Colorectal Cancer Screening",
                    "age_min": 45,
                    "age_max": 75,
                    "frequency_years": 10,
                    "methods": ["colonoscopy", "fit_test", "cologuard"],
                    "priority": CareGapPriority.HIGH,
                },
                "breast_cancer_screening": {
                    "name": "Breast Cancer Screening (Mammography)",
                    "gender": "female",
                    "age_min": 40,
                    "age_max": 74,
                    "frequency_years": 2,
                    "priority": CareGapPriority.HIGH,
                },
                "cervical_screening": {
                    "name": "Cervical Cancer Screening",
                    "gender": "female",
                    "age_min": 21,
                    "age_max": 65,
                    "frequency_years": 3,
                    "priority": CareGapPriority.MEDIUM,
                },
                "diabetes_screening": {
                    "name": "Diabetes Screening",
                    "age_min": 35,
                    "age_max": 70,
                    "frequency_years": 3,
                    "risk_factors": ["overweight", "obesity"],
                    "priority": CareGapPriority.MEDIUM,
                },
            },
            "acip": {
                "influenza": {
                    "name": "Annual Influenza Vaccination",
                    "age_min": 6,  # months
                    "frequency_months": 12,
                    "priority": CareGapPriority.MEDIUM,
                },
                "covid19": {
                    "name": "COVID-19 Vaccination",
                    "age_min": 6,  # months
                    "priority": CareGapPriority.MEDIUM,
                },
                "pneumococcal": {
                    "name": "Pneumococcal Vaccination",
                    "age_min": 65,
                    "priority": CareGapPriority.MEDIUM,
                },
                "shingles": {
                    "name": "Shingles Vaccination",
                    "age_min": 50,
                    "priority": CareGapPriority.LOW,
                },
            },
            "hedis": {
                "hba1c_control": {
                    "name": "HbA1c Testing for Diabetics",
                    "conditions": ["E11", "E10"],  # ICD-10 diabetes codes
                    "frequency_months": 6,
                    "priority": CareGapPriority.HIGH,
                },
                "eye_exam_diabetes": {
                    "name": "Diabetic Eye Exam",
                    "conditions": ["E11", "E10"],
                    "frequency_years": 1,
                    "priority": CareGapPriority.HIGH,
                },
                "bp_control": {
                    "name": "Blood Pressure Control",
                    "conditions": ["I10", "I11", "I12", "I13"],  # Hypertension
                    "frequency_months": 3,
                    "priority": CareGapPriority.HIGH,
                },
            },
        }
    
    def _generate_audit_hash(self, data: dict) -> str:
        """Generate hash for audit chain integrity."""
        previous_hash = self.audit_chain[-1]["hash"] if self.audit_chain else "genesis"
        content = f"{previous_hash}:{str(data)}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _add_audit_entry(self, operation: str, details: dict):
        """Add entry to audit chain."""
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "operation": operation,
            "details": details,
            "hash": self._generate_audit_hash(details),
        }
        self.audit_chain.append(entry)
    
    async def _fetch_patient_data(self, patient_id: str) -> dict:
        """
        Fetch patient data from FHIR Integration Service.
        
        In production, this calls the fhir-integration-service.
        """
        # Simulated patient data for demonstration
        return {
            "patient_id": patient_id,
            "demographics": {
                "age": 58,
                "gender": "female",
                "race": "white",
            },
            "conditions": [
                {"code": "E11.9", "description": "Type 2 diabetes", "onset": "2019-03-15"},
                {"code": "I10", "description": "Hypertension", "onset": "2018-07-22"},
            ],
            "procedures": [
                {"code": "45378", "description": "Colonoscopy", "date": "2019-06-15"},
                {"code": "77067", "description": "Mammography", "date": "2023-08-20"},
            ],
            "labs": [
                {"code": "4548-4", "name": "HbA1c", "value": 7.2, "date": "2023-10-15"},
                {"code": "2345-7", "name": "Glucose", "value": 142, "date": "2023-12-01"},
            ],
            "immunizations": [
                {"code": "141", "name": "Influenza", "date": "2023-10-01"},
                {"code": "208", "name": "COVID-19", "date": "2023-09-15"},
            ],
            "medications": [
                {"name": "Metformin", "dose": "1000mg", "frequency": "twice daily"},
                {"name": "Lisinopril", "dose": "10mg", "frequency": "once daily"},
            ],
        }
    
    async def _retrieve_features(self, patient_id: str, patient_data: dict) -> dict:
        """
        Retrieve features from Feature Store.
        
        In production, this calls feature-store-healthcare.
        """
        # Calculate derived features
        age = patient_data["demographics"]["age"]
        has_diabetes = any(
            c["code"].startswith("E11") or c["code"].startswith("E10")
            for c in patient_data["conditions"]
        )
        has_hypertension = any(
            c["code"].startswith("I10") or c["code"].startswith("I11")
            for c in patient_data["conditions"]
        )
        
        return {
            "patient_id": patient_id,
            "age": age,
            "gender": patient_data["demographics"]["gender"],
            "has_diabetes": has_diabetes,
            "has_hypertension": has_hypertension,
            "last_colonoscopy": "2019-06-15" if any(
                p["code"] == "45378" for p in patient_data["procedures"]
            ) else None,
            "last_mammogram": "2023-08-20" if any(
                p["code"] == "77067" for p in patient_data["procedures"]
            ) else None,
            "last_hba1c": "2023-10-15",
            "last_flu_shot": "2023-10-01",
            "medication_count": len(patient_data["medications"]),
            "condition_count": len(patient_data["conditions"]),
        }
    
    def _evaluate_gaps(self, features: dict) -> list[CareGap]:
        """
        Evaluate care gaps based on clinical guidelines.
        
        This is the core rules engine that applies clinical guidelines
        to patient features to identify care gaps.
        """
        gaps = []
        today = date.today()
        
        # Colorectal screening (age 45-75, every 10 years)
        if 45 <= features["age"] <= 75:
            last_colonoscopy = features.get("last_colonoscopy")
            if last_colonoscopy:
                last_date = datetime.strptime(last_colonoscopy, "%Y-%m-%d").date()
                next_due = last_date + timedelta(days=365 * 10)
                if next_due <= today + timedelta(days=90):
                    gaps.append(CareGap(
                        gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                        type=CareGapType.SCREENING,
                        name="Colorectal Cancer Screening",
                        description="Due for colonoscopy based on 10-year screening interval",
                        guideline_source="USPSTF 2021",
                        due_date=next_due,
                        priority=CareGapPriority.HIGH,
                        icd10_codes=["Z12.11"],
                        cpt_codes=["45378", "45380"],
                        estimated_impact=0.85,
                    ))
            else:
                # Never had colonoscopy
                gaps.append(CareGap(
                    gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                    type=CareGapType.SCREENING,
                    name="Colorectal Cancer Screening",
                    description="No colonoscopy on record; screening recommended for age 45+",
                    guideline_source="USPSTF 2021",
                    due_date=today,
                    priority=CareGapPriority.HIGH,
                    icd10_codes=["Z12.11"],
                    cpt_codes=["45378", "45380"],
                    estimated_impact=0.90,
                ))
        
        # Breast cancer screening (female, 40-74, every 2 years)
        if features["gender"] == "female" and 40 <= features["age"] <= 74:
            last_mammogram = features.get("last_mammogram")
            if last_mammogram:
                last_date = datetime.strptime(last_mammogram, "%Y-%m-%d").date()
                next_due = last_date + timedelta(days=365 * 2)
                if next_due <= today + timedelta(days=90):
                    gaps.append(CareGap(
                        gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                        type=CareGapType.SCREENING,
                        name="Breast Cancer Screening",
                        description="Due for mammography based on 2-year screening interval",
                        guideline_source="USPSTF 2024",
                        due_date=next_due,
                        priority=CareGapPriority.HIGH,
                        icd10_codes=["Z12.31"],
                        cpt_codes=["77067"],
                        estimated_impact=0.80,
                    ))
        
        # Diabetic care gaps
        if features.get("has_diabetes"):
            # HbA1c every 6 months
            last_hba1c = features.get("last_hba1c")
            if last_hba1c:
                last_date = datetime.strptime(last_hba1c, "%Y-%m-%d").date()
                next_due = last_date + timedelta(days=180)
                if next_due <= today + timedelta(days=30):
                    gaps.append(CareGap(
                        gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                        type=CareGapType.LAB_TEST,
                        name="HbA1c Testing",
                        description="Due for HbA1c monitoring per diabetes management guidelines",
                        guideline_source="HEDIS 2024",
                        due_date=next_due,
                        priority=CareGapPriority.HIGH,
                        icd10_codes=["E11.9"],
                        cpt_codes=["83036"],
                        estimated_impact=0.75,
                    ))
            
            # Annual diabetic eye exam
            gaps.append(CareGap(
                gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                type=CareGapType.SCREENING,
                name="Diabetic Eye Exam",
                description="Annual dilated eye exam recommended for diabetes management",
                guideline_source="ADA Standards 2024",
                due_date=today + timedelta(days=60),
                priority=CareGapPriority.MEDIUM,
                icd10_codes=["E11.9", "Z13.5"],
                cpt_codes=["92004", "92014"],
                estimated_impact=0.70,
            ))
        
        # Annual flu vaccination
        last_flu = features.get("last_flu_shot")
        if last_flu:
            last_date = datetime.strptime(last_flu, "%Y-%m-%d").date()
            if (today - last_date).days > 365:
                gaps.append(CareGap(
                    gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                    type=CareGapType.VACCINATION,
                    name="Annual Influenza Vaccination",
                    description="Due for annual flu shot",
                    guideline_source="ACIP 2024",
                    due_date=today,
                    priority=CareGapPriority.MEDIUM,
                    icd10_codes=["Z23"],
                    cpt_codes=["90688"],
                    estimated_impact=0.60,
                ))
        
        # Pneumococcal vaccination (age 65+)
        if features["age"] >= 65:
            gaps.append(CareGap(
                gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                type=CareGapType.VACCINATION,
                name="Pneumococcal Vaccination",
                description="Pneumococcal vaccine recommended for adults 65+",
                guideline_source="ACIP 2024",
                due_date=today + timedelta(days=30),
                priority=CareGapPriority.MEDIUM,
                icd10_codes=["Z23"],
                cpt_codes=["90670", "90671"],
                estimated_impact=0.55,
            ))
        
        return gaps
    
    def _calculate_risk_score(self, gaps: list[CareGap]) -> float:
        """Calculate overall care gap risk score."""
        if not gaps:
            return 0.0
        
        priority_weights = {
            CareGapPriority.CRITICAL: 1.0,
            CareGapPriority.HIGH: 0.8,
            CareGapPriority.MEDIUM: 0.5,
            CareGapPriority.LOW: 0.2,
        }
        
        weighted_sum = sum(
            priority_weights[gap.priority] * gap.estimated_impact
            for gap in gaps
        )
        
        # Normalize to 0-1 range
        max_possible = len(gaps) * 1.0  # If all were critical with 1.0 impact
        return min(weighted_sum / max_possible, 1.0) if max_possible > 0 else 0.0
    
    def _generate_recommendations(self, gaps: list[CareGap]) -> list[str]:
        """Generate actionable recommendations based on gaps."""
        recommendations = []
        
        high_priority = [g for g in gaps if g.priority in [CareGapPriority.CRITICAL, CareGapPriority.HIGH]]
        if high_priority:
            recommendations.append(
                f"Schedule appointments for {len(high_priority)} high-priority care gaps within 30 days"
            )
        
        screenings = [g for g in gaps if g.type == CareGapType.SCREENING]
        if screenings:
            recommendations.append(
                f"Preventive screenings needed: {', '.join(g.name for g in screenings)}"
            )
        
        vaccinations = [g for g in gaps if g.type == CareGapType.VACCINATION]
        if vaccinations:
            recommendations.append(
                f"Vaccinations due: {', '.join(g.name for g in vaccinations)}"
            )
        
        if any(g.type == CareGapType.LAB_TEST for g in gaps):
            recommendations.append(
                "Order pending laboratory tests for chronic disease monitoring"
            )
        
        return recommendations
    
    async def detect_gaps(
        self,
        patient_id: str,
        include_closed: bool = False,
        lookback_months: int = 24,
    ) -> CareGapResponse:
        """
        Main entry point for care gap detection.
        
        Orchestrates the complete pipeline:
        1. Fetch patient data from FHIR
        2. Retrieve features from Feature Store
        3. Apply clinical guidelines (rules engine)
        4. Generate recommendations
        5. Create audit trail
        """
        self._add_audit_entry("detect_gaps_started", {
            "patient_id": patient_id,
            "lookback_months": lookback_months,
        })
        
        # Step 1: Fetch patient data
        patient_data = await self._fetch_patient_data(patient_id)
        self._add_audit_entry("patient_data_fetched", {
            "conditions_count": len(patient_data["conditions"]),
            "procedures_count": len(patient_data["procedures"]),
        })
        
        # Step 2: Retrieve features
        features = await self._retrieve_features(patient_id, patient_data)
        self._add_audit_entry("features_retrieved", {
            "feature_count": len(features),
        })
        
        # Step 3: Evaluate gaps
        gaps = self._evaluate_gaps(features)
        self._add_audit_entry("gaps_evaluated", {
            "gaps_found": len(gaps),
        })
        
        # Step 4: Calculate risk score
        risk_score = self._calculate_risk_score(gaps)
        
        # Step 5: Generate recommendations
        recommendations = self._generate_recommendations(gaps)
        
        # Build response
        response = CareGapResponse(
            patient_id=patient_id,
            analysis_timestamp=datetime.utcnow(),
            total_gaps=len(gaps),
            risk_score=risk_score,
            care_gaps=gaps,
            recommendations=recommendations,
            audit_trail={
                "entries": self.audit_chain,
                "hash": self.audit_chain[-1]["hash"] if self.audit_chain else None,
            },
        )
        
        self._add_audit_entry("detect_gaps_completed", {
            "total_gaps": len(gaps),
            "risk_score": risk_score,
        })
        
        logger.info(
            "care_gap_detection_complete",
            patient_id=patient_id,
            gaps_found=len(gaps),
            risk_score=risk_score,
        )
        
        return response
    
    async def analyze_cohort(
        self,
        patient_ids: list[str],
        gap_types: Optional[list[CareGapType]] = None,
        min_priority: Optional[CareGapPriority] = None,
    ) -> CareGapSummary:
        """Analyze care gaps across a patient cohort."""
        all_gaps = []
        patients_with_gaps = 0
        total_risk = 0.0
        
        for patient_id in patient_ids:
            result = await self.detect_gaps(patient_id)
            if result.care_gaps:
                patients_with_gaps += 1
                all_gaps.extend(result.care_gaps)
            total_risk += result.risk_score
        
        # Filter by type if specified
        if gap_types:
            all_gaps = [g for g in all_gaps if g.type in gap_types]
        
        # Filter by priority if specified
        if min_priority:
            priority_order = [CareGapPriority.CRITICAL, CareGapPriority.HIGH, 
                            CareGapPriority.MEDIUM, CareGapPriority.LOW]
            min_index = priority_order.index(min_priority)
            allowed = priority_order[:min_index + 1]
            all_gaps = [g for g in all_gaps if g.priority in allowed]
        
        # Calculate summary statistics
        gaps_by_type = {}
        gaps_by_priority = {}
        for gap in all_gaps:
            gaps_by_type[gap.type.value] = gaps_by_type.get(gap.type.value, 0) + 1
            gaps_by_priority[gap.priority.value] = gaps_by_priority.get(gap.priority.value, 0) + 1
        
        return CareGapSummary(
            total_patients_analyzed=len(patient_ids),
            patients_with_gaps=patients_with_gaps,
            total_gaps_identified=len(all_gaps),
            gaps_by_type=gaps_by_type,
            gaps_by_priority=gaps_by_priority,
            average_risk_score=total_risk / len(patient_ids) if patient_ids else 0.0,
        )
    
    async def close_gap(
        self,
        patient_id: str,
        gap_id: str,
        closure_reason: str,
        closure_date: date,
    ) -> dict:
        """Close a care gap after intervention."""
        self._add_audit_entry("gap_closed", {
            "patient_id": patient_id,
            "gap_id": gap_id,
            "closure_reason": closure_reason,
            "closure_date": closure_date.isoformat(),
        })
        
        return {
            "status": "closed",
            "gap_id": gap_id,
            "patient_id": patient_id,
            "closure_date": closure_date.isoformat(),
            "closure_reason": closure_reason,
            "audit_hash": self.audit_chain[-1]["hash"],
        }
