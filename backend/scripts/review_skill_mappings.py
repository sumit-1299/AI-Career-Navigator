"""
Batch Mapping Review Tool for AI Career Navigator.

Lightweight CLI and utility for reviewing, approving, and rejecting
candidate skill mappings from skill_mapping_review.csv.

Supports:
- Tracking decisions: APPROVED, REVIEW, REJECTED, UNMATCHED.
- Listing pending candidates requiring human review.
- Approving candidates and registering new SkillAlias records in PostgreSQL.
- Rejecting false-positive candidate pairings with explicit rationale.
"""

import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

REVIEW_FILE_PROCESSED = PROJECT_ROOT / "data" / "processed" / "skill_mapping_review.csv"
REVIEW_FILE_MAPPINGS = PROJECT_ROOT / "data" / "mappings" / "skill_mapping_review.csv"


def load_review_records() -> List[Dict[str, str]]:
    """Loads all records from the review CSV file."""
    filepath = REVIEW_FILE_PROCESSED if REVIEW_FILE_PROCESSED.exists() else REVIEW_FILE_MAPPINGS
    if not filepath.exists():
        raise FileNotFoundError(f"Review file not found at {filepath}")

    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_review_records(records: List[Dict[str, str]]):
    """Saves records back to both processed and mappings directories."""
    fieldnames = [
        "source",
        "source_skill",
        "normalized_source_skill",
        "candidate_canonical_skill",
        "confidence",
        "decision",
        "reason"
    ]

    for path in [REVIEW_FILE_PROCESSED, REVIEW_FILE_MAPPINGS]:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)


def get_summary() -> Dict[str, Any]:
    """Computes summary statistics across all reviewed candidate records."""
    records = load_review_records()
    decision_counts = Counter(r.get("decision", "UNMATCHED") for r in records)
    confidence_counts = Counter(r.get("confidence", "LOW") for r in records)

    return {
        "total_records": len(records),
        "decisions": dict(decision_counts),
        "confidences": dict(confidence_counts)
    }


def list_review_candidates(
    decision: str = "REVIEW",
    limit: int = 15,
    search: Optional[str] = None,
    source: Optional[str] = None
) -> List[Dict[str, str]]:
    """Lists candidate records matching filter criteria."""
    records = load_review_records()
    filtered = []

    for r in records:
        if decision and r.get("decision") != decision:
            continue
        if source and r.get("source", "").upper() != source.upper():
            continue
        if search:
            q = search.lower()
            if q not in r.get("source_skill", "").lower() and q not in r.get("candidate_canonical_skill", "").lower():
                continue
        filtered.append(r)
        if len(filtered) >= limit:
            break

    return filtered


def approve_mapping(
    source_skill: str,
    canonical_skill_name: str,
    note: Optional[str] = None,
    persist_to_db: bool = True
) -> bool:
    """
    Approves a candidate mapping.
    Updates review CSV status to APPROVED and registers alias in database.
    """
    records = load_review_records()
    matched = False
    norm_target = source_skill.strip().lower()

    for r in records:
        if r.get("source_skill", "").strip().lower() == norm_target or r.get("normalized_source_skill", "").strip() == norm_target:
            r["decision"] = "APPROVED"
            r["candidate_canonical_skill"] = canonical_skill_name.strip()
            r["confidence"] = "HIGH"
            r["reason"] = note or f"Manually verified equivalent of '{canonical_skill_name.strip()}'"
            matched = True
            break

    if not matched:
        print(f"Error: Candidate '{source_skill}' not found in review pool.")
        return False

    save_review_records(records)
    print(f"Successfully approved '{source_skill}' -> '{canonical_skill_name}'.")

    # Optionally persist directly into PostgreSQL SkillAlias
    if persist_to_db:
        try:
            from app import create_app
            from extensions import db
            from models.canonical_skill import CanonicalSkill
            from models.skill_alias import SkillAlias
            from models.data_source import DataSource
            from utils.normalization import normalize_skill_name

            app = create_app()
            with app.app_context():
                canonical = CanonicalSkill.query.filter_by(
                    normalized_name=normalize_skill_name(canonical_skill_name)
                ).first()

                if not canonical:
                    print(f"Warning: Canonical skill '{canonical_skill_name}' does not exist in DB yet.")
                    return True

                norm_alias = normalize_skill_name(source_skill)
                existing_alias = SkillAlias.query.filter_by(
                    canonical_skill_id=canonical.id,
                    normalized_alias=norm_alias
                ).first()

                if not existing_alias:
                    alias = SkillAlias(
                        canonical_skill_id=canonical.id,
                        alias_name=source_skill.strip(),
                        normalized_alias=norm_alias
                    )
                    db.session.add(alias)
                    db.session.commit()
                    print(f"Registered new SkillAlias in PostgreSQL: '{source_skill}' (id: {alias.id}).")
        except Exception as e:
            print(f"Note: Could not write alias to database: {e}")

    return True


