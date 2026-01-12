#!/usr/bin/env python3
"""
CoCo Interactive Demo

Demonstrates all three clinical use cases with real API calls.
Run after starting the platform with `docker compose up`.

Usage:
    python scripts/run_demo.py
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Optional

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


BASE_URL = "http://localhost:8000"

# ANSI colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print styled header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_section(text: str):
    """Print section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}▶ {text}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.ENDC}")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_json(data: dict, indent: int = 2):
    """Print formatted JSON."""
    print(json.dumps(data, indent=indent, default=str))


async def check_health(client: httpx.AsyncClient) -> bool:
    """Check if CoCo API is healthy."""
    try:
        response = await client.get(f"{BASE_URL}/health")
        return response.status_code == 200
    except Exception:
        return False


async def demo_platform_info(client: httpx.AsyncClient):
    """Demo: Platform information."""
    print_section("Platform Information")
    
    response = await client.get(f"{BASE_URL}/")
    data = response.json()
    
    print_info(f"Name: {data['name']}")
    print_info(f"Version: {data['version']}")
    print_info(f"Playbook Phase: {data['playbook_phase']}")
    print()
    
    print_info("Clinical Use Cases:")
    for uc in data['clinical_use_cases']:
        print(f"  • {uc['name']}: {uc['endpoint']}")
    print()
    
    print_info("Governance Features:")
    for key, value in data['governance'].items():
        status = "✓" if value else "✗"
        print(f"  {status} {key.replace('_', ' ').title()}")


async def demo_care_gaps(client: httpx.AsyncClient, patient_id: str = "P001"):
    """Demo: Care Gap Detection."""
    print_section(f"Care Gap Detection for Patient {patient_id}")
    
    # Get care gaps
    response = await client.get(f"{BASE_URL}/api/v1/care-gaps/patient/{patient_id}")
    data = response.json()
    
    print_success(f"Analysis completed at {data['analysis_timestamp']}")
    print_info(f"Total gaps identified: {data['total_gaps']}")
    print_info(f"Risk score: {data['risk_score']:.2f}")
    print()
    
    if data['care_gaps']:
        print_info("Care Gaps Found:")
        for gap in data['care_gaps'][:5]:  # Show first 5
            priority_color = Colors.RED if gap['priority'] in ['critical', 'high'] else Colors.YELLOW
            print(f"  {priority_color}[{gap['priority'].upper()}]{Colors.ENDC} {gap['name']}")
            print(f"    Due: {gap['due_date']} | Source: {gap['guideline_source']}")
    print()
    
    if data['recommendations']:
        print_info("Recommendations:")
        for rec in data['recommendations']:
            print(f"  → {rec}")
    
    return data


async def demo_readmission_risk(client: httpx.AsyncClient, patient_id: str = "P001"):
    """Demo: Readmission Risk Prediction."""
    print_section(f"Readmission Risk Prediction for Patient {patient_id}")
    
    response = await client.get(f"{BASE_URL}/api/v1/readmission/predict/{patient_id}")
    data = response.json()
    
    # Color code risk tier
    tier_colors = {
        'low': Colors.GREEN,
        'medium': Colors.YELLOW,
        'high': Colors.RED,
        'critical': Colors.RED + Colors.BOLD,
    }
    tier_color = tier_colors.get(data['risk_tier'], Colors.ENDC)
    
    print_success(f"Prediction completed")
    print_info(f"Risk Score: {data['risk_score']:.2%}")
    print(f"  Risk Tier: {tier_color}{data['risk_tier'].upper()}{Colors.ENDC}")
    print(f"  Confidence Interval: [{data['confidence_interval'][0]:.2%}, {data['confidence_interval'][1]:.2%}]")
    print()
    
    if data['contributing_factors']:
        print_info("Top Contributing Factors:")
        for factor in data['contributing_factors'][:5]:
            print(f"  • {factor['factor_name']}: {factor['value']} (weight: {factor['weight']:.2f})")
            if factor['is_modifiable']:
                print(f"    {Colors.GREEN}↳ Modifiable{Colors.ENDC}")
    print()
    
    if data['recommended_interventions']:
        print_info("Recommended Interventions:")
        for intervention in data['recommended_interventions'][:3]:
            print(f"  [{intervention['evidence_level']}] {intervention['name']}")
            print(f"    Risk reduction: {intervention['estimated_risk_reduction']:.0%}")
    print()
    
    # Model governance info
    gov = data['model_governance']
    print_info("Model Governance:")
    print(f"  Model: {gov['model_id']} v{gov['model_version']}")
    print(f"  Validation AUC: {gov['validation_auc']}")
    print(f"  Drift Status: {gov['drift_status']}")
    
    return data


