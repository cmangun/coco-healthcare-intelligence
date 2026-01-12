"""
Tests for Care Gap Detection Workflow

Validates:
- Gap detection logic
- Clinical guideline application
- Risk score calculation
- Audit trail integrity
"""

import pytest
from datetime import date, datetime
from coco.workflows.care_gap_workflow import (
    CareGapWorkflow,
    CareGapType,
    CareGapPriority,
)


class TestCareGapWorkflow:
    """Test suite for Care Gap Detection."""
    
    @pytest.fixture
    def workflow(self):
        """Create workflow instance."""
        return CareGapWorkflow()
    
    @pytest.mark.asyncio
    async def test_detect_gaps_returns_response(self, workflow):
        """Test that gap detection returns valid response."""
        result = await workflow.detect_gaps(patient_id="TEST-001")
        
        assert result.patient_id == "TEST-001"
        assert isinstance(result.analysis_timestamp, datetime)
        assert isinstance(result.total_gaps, int)
        assert 0 <= result.risk_score <= 1
        assert isinstance(result.care_gaps, list)
        assert isinstance(result.recommendations, list)
        assert "entries" in result.audit_trail
    
    @pytest.mark.asyncio
    async def test_gaps_have_required_fields(self, workflow):
        """Test that each gap has all required fields."""
        result = await workflow.detect_gaps(patient_id="TEST-001")
        
        for gap in result.care_gaps:
            assert gap.gap_id is not None
            assert gap.type in CareGapType
            assert gap.name is not None
            assert gap.description is not None
            assert gap.guideline_source is not None
            assert isinstance(gap.due_date, date)
            assert gap.priority in CareGapPriority
            assert 0 <= gap.estimated_impact <= 1
    
    @pytest.mark.asyncio
    async def test_risk_score_calculation(self, workflow):
        """Test risk score is calculated correctly."""
        # Test with no gaps
        gaps = []
        score = workflow._calculate_risk_score(gaps)
        assert score == 0.0
    
    @pytest.mark.asyncio
    async def test_audit_trail_integrity(self, workflow):
        """Test audit trail has hash chain."""
        result = await workflow.detect_gaps(patient_id="TEST-001")
        
        audit = result.audit_trail
        assert "entries" in audit
        assert "hash" in audit
        
        if audit["entries"]:
            for entry in audit["entries"]:
                assert "id" in entry
                assert "timestamp" in entry
                assert "operation" in entry
                assert "hash" in entry
    
    @pytest.mark.asyncio
    async def test_cohort_analysis(self, workflow):
        """Test cohort analysis returns summary."""
        patient_ids = ["TEST-001", "TEST-002", "TEST-003"]
        
        summary = await workflow.analyze_cohort(patient_ids)
        
        assert summary.total_patients_analyzed == 3
        assert summary.patients_with_gaps >= 0
        assert summary.total_gaps_identified >= 0
        assert isinstance(summary.gaps_by_type, dict)
        assert isinstance(summary.gaps_by_priority, dict)
        assert 0 <= summary.average_risk_score <= 1
    
    @pytest.mark.asyncio
    async def test_close_gap(self, workflow):
        """Test gap closure."""
        result = await workflow.close_gap(
            patient_id="TEST-001",
            gap_id="GAP-001",
            closure_reason="Screening completed",
            closure_date=date.today(),
        )
        
        assert result["status"] == "closed"
        assert result["gap_id"] == "GAP-001"
        assert "audit_hash" in result


class TestCareGapGuidelines:
    """Test clinical guideline application."""
    
    @pytest.fixture
    def workflow(self):
        return CareGapWorkflow()
    
    def test_guidelines_loaded(self, workflow):
        """Test that guidelines are properly loaded."""
        assert "uspstf" in workflow.guidelines
        assert "acip" in workflow.guidelines
        assert "hedis" in workflow.guidelines
    
    def test_colorectal_screening_guideline(self, workflow):
        """Test colorectal screening guideline parameters."""
        guideline = workflow.guidelines["uspstf"]["colorectal_screening"]
        
        assert guideline["age_min"] == 45
        assert guideline["age_max"] == 75
        assert guideline["frequency_years"] == 10
        assert guideline["priority"] == CareGapPriority.HIGH
    
    def test_evaluate_gaps_for_diabetic(self, workflow):
        """Test gap evaluation for diabetic patient."""
        features = {
            "patient_id": "TEST-001",
            "age": 55,
            "gender": "female",
            "has_diabetes": True,
            "has_hypertension": True,
            "last_colonoscopy": None,
            "last_mammogram": "2022-01-01",
            "last_hba1c": "2023-06-01",
            "last_flu_shot": "2022-10-01",
        }
        
        gaps = workflow._evaluate_gaps(features)
        
        # Should have gaps for: colonoscopy, mammogram, HbA1c, eye exam, flu
        gap_names = [g.name for g in gaps]
        assert "Colorectal Cancer Screening" in gap_names
        assert any("Diabetic" in name for name in gap_names)


class TestCareGapRecommendations:
    """Test recommendation generation."""
    
    @pytest.fixture
    def workflow(self):
        return CareGapWorkflow()
    
    @pytest.mark.asyncio
    async def test_recommendations_generated(self, workflow):
        """Test that recommendations are generated."""
        result = await workflow.detect_gaps(patient_id="TEST-001")
        
        if result.care_gaps:
            assert len(result.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_high_priority_recommendation(self, workflow):
        """Test high priority gaps generate scheduling recommendation."""
        result = await workflow.detect_gaps(patient_id="TEST-001")
        
        high_priority_gaps = [
            g for g in result.care_gaps
            if g.priority in [CareGapPriority.CRITICAL, CareGapPriority.HIGH]
        ]
        
        if high_priority_gaps:
            assert any("high-priority" in r.lower() or "schedule" in r.lower() 
                      for r in result.recommendations)
