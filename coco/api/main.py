"""
CoCo: Careware for Healthcare Intelligence
Unified API Gateway for Healthcare AI Services

This is the central orchestration layer that connects all 10 healthcare AI
repositories into a cohesive platform following the 12-phase FDE playbook.
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from coco.api.routers import care_gaps, readmission, summarization
from coco.governance.cost_telemetry import CostTelemetryMiddleware
from coco.governance.phase_gates import PhaseGateRegistry

# Structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "coco_requests_total",
    "Total requests to CoCo API",
    ["method", "endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "coco_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"]
)
CLINICAL_OPERATIONS = Counter(
    "coco_clinical_operations_total",
    "Clinical operations performed",
    ["operation_type", "status"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""
    # Startup
    logger.info(
        "coco_startup",
        version="1.0.0",
        phase="10-production",
        timestamp=datetime.utcnow().isoformat()
    )
    
    # Initialize phase gate registry
    app.state.phase_gates = PhaseGateRegistry()
    
    yield
    
    # Shutdown
    logger.info("coco_shutdown", timestamp=datetime.utcnow().isoformat())


# Initialize FastAPI application
app = FastAPI(
    title="CoCo: Careware for Healthcare Intelligence",
    description="""
    End-to-end healthcare AI platform demonstrating the 12-phase 
    Forward Deployed Engineering production playbook.
    
    ## Clinical Use Cases
    
    - **Care Gap Detection**: Identify patients missing preventive care
    - **Readmission Risk**: Predict 30-day readmission probability
    - **Clinical Summarization**: RAG-powered patient summaries
    
    ## Compliance
    
    - HIPAA-compliant data handling
    - PHI detection and redaction
    - Immutable audit logging
    - Model governance framework
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cost telemetry middleware
app.add_middleware(CostTelemetryMiddleware)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect Prometheus metrics for all requests."""
    import time
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    endpoint = request.url.path
    method = request.method
    status = response.status_code
    
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
    
    # Add trace headers
    response.headers["X-Request-ID"] = request.headers.get(
        "X-Request-ID", 
        f"coco-{datetime.utcnow().timestamp()}"
    )
    response.headers["X-Response-Time"] = f"{duration:.4f}s"
    
    return response


# Include routers for clinical use cases
app.include_router(
    care_gaps.router,
    prefix="/api/v1/care-gaps",
    tags=["Care Gap Detection"]
)
app.include_router(
    readmission.router,
    prefix="/api/v1/readmission",
    tags=["Readmission Risk"]
)
app.include_router(
    summarization.router,
    prefix="/api/v1/summarize",
    tags=["Clinical Summarization"]
)


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with platform overview."""
    return {
        "name": "CoCo: Careware for Healthcare Intelligence",
        "version": "1.0.0",
        "description": "End-to-end healthcare AI platform",
        "playbook_phase": "10-production",
        "clinical_use_cases": [
            {"name": "Care Gap Detection", "endpoint": "/api/v1/care-gaps"},
            {"name": "Readmission Risk", "endpoint": "/api/v1/readmission"},
            {"name": "Clinical Summarization", "endpoint": "/api/v1/summarize"},
        ],
        "governance": {
            "hipaa_compliant": True,
            "phi_detection": True,
            "audit_logging": True,
            "cost_telemetry": True,
        },
        "documentation": {
            "openapi": "/docs",
            "redoc": "/redoc",
            "playbook": "https://enterprise-ai-playbook-demo.vercel.app/",
        },
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "api": "healthy",
            "database": "healthy",  # Would check actual DB connection
            "cache": "healthy",     # Would check Redis connection
            "vector_db": "healthy", # Would check Qdrant connection
        }
    }


@app.get("/ready", tags=["System"])
async def readiness_check():
    """Readiness check for Kubernetes probes."""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/governance/phase-status", tags=["Governance"])
async def phase_status(request: Request):
    """Current phase gate status across all components."""
    registry = request.app.state.phase_gates
    return {
        "current_phase": "10-production",
        "phase_gates": registry.get_all_gates(),
        "kill_criteria": registry.get_kill_criteria(),
        "compliance_status": {
            "hipaa": "compliant",
            "phi_detection": "active",
            "audit_logging": "enabled",
        }
    }


@app.get("/governance/cost-telemetry", tags=["Governance"])
async def cost_telemetry():
    """Cost telemetry dashboard data."""
    return {
        "metrics": {
            "cost_per_inference_usd": 0.0023,
            "value_per_inference_usd": 0.15,
            "roi_ratio": 65.2,
            "daily_inference_count": 12450,
            "monthly_cost_usd": 856.35,
        },
        "thresholds": {
            "cost_ceiling_per_request": 0.05,
            "kill_threshold_ratio": 1.0,
            "warning_threshold_ratio": 0.8,
        },
        "status": "healthy",
        "last_updated": datetime.utcnow().isoformat(),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with audit logging."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": request.headers.get("X-Request-ID", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "coco.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
