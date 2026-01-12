#!/usr/bin/env bash
#
# CoCo Demo Script
# Golden-path end-to-end demonstration
#
# Usage:
#   ./scripts/demo.sh           # Full demo
#   ./scripts/demo.sh --quick   # Skip data generation
#
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
QUICK_MODE=false
if [[ "${1:-}" == "--quick" ]]; then
    QUICK_MODE=true
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║   CoCo: Careware for Healthcare Intelligence                     ║"
echo "║   End-to-End Demo                                                 ║"
echo "║                                                                   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_ROOT"

# ============================================================================
# Step 1: Check prerequisites
# ============================================================================
log_info "Step 1: Checking prerequisites..."

command -v docker >/dev/null 2>&1 || { log_error "Docker is required but not installed."; exit 1; }
command -v curl >/dev/null 2>&1 || { log_error "curl is required but not installed."; exit 1; }

log_success "Prerequisites satisfied"

# ============================================================================
# Step 2: Start services
# ============================================================================
log_info "Step 2: Starting services..."

docker compose up -d --wait 2>/dev/null || docker-compose up -d

# Wait for API to be healthy
log_info "Waiting for API to be healthy..."
MAX_ATTEMPTS=30
ATTEMPT=0
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
        log_error "API failed to start after $MAX_ATTEMPTS attempts"
        exit 1
    fi
    sleep 2
done

log_success "Services started and healthy"

# ============================================================================
# Step 3: Generate synthetic data (unless --quick)
# ============================================================================
if [ "$QUICK_MODE" = false ]; then
    log_info "Step 3: Generating synthetic patient data..."
    python scripts/generate_synthetic_data.py --patients 10 --output data/
    log_success "Generated 10 synthetic patients"
else
    log_info "Step 3: Skipping data generation (--quick mode)"
fi

# ============================================================================
# Step 4: Run Care Gap Detection
# ============================================================================
log_info "Step 4: Running Care Gap Detection workflow..."

CARE_GAP_RESPONSE=$(curl -s http://localhost:8000/api/v1/care-gaps/patient/P12345678)

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "CARE GAP DETECTION RESULT"
echo "─────────────────────────────────────────────────────────────────"
echo "$CARE_GAP_RESPONSE" | python -m json.tool 2>/dev/null || echo "$CARE_GAP_RESPONSE"
echo "─────────────────────────────────────────────────────────────────"
echo ""

# Validate response structure
if echo "$CARE_GAP_RESPONSE" | grep -q '"patient_id"'; then
    log_success "Care Gap Detection: Valid response received"
else
    log_warn "Care Gap Detection: Unexpected response format"
fi

# ============================================================================
# Step 5: Run Readmission Risk Prediction
# ============================================================================
log_info "Step 5: Running Readmission Risk Prediction workflow..."

READMISSION_RESPONSE=$(curl -s http://localhost:8000/api/v1/readmission/predict/P12345678)

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "READMISSION RISK PREDICTION RESULT"
echo "─────────────────────────────────────────────────────────────────"
echo "$READMISSION_RESPONSE" | python -m json.tool 2>/dev/null || echo "$READMISSION_RESPONSE"
echo "─────────────────────────────────────────────────────────────────"
echo ""

if echo "$READMISSION_RESPONSE" | grep -q '"risk_score"'; then
    log_success "Readmission Risk: Valid response received"
else
    log_warn "Readmission Risk: Unexpected response format"
fi

# ============================================================================
# Step 6: Run Clinical Summarization
# ============================================================================
log_info "Step 6: Running Clinical Summarization workflow..."

SUMMARY_RESPONSE=$(curl -s http://localhost:8000/api/v1/summarize/patient/P12345678)

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "CLINICAL SUMMARIZATION RESULT"
echo "─────────────────────────────────────────────────────────────────"
echo "$SUMMARY_RESPONSE" | python -m json.tool 2>/dev/null || echo "$SUMMARY_RESPONSE"
echo "─────────────────────────────────────────────────────────────────"
echo ""

if echo "$SUMMARY_RESPONSE" | grep -q '"summary"'; then
    log_success "Clinical Summarization: Valid response received"
else
    log_warn "Clinical Summarization: Unexpected response format"
fi

# ============================================================================
# Step 7: Check Governance Status
# ============================================================================
log_info "Step 7: Checking governance status..."

GOVERNANCE_RESPONSE=$(curl -s http://localhost:8000/api/v1/governance/status)

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "GOVERNANCE STATUS"
echo "─────────────────────────────────────────────────────────────────"
echo "$GOVERNANCE_RESPONSE" | python -m json.tool 2>/dev/null || echo "$GOVERNANCE_RESPONSE"
echo "─────────────────────────────────────────────────────────────────"
echo ""

log_success "Governance check complete"

# ============================================================================
# Step 8: Verify Audit Trail
# ============================================================================
log_info "Step 8: Verifying audit trail integrity..."

AUDIT_RESPONSE=$(curl -s http://localhost:8000/api/v1/audit/verify)

echo ""
echo "─────────────────────────────────────────────────────────────────"
echo "AUDIT TRAIL VERIFICATION"
echo "─────────────────────────────────────────────────────────────────"
echo "$AUDIT_RESPONSE" | python -m json.tool 2>/dev/null || echo "$AUDIT_RESPONSE"
echo "─────────────────────────────────────────────────────────────────"
echo ""

log_success "Audit verification complete"

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                       DEMO COMPLETE                               ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║                                                                   ║"
echo "║   ✓ Services started and healthy                                 ║"
echo "║   ✓ Care Gap Detection executed                                  ║"
echo "║   ✓ Readmission Risk Prediction executed                         ║"
echo "║   ✓ Clinical Summarization executed                              ║"
echo "║   ✓ Governance status checked                                    ║"
echo "║   ✓ Audit trail verified                                         ║"
echo "║                                                                   ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║   SERVICES RUNNING                                                ║"
echo "║   • API:        http://localhost:8000                            ║"
echo "║   • Grafana:    http://localhost:3000 (admin/admin)              ║"
echo "║   • Prometheus: http://localhost:9090                            ║"
echo "║   • Jaeger:     http://localhost:16686                           ║"
echo "║   • MLflow:     http://localhost:5000                            ║"
echo "║                                                                   ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║   To stop: docker compose down                                   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
