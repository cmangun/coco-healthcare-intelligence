"""
Phase Gate Registry

Implements the 12-phase gate system from the FDE Playbook.
Each phase has explicit exit contracts: Truth, Economic, Risk, Ownership.

Playbook Reference: Phase Exit Contracts, Gate Types (HJG, $, ⚠, CT)
"""

from datetime import datetime
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


class GateType(str, Enum):
    """Gate types from FDE Playbook."""
    HJG = "human_judgment_gate"  # Requires explicit human decision
    ECONOMIC = "economic_gate"    # Requires ROI validation
    IRREVERSIBILITY = "irreversibility_flag"  # Decisions costly to unwind
    CT = "cost_telemetry"         # Metrics with named owners


class PhaseStatus(str, Enum):
    """Status of a phase."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    BLOCKED = "blocked"


@dataclass
class ExitContract:
    """Phase exit contract with four components."""
    truth_contract: dict = field(default_factory=dict)
    economic_contract: dict = field(default_factory=dict)
    risk_contract: dict = field(default_factory=dict)
    ownership_contract: dict = field(default_factory=dict)
    
    def is_complete(self) -> bool:
        """Check if all contracts are satisfied."""
        return all([
            self.truth_contract.get("satisfied", False),
            self.economic_contract.get("satisfied", False),
            self.risk_contract.get("satisfied", False),
            self.ownership_contract.get("satisfied", False),
        ])


@dataclass
class PhaseGate:
    """Individual phase gate."""
    phase_number: int
    phase_name: str
    quarter: str
    description: str
    gate_types: list[GateType]
    status: PhaseStatus = PhaseStatus.NOT_STARTED
    exit_contract: ExitContract = field(default_factory=ExitContract)
    evidence_pack_id: str = ""
    required_artifacts: list[str] = field(default_factory=list)
    reviewers: list[str] = field(default_factory=list)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class PhaseGateRegistry:
    """
    Registry of all 12 phase gates.
    
    Maps to FDE Playbook phases:
    - Q1 Diagnostics: Phases 1-3 (Ontology, Problem Space, Discovery)
    - Q2 Architect: Phases 4-6 (Alignment, Integration, Build)
    - Q3 Engineer: Phases 7-9 (Validation, Pre-Production, Hypercare)
    - Q4 Enable: Phases 10-12 (Production, Reliability, Continuous Improvement)
    """
    
    def __init__(self):
        self.gates = self._initialize_gates()
        self.kill_criteria = self._initialize_kill_criteria()
    
    def _initialize_gates(self) -> dict[int, PhaseGate]:
        """Initialize all 12 phase gates."""
        return {
            1: PhaseGate(
                phase_number=1,
                phase_name="Ontology",
                quarter="Q1",
                description="Define conceptual foundation - entities, relationships, boundaries",
                gate_types=[GateType.HJG],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH1-EVID-1",
                required_artifacts=[
                    "Expert stakeholder map",
                    "Concept glossary",
                    "Relationship diagram",
                    "Contested concept log",
                ],
                reviewers=["Domain Lead", "Product"],
            ),
            2: PhaseGate(
                phase_number=2,
                phase_name="Problem Space",
                quarter="Q1",
                description="Define boundaries, validate assumptions, stress-test problem definition",
                gate_types=[GateType.HJG, GateType.IRREVERSIBILITY],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH2-EVID-1",
                required_artifacts=[
                    "Boundary stress tests",
                    "Edge case matrix",
                    "Scope validation results",
                ],
                reviewers=["Tech Lead", "Product"],
            ),
            3: PhaseGate(
                phase_number=3,
                phase_name="Discovery",
                quarter="Q1",
                description="Gather requirements from multiple perspectives",
                gate_types=[GateType.HJG],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH3-EVID-1",
                required_artifacts=[
                    "Stakeholder interview notes",
                    "Data inventory",
                    "Regulatory constraint map",
                ],
                reviewers=["Product", "Compliance"],
            ),
            4: PhaseGate(
                phase_number=4,
                phase_name="Alignment & Design",
                quarter="Q2",
                description="Lock stakeholder alignment, design end-to-end architecture",
                gate_types=[GateType.HJG, GateType.ECONOMIC, GateType.IRREVERSIBILITY],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH4-EVID-1",
                required_artifacts=[
                    "Architecture ROI pack",
                    "Stakeholder sign-off matrix",
                    "Risk acceptance docs",
                ],
                reviewers=["Exec Sponsor", "Finance"],
            ),
            5: PhaseGate(
                phase_number=5,
                phase_name="Integration",
                quarter="Q2",
                description="Connect ML system to infrastructure, APIs, data sources",
                gate_types=[GateType.HJG],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH5-EVID-1",
                required_artifacts=[
                    "IaC validation logs",
                    "Schema version registry",
                    "Security scan results",
                ],
                reviewers=["Platform Lead", "Security"],
            ),
            6: PhaseGate(
                phase_number=6,
                phase_name="Build",
                quarter="Q2",
                description="Construct model, pipelines, infrastructure with reproducibility",
                gate_types=[GateType.HJG, GateType.CT],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH6-EVID-1",
                required_artifacts=[
                    "Baseline model metrics",
                    "Telemetry contract",
                    "Reproducibility proof",
                ],
                reviewers=["ML Lead", "SRE"],
            ),
            7: PhaseGate(
                phase_number=7,
                phase_name="Validation",
                quarter="Q3",
                description="Rigorous testing - functional, performance, fairness, security",
                gate_types=[GateType.HJG],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH7-EVID-1",
                required_artifacts=[
                    "Test suite results",
                    "Bias audit",
                    "Red team report",
                    "Pen test findings",
                ],
                reviewers=["QA Lead", "Security"],
            ),
            8: PhaseGate(
                phase_number=8,
                phase_name="Pre-Production",
                quarter="Q3",
                description="Staging environment, load testing, final sign-off",
                gate_types=[GateType.HJG, GateType.ECONOMIC, GateType.CT],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH8-EVID-1",
                required_artifacts=[
                    "Load test results",
                    "Canary metrics",
                    "Rollback verification",
                    "Kill drill results",
                ],
                reviewers=["SRE Lead", "Ops"],
            ),
            9: PhaseGate(
                phase_number=9,
                phase_name="Hypercare",
                quarter="Q3",
                description="Intensive post-launch support, high-touch monitoring",
                gate_types=[GateType.HJG],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH9-EVID-1",
                required_artifacts=[
                    "Launch checklist",
                    "Escalation log",
                    "Rapid iteration tracking",
                ],
                reviewers=["Product", "Support Lead"],
            ),
            10: PhaseGate(
                phase_number=10,
                phase_name="Production",
                quarter="Q4",
                description="Full production rollout with monitoring and scaling",
                gate_types=[GateType.HJG],
                status=PhaseStatus.APPROVED,
                evidence_pack_id="PH10-EVID-1",
                required_artifacts=[
                    "Deployment verification",
                    "Autoscaling proof",
                    "Rollback test results",
                ],
                reviewers=["SRE", "Platform Lead"],
            ),
            11: PhaseGate(
                phase_number=11,
                phase_name="Reliability",
                quarter="Q4",
                description="Establish operational excellence - observability, incident response",
                gate_types=[GateType.HJG],
                status=PhaseStatus.IN_PROGRESS,
                evidence_pack_id="PH11-EVID-1",
                required_artifacts=[
                    "Observability dashboard",
                    "On-call rotation",
                    "Decay detection baseline",
                ],
                reviewers=["SRE Lead", "ML Lead"],
            ),
            12: PhaseGate(
                phase_number=12,
                phase_name="Continuous Improvement",
                quarter="Q4",
                description="Automation, documentation, architecture reviews, ROI validation",
                gate_types=[GateType.HJG, GateType.ECONOMIC],
                status=PhaseStatus.NOT_STARTED,
                evidence_pack_id="PH12-EVID-1",
                required_artifacts=[
                    "Automation inventory",
                    "Knowledge transfer docs",
                    "Next iteration brief",
                ],
                reviewers=["Tech Lead", "Product"],
            ),
        }
    
    def _initialize_kill_criteria(self) -> list[dict]:
        """Initialize kill criteria from playbook."""
        return [
            {
                "id": "KILL-001",
                "name": "ROI Collapse",
                "description": "Cost per inference exceeds value for 2 consecutive months",
                "threshold": "cost_value_ratio > 1.0 for 60 days",
                "action": "Initiate sunset review",
                "owner": "CTO + CFO",
                "status": "not_triggered",
            },
            {
                "id": "KILL-002",
                "name": "Consequential Error Spike",
                "description": "Weighted error cost exceeds $50K in any month",
                "threshold": "error_cost_monthly > 50000",
                "action": "Convene incident review within 48 hours",
                "owner": "CTO",
                "status": "not_triggered",
            },
            {
                "id": "KILL-003",
                "name": "Compliance Gap",
                "description": "Any material compliance gap",
                "threshold": "compliance_gap = true",
                "action": "Halt new feature deployment",
                "owner": "General Counsel",
                "status": "not_triggered",
            },
            {
                "id": "KILL-004",
                "name": "Model Performance Decay",
                "description": "Accuracy drift exceeds 15% from baseline",
                "threshold": "accuracy_decay > 0.15",
                "action": "Trigger retraining or rollback",
                "owner": "ML Lead",
                "status": "not_triggered",
            },
            {
                "id": "KILL-005",
                "name": "PHI Exposure",
                "description": "Any confirmed PHI exposure incident",
                "threshold": "phi_exposure = true",
                "action": "Immediate system halt and incident response",
                "owner": "CISO + Compliance",
                "status": "not_triggered",
            },
        ]
    
    def get_gate(self, phase_number: int) -> Optional[PhaseGate]:
        """Get a specific phase gate."""
        return self.gates.get(phase_number)
    
    def get_current_phase(self) -> PhaseGate:
        """Get the current active phase."""
        for phase_num in range(1, 13):
            gate = self.gates[phase_num]
            if gate.status in [PhaseStatus.IN_PROGRESS, PhaseStatus.PENDING_REVIEW]:
                return gate
        # Default to production phase
        return self.gates[10]
    
    def get_all_gates(self) -> list[dict]:
        """Get all gates as serializable dicts."""
        return [
            {
                "phase_number": gate.phase_number,
                "phase_name": gate.phase_name,
                "quarter": gate.quarter,
                "description": gate.description,
                "gate_types": [gt.value for gt in gate.gate_types],
                "status": gate.status.value,
                "evidence_pack_id": gate.evidence_pack_id,
                "required_artifacts": gate.required_artifacts,
                "reviewers": gate.reviewers,
            }
            for gate in self.gates.values()
        ]
    
    def get_kill_criteria(self) -> list[dict]:
        """Get all kill criteria."""
        return self.kill_criteria
    
    def check_phase_exit(self, phase_number: int) -> dict:
        """Check if a phase can exit."""
        gate = self.gates.get(phase_number)
        if not gate:
            return {"error": f"Phase {phase_number} not found"}
        
        return {
            "phase": phase_number,
            "phase_name": gate.phase_name,
            "can_exit": gate.exit_contract.is_complete(),
            "contracts": {
                "truth": gate.exit_contract.truth_contract,
                "economic": gate.exit_contract.economic_contract,
                "risk": gate.exit_contract.risk_contract,
                "ownership": gate.exit_contract.ownership_contract,
            },
            "missing_artifacts": [
                a for a in gate.required_artifacts
                # Would check actual artifact existence
            ],
        }
    
    def approve_phase(
        self,
        phase_number: int,
        approver: str,
        evidence: dict,
    ) -> dict:
        """Approve a phase gate."""
        gate = self.gates.get(phase_number)
        if not gate:
            return {"error": f"Phase {phase_number} not found"}
        
        gate.status = PhaseStatus.APPROVED
        gate.approved_at = datetime.utcnow()
        gate.approved_by = approver
        
        logger.info(
            "phase_gate_approved",
            phase=phase_number,
            phase_name=gate.phase_name,
            approver=approver,
        )
        
        return {
            "status": "approved",
            "phase": phase_number,
            "approved_at": gate.approved_at.isoformat(),
            "approved_by": approver,
        }
    
    def get_playbook_summary(self) -> dict:
        """Get summary aligned with playbook structure."""
        quarters = {
            "Q1_Diagnostics": {
                "phases": [1, 2, 3],
                "human_aim": "Align people on reality before building anything expensive",
                "gate": "Problem & success definition locked; baseline approved",
                "status": "complete",
            },
            "Q2_Architect": {
                "phases": [4, 5, 6],
                "human_aim": "Reduce ambiguity so teams stop arguing and start shipping",
                "gate": "Architecture review passed; security/compliance accepted",
                "status": "complete",
            },
            "Q3_Engineer": {
                "phases": [7, 8, 9],
                "human_aim": "Build with guardrails so operators don't carry risk",
                "gate": "Validation suite green; risk controls implemented",
                "status": "complete",
            },
            "Q4_Enable": {
                "phases": [10, 11, 12],
                "human_aim": "Make the system survivable after handoff",
                "gate": "Production readiness met; monitoring live; owner assigned",
                "status": "in_progress",
            },
        }
        
        return {
            "playbook_version": "7.5",
            "playbook_url": "https://enterprise-ai-playbook-demo.vercel.app/",
            "quarters": quarters,
            "current_phase": self.get_current_phase().phase_number,
            "phases_completed": sum(
                1 for g in self.gates.values() 
                if g.status == PhaseStatus.APPROVED
            ),
            "total_phases": 12,
        }
