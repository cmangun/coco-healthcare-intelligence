#!/usr/bin/env python3
"""
CoCo Repository Evaluation Runner

Evaluates the repository against the eval_schema.json criteria.
Can be run standalone or integrated into CI.

Usage:
    python eval/run_eval.py                    # Full evaluation
    python eval/run_eval.py --section security # Single section
    python eval/run_eval.py --json             # JSON output
    python eval/run_eval.py --ci               # CI mode (exit 1 if < threshold)
"""

import json
import os
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CheckResult:
    """Result of a single check criterion."""
    name: str
    passed: bool
    points: int
    max_points: int
    evidence: Optional[str] = None


@dataclass
class SectionResult:
    """Result of a section evaluation."""
    id: str
    name: str
    score: int
    max_points: int
    checks: list = field(default_factory=list)
    is_bonus: bool = False


@dataclass
class EvalReport:
    """Complete evaluation report."""
    total_score: int
    max_score: int
    bonus_score: int
    rating: str
    sections: list = field(default_factory=list)
    passed: bool = True


def load_schema(schema_path: Path) -> dict:
    """Load the evaluation schema."""
    with open(schema_path) as f:
        return json.load(f)


def check_file_exists(repo_root: Path, file_path: str) -> bool:
    """Check if a file exists."""
    return (repo_root / file_path).exists()


def check_directory(repo_root: Path, dir_path: str, pattern: str, min_count: int) -> bool:
    """Check if directory exists with required files."""
    dir_full = repo_root / dir_path
    if not dir_full.exists():
        return False
    
    # Convert glob pattern to work with Path
    if pattern.startswith("*"):
        files = list(dir_full.glob(pattern))
    else:
        files = list(dir_full.glob(f"*{pattern}"))
    
    return len(files) >= min_count


def search_file_content(repo_root: Path, file_path: str, search_terms: list, min_occurrences: int = 1) -> tuple[bool, str]:
    """Search file content for terms. Returns (passed, evidence)."""
    full_path = repo_root / file_path
    if not full_path.exists():
        return False, "File not found"
    
    try:
        content = full_path.read_text()
    except Exception as e:
        return False, f"Error reading file: {e}"
    
    found_terms = []
    total_occurrences = 0
    
    for term in search_terms:
        # Support regex patterns
        if any(c in term for c in ['*', '.', '|', '[']):
            matches = re.findall(term, content, re.IGNORECASE)
        else:
            matches = re.findall(re.escape(term), content, re.IGNORECASE)
        
        if matches:
            found_terms.append(term)
            total_occurrences += len(matches)
    
    if min_occurrences > 1:
        passed = total_occurrences >= min_occurrences
        evidence = f"Found {total_occurrences} occurrences (need {min_occurrences})"
    else:
        passed = len(found_terms) > 0
        evidence = f"Found: {', '.join(found_terms[:3])}" if found_terms else "No terms found"
    
    return passed, evidence


def evaluate_check(repo_root: Path, check: dict) -> list[CheckResult]:
    """Evaluate a single check and return results for all criteria."""
    results = []
    check_type = check.get("type", "content")
    
    if check_type == "existence":
        for item in check.get("items", []):
            exists = check_file_exists(repo_root, item["path"])
            results.append(CheckResult(
                name=item["path"],
                passed=exists,
                points=item["points"] if exists else 0,
                max_points=item["points"],
                evidence="✅ Exists" if exists else "❌ Missing"
            ))
    
    elif check_type == "directory":
        for item in check.get("items", []):
            passed = check_directory(
                repo_root,
                item["path"],
                item["required_pattern"],
                item["min_count"]
            )
            results.append(CheckResult(
                name=f"{item['path']} ({item['required_pattern']})",
                passed=passed,
                points=item["points"] if passed else 0,
                max_points=item["points"],
                evidence="✅ Has required files" if passed else "❌ Missing or insufficient files"
            ))
    
    elif check_type == "content":
        file_path = check.get("file", "")
        
        for criterion in check.get("criteria", []):
            if criterion["name"] == "file_exists":
                exists = check_file_exists(repo_root, file_path)
                results.append(CheckResult(
                    name="file_exists",
                    passed=exists,
                    points=criterion["points"] if exists else 0,
                    max_points=criterion["points"],
                    evidence="✅ Exists" if exists else "❌ Missing"
                ))
            else:
                min_occ = criterion.get("min_occurrences", 1)
                passed, evidence = search_file_content(
                    repo_root,
                    file_path,
                    criterion.get("search_terms", []),
                    min_occ
                )
                results.append(CheckResult(
                    name=criterion["name"],
                    passed=passed,
                    points=criterion["points"] if passed else 0,
                    max_points=criterion["points"],
                    evidence=evidence
                ))
    
    return results


