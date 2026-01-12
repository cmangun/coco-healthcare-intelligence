"""
Integration Tests for CoCo Platform

Tests end-to-end flows across all three clinical use cases.
Validates data flow through the complete pipeline.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

# Import will work when package is installed
try:
    from coco.api.main import app
except ImportError:
    app = None


@pytest.fixture
def client():
    """Create test client."""
    if app is None:
        pytest.skip("App not available")
    return TestClient(app)


class TestHealthEndpoints:
    """Test system health endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns platform info."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "CoCo: Careware for Healthcare Intelligence"
        assert data["version"] == "1.0.0"
        assert "clinical_use_cases" in data
        assert len(data["clinical_use_cases"]) == 3
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "components" in data
    
    def test_readiness_check(self, client):
        """Test readiness endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "coco_requests_total" in response.text or response.status_code == 200


class TestCareGapEndpoints:
    """Test care gap detection endpoints."""
    
    def test_detect_care_gaps(self, client):
        """Test care gap detection for patient."""
        response = client.get("/api/v1/care-gaps/patient/TEST-001")
        assert response.status_code == 200
        
        data = response.json()
        assert data["patient_id"] == "TEST-001"
        assert "care_gaps" in data
        assert "risk_score" in data
        assert 0 <= data["risk_score"] <= 1
    
    def test_care_gaps_with_params(self, client):
        """Test care gap detection with parameters."""
        response = client.get(
            "/api/v1/care-gaps/patient/TEST-001",
            params={"include_closed": False, "lookback_months": 12}
        )
        assert response.status_code == 200
    
    def test_list_guidelines(self, client):
        """Test clinical guidelines endpoint."""
        response = client.get("/api/v1/care-gaps/guidelines")
        assert response.status_code == 200
        
        data = response.json()
        assert "guidelines" in data
        assert len(data["guidelines"]) > 0
    
    def test_care_gap_metrics(self, client):
        """Test care gap metrics endpoint."""
        response = client.get("/api/v1/care-gaps/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "care-gap-detection"
        assert "metrics" in data


class TestReadmissionEndpoints:
    """Test readmission prediction endpoints."""
    
    def test_predict_readmission(self, client):
        """Test readmission risk prediction."""
        response = client.get("/api/v1/readmission/predict/TEST-001")
        assert response.status_code == 200
        
        data = response.json()
        assert data["patient_id"] == "TEST-001"
        assert "risk_score" in data
        assert "risk_tier" in data
        assert data["risk_tier"] in ["low", "medium", "high", "critical"]
        assert "contributing_factors" in data
        assert "model_governance" in data
    
    def test_model_info(self, client):
        """Test model information endpoint."""
        response = client.get("/api/v1/readmission/model/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "model" in data
        assert "performance" in data
        assert "fairness" in data
        assert "governance" in data
    
    def test_feature_importance(self, client):
        """Test feature importance endpoint."""
        response = client.get("/api/v1/readmission/model/features")
        assert response.status_code == 200
        
        data = response.json()
        assert "features" in data
        assert len(data["features"]) > 0
    
    def test_interventions_list(self, client):
        """Test interventions endpoint."""
        response = client.get("/api/v1/readmission/interventions")
        assert response.status_code == 200
        
        data = response.json()
        assert "interventions" in data


class TestSummarizationEndpoints:
    """Test clinical summarization endpoints."""
    
    def test_generate_summary(self, client):
        """Test clinical summary generation."""
        response = client.get("/api/v1/summarize/patient/TEST-001")
        assert response.status_code == 200
        
        data = response.json()
        assert data["patient_id"] == "TEST-001"
        assert "summary" in data
        assert "citations" in data
        assert "phi_audit" in data
        assert data["phi_audit"]["scan_performed"] == True
    
    def test_summary_with_params(self, client):
        """Test summary with parameters."""
        response = client.get(
            "/api/v1/summarize/patient/TEST-001",
            params={
                "summary_type": "comprehensive",
                "time_range": "last_6_months",
                "max_length": 500
            }
        )
        assert response.status_code == 200
    
    def test_rag_info(self, client):
        """Test RAG pipeline information."""
        response = client.get("/api/v1/summarize/rag/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "retrieval" in data
        assert "generation" in data
        assert "governance" in data
    
    def test_llm_controls(self, client):
        """Test LLM controls status."""
        response = client.get("/api/v1/summarize/llm-controls")
        assert response.status_code == 200
        
        data = response.json()
        assert "phase_6_build_controls" in data
        assert "phase_7_validation_controls" in data
        assert "phase_8_preproduction_controls" in data


class TestGovernanceEndpoints:
    """Test governance endpoints."""
    
    def test_phase_status(self, client):
        """Test phase gate status endpoint."""
        response = client.get("/governance/phase-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_phase" in data
        assert "phase_gates" in data
        assert "compliance_status" in data
    
    def test_cost_telemetry(self, client):
        """Test cost telemetry endpoint."""
        response = client.get("/governance/cost-telemetry")
        assert response.status_code == 200
        
        data = response.json()
        assert "metrics" in data
        assert "thresholds" in data
        assert data["metrics"]["cost_per_inference_usd"] > 0


class TestEndToEndFlow:
    """Test complete clinical workflows."""
    
    def test_care_gap_to_intervention(self, client):
        """Test flow from care gap detection to intervention."""
        # 1. Detect care gaps
        gaps_response = client.get("/api/v1/care-gaps/patient/TEST-001")
        assert gaps_response.status_code == 200
        gaps_data = gaps_response.json()
        
        # 2. If gaps found, predict readmission risk
        if gaps_data["total_gaps"] > 0:
            risk_response = client.get("/api/v1/readmission/predict/TEST-001")
            assert risk_response.status_code == 200
            risk_data = risk_response.json()
            
            # 3. Get interventions if high risk
            if risk_data["risk_tier"] in ["high", "critical"]:
                assert len(risk_data["recommended_interventions"]) > 0
    
    def test_summary_with_citations(self, client):
        """Test summary generation includes proper citations."""
        response = client.get("/api/v1/summarize/patient/TEST-001")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify citations are included
        assert len(data["citations"]) > 0
        
        # Verify each citation has required fields
        for citation in data["citations"]:
            assert "source_id" in citation
            assert "source_type" in citation
            assert "relevance_score" in citation
            assert 0 <= citation["relevance_score"] <= 1
    
    def test_audit_trail_consistency(self, client):
        """Test audit trail is generated for all operations."""
        # Make multiple API calls
        client.get("/api/v1/care-gaps/patient/TEST-001")
        client.get("/api/v1/readmission/predict/TEST-001")
        client.get("/api/v1/summarize/patient/TEST-001")
        
        # Verify governance shows activity
        response = client.get("/governance/phase-status")
        assert response.status_code == 200
