"""
Cost Telemetry Middleware and Contract

Implements the Cost Telemetry Contract (CT-1) from the FDE Playbook.
Each metric has a named owner, refresh cadence, and kill binding.

Playbook Reference: Cost Telemetry Contract Section
"""

from datetime import datetime
from typing import Optional
import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from prometheus_client import Counter, Histogram, Gauge

logger = structlog.get_logger(__name__)

# Prometheus metrics for cost telemetry
INFERENCE_COST = Counter(
    "coco_inference_cost_usd_total",
    "Total inference cost in USD",
    ["model", "operation"]
)
INFERENCE_VALUE = Counter(
    "coco_inference_value_usd_total",
    "Total value delivered by inferences in USD",
    ["model", "operation"]
)
COST_PER_INFERENCE = Histogram(
    "coco_cost_per_inference_usd",
    "Cost per inference in USD",
    ["model", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)
HUMAN_REVIEW_COST = Counter(
    "coco_human_review_cost_usd_total",
    "Cost of human review in USD",
    ["operation"]
)
CURRENT_ROI_RATIO = Gauge(
    "coco_roi_ratio",
    "Current ROI ratio (value/cost)",
    ["model"]
)


class CostTelemetryContract:
    """
    Cost Telemetry Contract (CT-1)
    
    Per FDE Playbook requirements, each metric must have:
    - Named human owner (not "team")
    - Defined refresh cadence
    - Review forum
    - Binding to specific kill threshold
    
    Systems without complete telemetry contracts do not ship.
    """
    
    METRICS = {
        "cost_per_inference": {
            "owner": "Engineering Manager",
            "refresh": "Daily",
            "reviewed_by": "CTO + CFO",
            "kill_trigger": ">1.0× value for 2 months",
            "current_value": 0.0023,
            "threshold": 0.05,
        },
        "error_cost_per_month": {
            "owner": "Product Manager",
            "refresh": "Weekly",
            "reviewed_by": "Executive Review",
            "kill_trigger": ">$50K/month",
            "current_value": 8234.50,
            "threshold": 50000.0,
        },
        "human_review_cost_per_output": {
            "owner": "Operations Lead",
            "refresh": "Weekly",
            "reviewed_by": "Ops Review",
            "kill_trigger": ">30% of inference cost",
            "current_value": 0.0004,
            "threshold": 0.015,  # 30% of 0.05
        },
        "compute_cost_per_1k": {
            "owner": "Platform Engineer",
            "refresh": "Real-time",
            "reviewed_by": "Infra Review",
            "kill_trigger": ">2× baseline for 1 week",
            "current_value": 2.34,
            "threshold": 4.68,
        },
        "retraining_cost_per_cycle": {
            "owner": "ML Engineer",
            "refresh": "Per event",
            "reviewed_by": "ML Review",
            "kill_trigger": ">1 month of value",
            "current_value": 1250.0,
            "threshold": 5000.0,
        },
        "value_per_inference": {
            "owner": "Business Analyst",
            "refresh": "Monthly",
            "reviewed_by": "Exec Review",
            "kill_trigger": "<0.8× projected for 2 months",
            "current_value": 0.15,
            "threshold": 0.12,  # 0.8× of projected
        },
    }
    
    @classmethod
    def get_contract_status(cls) -> dict:
        """Get current status of all telemetry metrics."""
        status = {
            "contract_id": "CT-1",
            "version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat(),
            "metrics": {},
            "overall_status": "healthy",
        }
        
        all_healthy = True
        for metric_name, config in cls.METRICS.items():
            is_healthy = config["current_value"] < config["threshold"]
            status["metrics"][metric_name] = {
                **config,
                "status": "healthy" if is_healthy else "warning",
                "headroom": (config["threshold"] - config["current_value"]) / config["threshold"],
            }
            if not is_healthy:
                all_healthy = False
        
        status["overall_status"] = "healthy" if all_healthy else "warning"
        return status
    
    @classmethod
    def check_kill_criteria(cls) -> dict:
        """Check if any kill criteria are met."""
        triggers = []
        
        for metric_name, config in cls.METRICS.items():
            if config["current_value"] >= config["threshold"]:
                triggers.append({
                    "metric": metric_name,
                    "current": config["current_value"],
                    "threshold": config["threshold"],
                    "owner": config["owner"],
                    "action_required": config["kill_trigger"],
                })
        
        return {
            "kill_triggered": len(triggers) > 0,
            "triggers": triggers,
            "checked_at": datetime.utcnow().isoformat(),
        }


class CostTracker:
    """Tracks costs for individual operations."""
    
    # Cost estimates per operation (in USD)
    OPERATION_COSTS = {
        "care_gap_detection": 0.0018,
        "readmission_prediction": 0.0031,
        "clinical_summarization": 0.034,
        "batch_prediction": 0.0025,
        "document_retrieval": 0.0005,
        "phi_detection": 0.0002,
    }
    
    # Value estimates per operation (in USD)
    OPERATION_VALUES = {
        "care_gap_detection": 0.12,
        "readmission_prediction": 0.45,
        "clinical_summarization": 2.50,
        "batch_prediction": 0.35,
        "document_retrieval": 0.05,
        "phi_detection": 0.10,
    }
    
    @classmethod
    def record_operation(
        cls,
        operation: str,
        model: str = "default",
        tokens_used: int = 0,
        human_review_required: bool = False,
    ):
        """Record cost and value for an operation."""
        cost = cls.OPERATION_COSTS.get(operation, 0.001)
        value = cls.OPERATION_VALUES.get(operation, 0.01)
        
        # Add token-based costs for LLM operations
        if tokens_used > 0:
            # Approximate cost: $0.01 per 1K tokens
            cost += (tokens_used / 1000) * 0.01
        
        # Record metrics
        INFERENCE_COST.labels(model=model, operation=operation).inc(cost)
        INFERENCE_VALUE.labels(model=model, operation=operation).inc(value)
        COST_PER_INFERENCE.labels(model=model, operation=operation).observe(cost)
        
        if human_review_required:
            review_cost = 0.50  # Estimated cost of human review
            HUMAN_REVIEW_COST.labels(operation=operation).inc(review_cost)
        
        # Update ROI gauge
        if cost > 0:
            CURRENT_ROI_RATIO.labels(model=model).set(value / cost)
        
        logger.debug(
            "operation_cost_recorded",
            operation=operation,
            cost=cost,
            value=value,
            tokens=tokens_used,
        )
        
        return {"cost": cost, "value": value, "roi": value / cost if cost > 0 else 0}


class CostTelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track cost telemetry for all API requests.
    
    Records:
    - Request count
    - Latency
    - Estimated cost per request
    - Error rates
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate latency
        latency = time.time() - start_time
        
        # Extract operation type from path
        path = request.url.path
        operation = self._path_to_operation(path)
        
        if operation:
            # Record cost telemetry
            CostTracker.record_operation(
                operation=operation,
                model="coco-platform",
            )
        
        # Add cost header for transparency
        response.headers["X-Cost-USD"] = f"{CostTracker.OPERATION_COSTS.get(operation, 0.001):.4f}"
        
        return response
    
    def _path_to_operation(self, path: str) -> Optional[str]:
        """Map request path to operation type."""
        if "/care-gaps" in path:
            return "care_gap_detection"
        elif "/readmission" in path:
            return "readmission_prediction"
        elif "/summarize" in path:
            return "clinical_summarization"
        elif "/batch" in path:
            return "batch_prediction"
        return None


class CostGuard:
    """
    Cost guard to prevent runaway spending.
    
    Per FDE Playbook: Governance checks fail fast before egress calls.
    """
    
    def __init__(
        self,
        max_cost_per_request: float = 0.25,
        daily_budget: float = 1000.0,
    ):
        self.max_cost_per_request = max_cost_per_request
        self.daily_budget = daily_budget
        self.daily_spend = 0.0
        self.last_reset = datetime.utcnow().date()
    
    def check_budget(self, estimated_cost: float) -> tuple[bool, str]:
        """
        Check if operation is within budget.
        
        Returns:
            (allowed, reason)
        """
        # Reset daily spend if new day
        today = datetime.utcnow().date()
        if today > self.last_reset:
            self.daily_spend = 0.0
            self.last_reset = today
        
        # Check per-request limit
        if estimated_cost > self.max_cost_per_request:
            return False, f"Estimated cost ${estimated_cost:.4f} exceeds per-request limit ${self.max_cost_per_request:.4f}"
        
        # Check daily budget
        if self.daily_spend + estimated_cost > self.daily_budget:
            return False, f"Daily budget ${self.daily_budget:.2f} would be exceeded"
        
        return True, "within_budget"
    
    def record_spend(self, cost: float):
        """Record actual spend."""
        self.daily_spend += cost
        logger.info(
            "cost_recorded",
            cost=cost,
            daily_spend=self.daily_spend,
            daily_budget=self.daily_budget,
            utilization=self.daily_spend / self.daily_budget,
        )
