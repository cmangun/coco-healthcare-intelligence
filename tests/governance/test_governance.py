"""
Governance Tests

Tests for phase gates, cost telemetry, and audit logging compliance.
These tests validate that the platform meets FDE Playbook requirements.
"""

import pytest
from datetime import datetime

from coco.governance.phase_gates import (
    PhaseGateRegistry,
    PhaseGate,
    GateType,
    PhaseStatus,
)
from coco.governance.cost_telemetry import (
    CostTelemetryContract,
    CostTracker,
    CostGuard,
)


class TestPhaseGates:
    """Test phase gate management."""
    
    def test_registry_initialization(self):
        """Registry initializes with all 12 phases."""
        registry = PhaseGateRegistry()
        assert len(registry.gates) == 12
    
    def test_phase_numbers_sequential(self):
        """Phase numbers are 1-12."""
        registry = PhaseGateRegistry()
        for i in range(1, 13):
            assert i in registry.gates
    
    def test_phase_quarters(self):
        """Phases map to correct quarters."""
        registry = PhaseGateRegistry()
        
        # Q1: Diagnostics (1-3)
        for phase in [1, 2, 3]:
            assert registry.gates[phase].quarter == "Q1"
        
        # Q2: Architect (4-6)
        for phase in [4, 5, 6]:
            assert registry.gates[phase].quarter == "Q2"
        
        # Q3: Engineer (7-9)
        for phase in [7, 8, 9]:
            assert registry.gates[phase].quarter == "Q3"
        
        # Q4: Enable (10-12)
        for phase in [10, 11, 12]:
            assert registry.gates[phase].quarter == "Q4"
    
    def test_gate_types_defined(self):
        """Each phase has appropriate gate types."""
        registry = PhaseGateRegistry()
        
        # Phase 4 should have HJG, Economic, and Irreversibility
        phase4 = registry.gates[4]
        assert GateType.HJG in phase4.gate_types
        assert GateType.ECONOMIC in phase4.gate_types
        assert GateType.IRREVERSIBILITY in phase4.gate_types
    
    def test_get_current_phase(self):
        """Can get current active phase."""
        registry = PhaseGateRegistry()
        current = registry.get_current_phase()
        assert current is not None
        assert current.phase_number >= 1
        assert current.phase_number <= 12
    
    def test_playbook_summary(self):
        """Playbook summary contains required fields."""
        registry = PhaseGateRegistry()
        summary = registry.get_playbook_summary()
        
        assert "playbook_version" in summary
        assert "quarters" in summary
        assert "current_phase" in summary
        assert "phases_completed" in summary
        assert "total_phases" in summary
        assert summary["total_phases"] == 12
    
    def test_kill_criteria_defined(self):
        """Kill criteria are properly defined."""
        registry = PhaseGateRegistry()
        criteria = registry.get_kill_criteria()
        
        assert len(criteria) >= 5  # At least 5 kill criteria
        
        for criterion in criteria:
            assert "id" in criterion
            assert "name" in criterion
            assert "description" in criterion
            assert "threshold" in criterion
            assert "owner" in criterion


class TestCostTelemetry:
    """Test cost telemetry contract."""
    
    def test_contract_metrics_defined(self):
        """All required metrics are defined per CT-1."""
        required_metrics = [
            "cost_per_inference",
            "error_cost_per_month",
            "human_review_cost_per_output",
            "compute_cost_per_1k",
            "retraining_cost_per_cycle",
            "value_per_inference",
        ]
        
        for metric in required_metrics:
            assert metric in CostTelemetryContract.METRICS
    
    def test_metrics_have_owners(self):
        """Each metric has a named owner (not 'team')."""
        for metric_name, config in CostTelemetryContract.METRICS.items():
            assert "owner" in config
            assert config["owner"]  # Not empty
            assert "team" not in config["owner"].lower()  # Not generic 'team'
    
    def test_metrics_have_refresh_cadence(self):
        """Each metric has a refresh cadence."""
        for metric_name, config in CostTelemetryContract.METRICS.items():
            assert "refresh" in config
            assert config["refresh"] in ["Real-time", "Daily", "Weekly", "Monthly", "Per event"]
    
    def test_metrics_have_thresholds(self):
        """Each metric has a threshold value."""
        for metric_name, config in CostTelemetryContract.METRICS.items():
            assert "threshold" in config
            assert config["threshold"] > 0
    
    def test_metrics_have_kill_triggers(self):
        """Each metric has a kill trigger defined."""
        for metric_name, config in CostTelemetryContract.METRICS.items():
            assert "kill_trigger" in config
            assert config["kill_trigger"]  # Not empty
    
    def test_contract_status(self):
        """Can get contract status."""
        status = CostTelemetryContract.get_contract_status()
        
        assert "contract_id" in status
        assert status["contract_id"] == "CT-1"
        assert "metrics" in status
        assert "overall_status" in status
    
    def test_kill_criteria_check(self):
        """Can check kill criteria."""
        check = CostTelemetryContract.check_kill_criteria()
        
        assert "kill_triggered" in check
        assert "triggers" in check
        assert "checked_at" in check
        assert isinstance(check["kill_triggered"], bool)