def reject_mapping(
    source_skill: str,
    reason: Optional[str] = None
) -> bool:
    """
    Rejects a candidate mapping.
    Updates review CSV status to REJECTED with explicit rationale.
    """
    records = load_review_records()
    matched = False
    norm_target = source_skill.strip().lower()

    for r in records:
        if r.get("source_skill", "").strip().lower() == norm_target or r.get("normalized_source_skill", "").strip() == norm_target:
            r["decision"] = "REJECTED"
            r["candidate_canonical_skill"] = ""
            r["confidence"] = "LOW"
            r["reason"] = reason or "Rejected during review: Disparate domain or distinct conceptual discipline."
            matched = True
            break

    if not matched:
        print(f"Error: Candidate '{source_skill}' not found in review pool.")
        return False

    save_review_records(records)
    print(f"Successfully rejected mapping for '{source_skill}'.")
    return True


def main():
    parser = argparse.ArgumentParser(description="AI Career Navigator — Batch Skill Review CLI")
    parser.add_argument("--status", action="store_true", help="Print summary counts of all decisions")
    parser.add_argument("--list", action="store_true", help="List pending candidate skills requiring review")
    parser.add_argument("--limit", type=int, default=15, help="Number of records to display")
    parser.add_argument("--search", type=str, help="Search query filter")
    parser.add_argument("--source", type=str, help="Source filter (e.g. O*NET, ESCO)")
    parser.add_argument("--decision", type=str, default="REVIEW", help="Filter by decision state (REVIEW, APPROVED, REJECTED, UNMATCHED)")
    parser.add_argument("--approve", type=str, help="Approve candidate skill name")
    parser.add_argument("--canonical", type=str, help="Target canonical skill for approval")
    parser.add_argument("--reject", type=str, help="Reject candidate skill name")
    parser.add_argument("--reason", type=str, help="Reason for rejection or approval note")

    args = parser.parse_args()

    if args.status or len(sys.argv) == 1:
        summary = get_summary()
        print("\n================= SKILL MAPPING REVIEW STATUS =================")
        print(f"Total Processed Candidates: {summary['total_records']}")
        print("\nBreakdown by Decision:")
        for dec, cnt in sorted(summary["decisions"].items()):
            print(f"  {dec:<15}: {cnt:>6}")
        print("\nBreakdown by Confidence:")
        for conf, cnt in sorted(summary["confidences"].items()):
            print(f"  {conf:<15}: {cnt:>6}")
        print("================================================================\n")
        return

    if args.approve:
        if not args.canonical:
            print("Error: --canonical <name> is required when using --approve.")
            sys.exit(1)
        approve_mapping(args.approve, args.canonical, args.reason)
        return

    if args.reject:
        reject_mapping(args.reject, args.reason)
        return

    if args.list:
        candidates = list_review_candidates(
            decision=args.decision,
            limit=args.limit,
            search=args.search,
            source=args.source
        )
        print(f"\nListing up to {args.limit} candidates with decision='{args.decision}':")
        print("-" * 90)
        print(f"{'Source':<8} | {'Source Skill':<35} | {'Candidate Canonical':<20} | {'Decision':<10}")
        print("-" * 90)
        for c in candidates:
            print(f"{c.get('source',''):<8} | {c.get('source_skill','')[:35]:<35} | {c.get('candidate_canonical_skill','')[:20]:<20} | {c.get('decision',''):<10}")
        print("-" * 90)


if __name__ == "__main__":
    main()