def evaluate_section(repo_root: Path, section: dict) -> SectionResult:
    """Evaluate a complete section."""
    total_score = 0
    total_max = 0
    check_results = []
    
    for check in section.get("checks", []):
        results = evaluate_check(repo_root, check)
        check_results.append({
            "id": check["id"],
            "name": check["name"],
            "results": results,
            "score": sum(r.points for r in results),
            "max": sum(r.max_points for r in results)
        })
        total_score += sum(r.points for r in results)
        total_max += sum(r.max_points for r in results)
    
    return SectionResult(
        id=section["id"],
        name=section["name"],
        score=total_score,
        max_points=total_max,
        checks=check_results,
        is_bonus=section.get("is_bonus", False)
    )


def get_rating(score: int, thresholds: dict) -> str:
    """Get rating based on score and thresholds."""
    for rating, config in thresholds.items():
        if config["min"] <= score <= config["max"]:
            return f"{rating.upper()} - {config['description']}"
    return "UNKNOWN"


def run_evaluation(repo_root: Path, schema_path: Path, section_filter: Optional[str] = None) -> EvalReport:
    """Run the complete evaluation."""
    schema = load_schema(schema_path)
    
    sections = []
    base_score = 0
    base_max = 0
    bonus_score = 0
    
    for section in schema["sections"]:
        if section_filter and section["id"] != section_filter:
            continue
        
        result = evaluate_section(repo_root, section)
        sections.append(result)
        
        if result.is_bonus:
            bonus_score += result.score
        else:
            base_score += result.score
            base_max += result.max_points
    
    total_score = base_score + bonus_score
    rating = get_rating(base_score, schema["thresholds"])
    
    return EvalReport(
        total_score=total_score,
        max_score=base_max + 5,  # +5 for bonus
        bonus_score=bonus_score,
        rating=rating,
        sections=sections,
        passed=base_score >= 85  # Strong threshold
    )


def format_report_text(report: EvalReport) -> str:
    """Format report as readable text."""
    lines = []
    lines.append("=" * 70)
    lines.append("COCO REPOSITORY EVALUATION REPORT")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Total Score: {report.total_score}/{report.max_score}")
    if report.bonus_score > 0:
        lines.append(f"  (Base: {report.total_score - report.bonus_score}/100 + Bonus: {report.bonus_score}/5)")
    lines.append(f"Rating: {report.rating}")
    lines.append(f"Status: {'✅ PASSED' if report.passed else '❌ NEEDS IMPROVEMENT'}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("SECTION SCORES")
    lines.append("-" * 70)
    
    for section in report.sections:
        bonus_marker = " (BONUS)" if section.is_bonus else ""
        lines.append(f"\n{section.name}{bonus_marker}: {section.score}/{section.max_points}")
        
        for check in section.checks:
            lines.append(f"  └─ {check['name']}: {check['score']}/{check['max']}")
            for result in check['results']:
                status = "✅" if result.passed else "❌"
                lines.append(f"       {status} {result.name}: {result.evidence}")
    
    lines.append("")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def format_report_json(report: EvalReport) -> str:
    """Format report as JSON."""
    data = {
        "total_score": report.total_score,
        "max_score": report.max_score,
        "bonus_score": report.bonus_score,
        "rating": report.rating,
        "passed": report.passed,
        "sections": []
    }
    
    for section in report.sections:
        section_data = {
            "id": section.id,
            "name": section.name,
            "score": section.score,
            "max_points": section.max_points,
            "is_bonus": section.is_bonus,
            "checks": []
        }
        
        for check in section.checks:
            check_data = {
                "id": check["id"],
                "name": check["name"],
                "score": check["score"],
                "max": check["max"],
                "criteria": [
                    {
                        "name": r.name,
                        "passed": r.passed,
                        "points": r.points,
                        "evidence": r.evidence
                    }
                    for r in check["results"]
                ]
            }
            section_data["checks"].append(check_data)
        
        data["sections"].append(section_data)
    
    return json.dumps(data, indent=2)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="CoCo Repository Evaluation")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--schema", default=None, help="Schema file path")
    parser.add_argument("--section", default=None, help="Evaluate single section")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--ci", action="store_true", help="CI mode (exit 1 if failed)")
    
    args = parser.parse_args()
    
    repo_root = Path(args.repo).resolve()
    
    # Find schema
    if args.schema:
        schema_path = Path(args.schema)
    else:
        schema_path = repo_root / "eval" / "eval_schema.json"
        if not schema_path.exists():
            schema_path = Path(__file__).parent / "eval_schema.json"
    
    if not schema_path.exists():
        print(f"Error: Schema not found at {schema_path}", file=sys.stderr)
        sys.exit(1)
    
    # Run evaluation
    report = run_evaluation(repo_root, schema_path, args.section)
    
    # Output
    if args.json:
        print(format_report_json(report))
    else:
        print(format_report_text(report))
    
    # CI mode exit code
    if args.ci and not report.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
