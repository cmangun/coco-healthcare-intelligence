# CoCo: Careware for Healthcare Intelligence
# Production-grade Dockerfile following healthcare security best practices

# Build stage
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels \
    fastapi uvicorn pydantic pydantic-settings httpx structlog \
    openai tiktoken numpy pandas scikit-learn \
    prometheus-client redis sqlalchemy asyncpg \
    opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp

# Production stage
FROM python:3.11-slim as production

# Security: Run as non-root user
RUN groupadd -r coco && useradd -r -g coco coco

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application code
COPY --chown=coco:coco coco/ /app/coco/
COPY --chown=coco:coco scripts/ /app/scripts/
COPY --chown=coco:coco data/ /app/data/

# Create directories for runtime
RUN mkdir -p /app/logs /app/tmp /tmp/prometheus \
    && chown -R coco:coco /app /tmp/prometheus

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus \
    ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER coco

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "coco.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Labels for container metadata
LABEL org.opencontainers.image.title="CoCo: Careware for Healthcare Intelligence" \
      org.opencontainers.image.description="End-to-end healthcare AI platform" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Christopher Mangun" \
      org.opencontainers.image.url="https://github.com/cmangun/coco-healthcare-intelligence" \
      org.opencontainers.image.source="https://github.com/cmangun/coco-healthcare-intelligence" \
      com.coco.hipaa-compliant="true" \
      com.coco.playbook-phase="10-production"