async def demo_clinical_summary(client: httpx.AsyncClient, patient_id: str = "P001"):
    """Demo: Clinical Summarization."""
    print_section(f"Clinical Summary for Patient {patient_id}")
    
    response = await client.get(
        f"{BASE_URL}/api/v1/summarize/patient/{patient_id}",
        params={"summary_type": "comprehensive", "time_range": "last_6_months"}
    )
    data = response.json()
    
    print_success(f"Summary generated at {data['generated_at']}")
    print()
    
    # PHI audit
    phi = data['phi_audit']
    if phi['phi_detected']:
        print_warning(f"PHI detected and redacted: {phi['phi_types_found']}")
    else:
        print_success("PHI scan: No PHI detected in output")
    print()
    
    # Summary
    print_info("Clinical Summary:")
    print(f"{Colors.CYAN}{'─'*50}{Colors.ENDC}")
    print(data['summary'][:800] + "..." if len(data['summary']) > 800 else data['summary'])
    print(f"{Colors.CYAN}{'─'*50}{Colors.ENDC}")
    print()
    
    # Key findings
    if data['key_findings']:
        print_info("Key Findings:")
        for finding in data['key_findings'][:4]:
            trend_icon = "↑" if finding.get('trend') == 'improving' else "↓" if finding.get('trend') == 'worsening' else "→"
            print(f"  {trend_icon} {finding['finding']}")
    print()
    
    # Active problems
    if data['active_problems']:
        print_info("Active Problems:")
        for problem in data['active_problems']:
            print(f"  • {problem}")
    print()
    
    # Citations
    if data['citations']:
        print_info(f"Citations ({len(data['citations'])} sources):")
        for cite in data['citations'][:3]:
            print(f"  [{cite['source_type']}] {cite['source_date'][:10]} - Relevance: {cite['relevance_score']:.0%}")
    print()
    
    # RAG metrics
    rag = data['rag_metrics']
    print_info("RAG Performance:")
    print(f"  Documents retrieved: {rag['documents_retrieved']}")
    print(f"  Average relevance: {rag['average_relevance']:.0%}")
    print(f"  Latency: {rag['latency_ms']:.0f}ms")
    
    return data


async def demo_governance(client: httpx.AsyncClient):
    """Demo: Governance and Phase Status."""
    print_section("Governance & Phase Status")
    
    # Phase status
    response = await client.get(f"{BASE_URL}/governance/phase-status")
    data = response.json()
    
    print_info(f"Current Phase: {data['current_phase']}")
    print()
    
    print_info("Phase Gate Status:")
    for gate in data['phase_gates'][:6]:  # Show first 6
        status_icon = "✓" if gate['status'] == 'approved' else "◐" if gate['status'] == 'in_progress' else "○"
        print(f"  {status_icon} Phase {gate['phase_number']}: {gate['phase_name']} ({gate['status']})")
    print("  ...")
    print()
    
    # Cost telemetry
    response = await client.get(f"{BASE_URL}/governance/cost-telemetry")
    cost_data = response.json()
    
    print_info("Cost Telemetry (CT-1 Contract):")
    metrics = cost_data['metrics']
    print(f"  Cost per inference: ${metrics['cost_per_inference_usd']:.4f}")
    print(f"  Value per inference: ${metrics['value_per_inference_usd']:.2f}")
    print(f"  ROI Ratio: {metrics['roi_ratio']:.1f}x")
    print(f"  Daily inferences: {metrics['daily_inference_count']:,}")
    print(f"  Monthly cost: ${metrics['monthly_cost_usd']:.2f}")
    print()
    
    print_info("Compliance Status:")
    for key, value in data['compliance_status'].items():
        status = "✓" if value in ['compliant', 'active', 'enabled'] else "○"
        print(f"  {status} {key.replace('_', ' ').title()}: {value}")


async def run_full_demo():
    """Run the complete demo."""
    print_header("CoCo: Careware for Healthcare Intelligence")
    print_info("End-to-end Healthcare AI Platform Demo")
    print_info("Following the 12-Phase FDE Production Playbook")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check health
        print_info("Checking platform health...")
        if not await check_health(client):
            print_error("CoCo API is not available!")
            print_info("Start the platform with: docker compose up -d")
            return
        print_success("Platform is healthy!")
        
        # Run demos
        await demo_platform_info(client)
        input(f"\n{Colors.BOLD}Press Enter to continue to Care Gap Detection...{Colors.ENDC}")
        
        await demo_care_gaps(client, "P001")
        input(f"\n{Colors.BOLD}Press Enter to continue to Readmission Risk...{Colors.ENDC}")
        
        await demo_readmission_risk(client, "P001")
        input(f"\n{Colors.BOLD}Press Enter to continue to Clinical Summary...{Colors.ENDC}")
        
        await demo_clinical_summary(client, "P001")
        input(f"\n{Colors.BOLD}Press Enter to view Governance Status...{Colors.ENDC}")
        
        await demo_governance(client)
        
        print_header("Demo Complete")
        print_success("All three clinical use cases demonstrated successfully!")
        print()
        print_info("Next steps:")
        print("  • Explore the API docs at http://localhost:8000/docs")
        print("  • View metrics at http://localhost:9090 (Prometheus)")
        print("  • Check dashboards at http://localhost:3000 (Grafana)")
        print("  • Review model registry at http://localhost:5000 (MLflow)")
        print()
        print_info("Learn more:")
        print("  • FDE Playbook: https://enterprise-ai-playbook-demo.vercel.app/")
        print("  • Portfolio: https://healthcare-ai-consultant.com")


def main():
    """Main entry point."""
    try:
        asyncio.run(run_full_demo())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print_error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    main()