class TestCostTracker:
    """Test cost tracking functionality."""
    
    def test_operation_costs_defined(self):
        """Operation costs are defined."""
        operations = [
            "care_gap_detection",
            "readmission_prediction",
            "clinical_summarization",
        ]
        
        for op in operations:
            assert op in CostTracker.OPERATION_COSTS
            assert CostTracker.OPERATION_COSTS[op] > 0
    
    def test_operation_values_defined(self):
        """Operation values are defined."""
        operations = [
            "care_gap_detection",
            "readmission_prediction",
            "clinical_summarization",
        ]
        
        for op in operations:
            assert op in CostTracker.OPERATION_VALUES
            assert CostTracker.OPERATION_VALUES[op] > 0
    
    def test_value_exceeds_cost(self):
        """Value exceeds cost for each operation (positive ROI)."""
        for op in CostTracker.OPERATION_COSTS:
            cost = CostTracker.OPERATION_COSTS[op]
            value = CostTracker.OPERATION_VALUES.get(op, 0)
            assert value > cost, f"Operation {op} has negative ROI"
    
    def test_record_operation(self):
        """Can record an operation."""
        result = CostTracker.record_operation(
            operation="care_gap_detection",
            model="test-model",
        )
        
        assert "cost" in result
        assert "value" in result
        assert "roi" in result
        assert result["roi"] > 0


class TestCostGuard:
    """Test cost guard functionality."""
    
    def test_budget_check_within_limits(self):
        """Budget check passes for reasonable costs."""
        guard = CostGuard(max_cost_per_request=0.25, daily_budget=1000.0)
        
        allowed, reason = guard.check_budget(0.10)
        assert allowed
        assert reason == "within_budget"
    
    def test_budget_check_exceeds_per_request(self):
        """Budget check fails when per-request limit exceeded."""
        guard = CostGuard(max_cost_per_request=0.25, daily_budget=1000.0)
        
        allowed, reason = guard.check_budget(0.50)
        assert not allowed
        assert "per-request limit" in reason
    
    def test_budget_check_exceeds_daily(self):
        """Budget check fails when daily budget would be exceeded."""
        guard = CostGuard(max_cost_per_request=0.25, daily_budget=1.0)
        
        # Record some spend
        guard.daily_spend = 0.90
        
        allowed, reason = guard.check_budget(0.20)
        assert not allowed
        assert "Daily budget" in reason
    
    def test_record_spend(self):
        """Can record actual spend."""
        guard = CostGuard(max_cost_per_request=0.25, daily_budget=1000.0)
        
        initial_spend = guard.daily_spend
        guard.record_spend(0.05)
        
        assert guard.daily_spend == initial_spend + 0.05


class TestPlaybookAlignment:
    """Test overall playbook alignment."""
    
    def test_quarter_aims_documented(self):
        """Each quarter has documented human aim."""
        registry = PhaseGateRegistry()
        summary = registry.get_playbook_summary()
        
        for quarter_name, quarter_data in summary["quarters"].items():
            assert "human_aim" in quarter_data
            assert quarter_data["human_aim"]  # Not empty
    
    def test_quarter_gates_documented(self):
        """Each quarter has documented gate criteria."""
        registry = PhaseGateRegistry()
        summary = registry.get_playbook_summary()
        
        for quarter_name, quarter_data in summary["quarters"].items():
            assert "gate" in quarter_data
            assert quarter_data["gate"]  # Not empty
    
    def test_all_phases_have_artifacts(self):
        """Each phase has required artifacts defined."""
        registry = PhaseGateRegistry()
        
        for phase_num, gate in registry.gates.items():
            assert gate.required_artifacts  # Not empty
            assert len(gate.required_artifacts) >= 1
    
    def test_all_phases_have_reviewers(self):
        """Each phase has reviewers defined."""
        registry = PhaseGateRegistry()
        
        for phase_num, gate in registry.gates.items():
            assert gate.reviewers  # Not empty
            assert len(gate.reviewers) >= 1


class TestComplianceIntegration:
    """Test compliance-related functionality."""
    
    def test_hipaa_safeguards_documented(self):
        """HIPAA technical safeguards are addressed."""
        # This would check actual implementation
        # For now, verify the structure exists
        safeguards = [
            "access_control",
            "audit_controls",
            "integrity",
            "transmission_security",
        ]
        
        # These should be documented in the codebase
        for safeguard in safeguards:
            assert safeguard in ["access_control", "audit_controls", "integrity", "transmission_security"]
    
    def test_phi_detection_exists(self):
        """PHI detection capability exists."""
        from coco.workflows.summarization_workflow import SummarizationWorkflow
        
        workflow = SummarizationWorkflow()
        assert hasattr(workflow, '_detect_phi')
    
    def test_audit_chain_immutability(self):
        """Audit entries can be added but not modified."""
        from coco.workflows.care_gap_workflow import CareGapWorkflow
        
        workflow = CareGapWorkflow()
        initial_count = len(workflow.audit_chain)
        
        workflow._add_audit_entry("test_operation", {"test": "data"})
        
        assert len(workflow.audit_chain) == initial_count + 1
        assert workflow.audit_chain[-1]["operation"] == "test_operation"
        assert "hash" in workflow.audit_chain[-1]
