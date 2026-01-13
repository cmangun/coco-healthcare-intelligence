#!/usr/bin/env bash
#
# Generate Evidence Pack for Compliance Review
#
# Creates a timestamped bundle containing:
# - Regulatory mappings
# - Threat model
# - Audit evidence index
# - Evaluation results
# - Demo run output
#
# Usage:
#   ./scripts/generate_evidence_pack.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PACK_DIR="$PROJECT_ROOT/evidence_pack_$TIMESTAMP"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║           CoCo Evidence Pack Generator                           ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Create pack directory
mkdir -p "$PACK_DIR"
echo "📁 Created: $PACK_DIR"

# Copy regulatory documents
echo "📋 Collecting regulatory documents..."
mkdir -p "$PACK_DIR/regulatory"
cp "$PROJECT_ROOT/regulatory/"*.md "$PACK_DIR/regulatory/"

# Copy security documents
echo "🔒 Collecting security documents..."
mkdir -p "$PACK_DIR/security"
cp "$PROJECT_ROOT/SECURITY.md" "$PACK_DIR/security/"
cp "$PROJECT_ROOT/THREAT_MODEL.md" "$PACK_DIR/security/"

# Copy evaluation
echo "📊 Collecting evaluation documentation..."
mkdir -p "$PACK_DIR/evaluation"
cp "$PROJECT_ROOT/docs/EVALUATION.md" "$PACK_DIR/evaluation/"

# Copy postmortems
echo "🔥 Collecting incident documentation..."
mkdir -p "$PACK_DIR/incidents"
cp "$PROJECT_ROOT/postmortems/"*.md "$PACK_DIR/incidents/"

# Copy runbook
echo "📖 Collecting operational documentation..."
mkdir -p "$PACK_DIR/operations"
cp "$PROJECT_ROOT/RUNBOOK.md" "$PACK_DIR/operations/"

# Generate system info
echo "💻 Generating system information..."
cat > "$PACK_DIR/system_info.txt" << EOF
CoCo Evidence Pack
Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Host: $(hostname)
Git Commit: $(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo "N/A")
Git Tag: $(cd "$PROJECT_ROOT" && git describe --tags 2>/dev/null || echo "N/A")
EOF

# Try to run health check and capture output
echo "🏥 Capturing health check..."
if curl -s http://localhost:8000/health > "$PACK_DIR/health_check.json" 2>/dev/null; then
    echo "   ✓ API health captured"
else
    echo '{"status": "not_running", "note": "API was not running during evidence collection"}' > "$PACK_DIR/health_check.json"
    echo "   ⚠ API not running (placeholder created)"
fi

# Try to capture governance status
echo "📋 Capturing governance status..."
if curl -s http://localhost:8000/api/v1/governance/status > "$PACK_DIR/governance_status.json" 2>/dev/null; then
    echo "   ✓ Governance status captured"
else
    echo '{"status": "not_captured", "note": "Run demo.sh first to capture live status"}' > "$PACK_DIR/governance_status.json"
    echo "   ⚠ Governance not captured (placeholder created)"
fi

# Try to capture audit verification
echo "🔍 Capturing audit verification..."
if curl -s http://localhost:8000/api/v1/audit/verify > "$PACK_DIR/audit_verification.json" 2>/dev/null; then
    echo "   ✓ Audit verification captured"
else
    echo '{"status": "not_captured", "note": "Run demo.sh first to capture live verification"}' > "$PACK_DIR/audit_verification.json"
    echo "   ⚠ Audit not captured (placeholder created)"
fi

# Create manifest
echo "📝 Creating manifest..."
cat > "$PACK_DIR/MANIFEST.md" << EOF
# CoCo Evidence Pack

**Generated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")  
**Version:** $(cd "$PROJECT_ROOT" && git describe --tags 2>/dev/null || echo "N/A")  
**Commit:** $(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo "N/A")

## Contents

### Regulatory Documents
- \`regulatory/hipaa-mapping.md\` - HIPAA Technical Safeguard Mapping
- \`regulatory/fda-ml-change-control.md\` - FDA ML/AI Change Control Framework
- \`regulatory/audit-evidence-index.md\` - Audit Evidence Index

### Security Documents
- \`security/SECURITY.md\` - Security Policy
- \`security/THREAT_MODEL.md\` - STRIDE Threat Analysis

### Evaluation
- \`evaluation/EVALUATION.md\` - Methodology, Metrics, Limitations

### Incident Documentation
- \`incidents/2024-llm-hallucination-event.md\` - LLM Hallucination Postmortem

### Operations
- \`operations/RUNBOOK.md\` - Operator Runbook

### Live Captures
- \`health_check.json\` - API Health Status
- \`governance_status.json\` - Governance Status
- \`audit_verification.json\` - Audit Chain Verification
- \`system_info.txt\` - System Information

## Usage

This evidence pack is suitable for:
- HIPAA Security Audits
- FDA Pre-Submission Meetings
- SOC 2 Type II Evidence Collection
- Enterprise Vendor Assessment
- Internal Compliance Review

## Contact

For questions about this evidence pack:
- Repository: https://github.com/cmangun/coco-healthcare-intelligence
- Author: Christopher Mangun
EOF

# Create zip archive
echo "📦 Creating archive..."
cd "$PROJECT_ROOT"
zip -r "evidence_pack_$TIMESTAMP.zip" "evidence_pack_$TIMESTAMP" > /dev/null

# Cleanup directory (keep zip)
rm -rf "$PACK_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    EVIDENCE PACK COMPLETE                         ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║                                                                   ║"
echo "║   📦 evidence_pack_$TIMESTAMP.zip                          ║"
echo "║                                                                   ║"
echo "║   Contents:                                                       ║"
echo "║   • HIPAA mapping + audit evidence index                         ║"
echo "║   • FDA change control framework                                  ║"
echo "║   • Threat model + security policy                               ║"
echo "║   • Evaluation methodology                                        ║"
echo "║   • Incident postmortem                                          ║"
echo "║   • Operator runbook                                             ║"
echo "║   • Live system captures (if API running)                        ║"
echo "║                                                                   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
