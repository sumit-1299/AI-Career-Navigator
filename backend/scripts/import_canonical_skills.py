"""
Canonical Skill Mapping, Ingestion, and Benchmark Migration Pipeline.

Phase 2 Implementation:
1. Safe canonical skill population with exact matching.
2. Conservative ambiguity detection (AUTO_MATCH, REVIEW, UNMATCHED).
3. Persistent review mapping output (skill_mapping_review.csv).
4. Automated benchmark career skills migration (linking career_skills.canonical_skill_id).
"""

import csv
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Project root and backend path setup
BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app
from extensions import db
from models.canonical_skill import CanonicalSkill
from models.career_skill import CareerSkill
from models.data_source import DataSource
from models.skill import Skill
from models.skill_alias import SkillAlias
from utils.normalization import (
    is_ambiguous_match,
    normalize_skill_name,
    strip_parenthetical_qualifiers,
)

CANDIDATES_FILE = PROJECT_ROOT / "data" / "processed" / "skill_candidates.csv"
REVIEW_OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "skill_mapping_review.csv"
MAPPINGS_DIR = PROJECT_ROOT / "data" / "mappings"
MAPPINGS_REVIEW_FILE = MAPPINGS_DIR / "skill_mapping_review.csv"


def get_data_source_map() -> Dict[str, int]:
    """Retrieve dictionary mapping uppercase source name to database source_id."""
    sources = DataSource.query.all()
    return {s.source_name.upper(): s.id for s in sources}


def find_or_create_canonical_skill(
    canonical_name: str,
    skill_type: Optional[str] = None,
    description: Optional[str] = None
) -> Tuple[CanonicalSkill, bool]:
    """Find existing canonical skill by normalized_name or create new one."""
    normalized = normalize_skill_name(canonical_name)
    if not normalized:
        raise ValueError("Canonical skill name cannot be empty.")

    existing = CanonicalSkill.query.filter_by(normalized_name=normalized).first()
    if existing:
        return existing, False

    skill = CanonicalSkill(
        canonical_name=canonical_name.strip(),
        normalized_name=normalized,
        skill_type=skill_type,
        description=description
    )
    db.session.add(skill)
    db.session.flush()
    return skill, True


def add_alias_if_not_exists(
    canonical_skill: CanonicalSkill,
    alias_name: str,
    source_id: Optional[int] = None
) -> Tuple[Optional[SkillAlias], bool]:
    """Add alias to canonical skill if not already present."""
    normalized_alias = normalize_skill_name(alias_name)
    if not normalized_alias:
        return None, False

    existing = SkillAlias.query.filter_by(
        canonical_skill_id=canonical_skill.id,
        normalized_alias=normalized_alias
    ).first()

    if existing:
        return existing, False

    alias = SkillAlias(
        canonical_skill_id=canonical_skill.id,
        alias_name=alias_name.strip(),
        normalized_alias=normalized_alias,
        source_id=source_id
    )
    db.session.add(alias)
    db.session.flush()
    return alias, True


def populate_benchmark_canonical_skills(source_map: Dict[str, int]) -> Dict[str, CanonicalSkill]:
    """
    Establish high-confidence benchmark IT canonical skills required
    by the 10 core career tracks.
    """
    core_it_skills = [
        ("Python", "Programming Language", "High-level general-purpose programming language"),
        ("Java", "Programming Language", "Object-oriented class-based programming language"),
        ("SQL", "Database Query Language", "Domain-specific language used in programming and managing databases"),
        ("HTML", "Web Technology", "Standard markup language for documents designed to be displayed in a web browser"),
        ("CSS", "Web Technology", "Style sheet language used for describing the presentation of a document"),
        ("JavaScript", "Programming Language", "Programming language that is one of the core technologies of the World Wide Web"),
        ("React", "Frontend Framework", "Free and open-source front-end JavaScript library for building user interfaces"),
        ("Git", "Version Control", "Distributed version control system for tracking changes in source code"),
        ("Docker", "Containerization", "OS-level virtualization platform delivering software in packages called containers"),
        ("Kubernetes", "Container Orchestration", "Open-source system for automating deployment and management of containerized applications"),
        ("Linux", "Operating System", "Open-source Unix-like operating system based on the Linux kernel"),
        ("PostgreSQL", "Database", "Free and open-source relational database management system emphasizing extensibility"),
        ("MySQL", "Database", "Open-source relational database management system"),
        ("Machine Learning", "Artificial Intelligence", "Study of computer algorithms that improve automatically through experience"),
        ("Deep Learning", "Artificial Intelligence", "Subfield of machine learning based on artificial neural networks"),
        ("AWS", "Cloud Computing", "Comprehensive, evolving cloud computing platform provided by Amazon"),
        ("Networking", "Infrastructure", "Practice of transporting and exchanging data between nodes over a shared medium"),
        ("Cybersecurity", "Security", "Protection of computer systems and networks from threats and unauthorized access"),
        ("CI/CD", "DevOps", "Combined practice of continuous integration and continuous delivery/deployment"),
        ("Data Structures", "Computer Science", "Data organization, management, and storage format enabling efficient access"),
        ("Pandas", "Data Analytics Library", "Software library written for Python for data manipulation and analysis"),
        ("TensorFlow", "Machine Learning Framework", "Open-source software library for machine learning and artificial intelligence"),
        ("Excel", "Software Tool", "Spreadsheet software developed by Microsoft"),
        ("Statistics", "Mathematics", "Discipline concerning the collection, organization, and analysis of data"),
        ("Power BI", "Data Analytics Tool", "Interactive data visualization software product developed by Microsoft"),
        ("SIEM", "Cybersecurity", "Security information and event management software system"),
        ("CCNA", "Certification / Networking", "Cisco Certified Network Associate credential and skill knowledge"),
        ("Routing and Switching", "Networking", "Configuring network paths, routing protocols, and hardware switches"),
        ("Database Security", "Database Management", "Collective measures used to secure and protect database management systems"),
        ("Network Security", "Networking", "Provisions and policies adopted to prevent and monitor unauthorized access"),
    ]

    canonical_map = {}
    prototype_source_id = source_map.get("PROTOTYPE")

    for name, stype, desc in core_it_skills:
        skill, _ = find_or_create_canonical_skill(name, stype, desc)
        canonical_map[skill.normalized_name] = skill

        # Register self-alias under PROTOTYPE source
        add_alias_if_not_exists(skill, name, prototype_source_id)

    return canonical_map


def process_candidates_and_generate_review(
    canonical_map: Dict[str, CanonicalSkill],
    source_map: Dict[str, int]
) -> Tuple[int, int, int, List[Dict[str, str]]]:
    """
    Evaluates candidate terms against canonical skills:
    - Exact matches -> AUTO_MATCH (HIGH confidence)
    - Parenthetical equivalents -> AUTO_MATCH (MEDIUM confidence)
    - Ambiguous token overlaps -> REVIEW (LOW confidence)
    - Unmatched skills -> UNMATCHED (LOW confidence)
    """
    auto_match_count = 0
    review_count = 0
    unmatched_count = 0

    review_records: List[Dict[str, str]] = []

    if not CANDIDATES_FILE.exists():
        print(f"Warning: {CANDIDATES_FILE} does not exist.")
        return 0, 0, 0, []

    with open(CANDIDATES_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            original_name = row["original_name"].strip()
            normalized_name = row["normalized_name"].strip()
            source = row["source"].strip()
            source_id = source_map.get(source.upper())

            # 1. Exact normalized match (HIGH confidence)
            if normalized_name in canonical_map:
                target_skill = canonical_map[normalized_name]
                alias, created = add_alias_if_not_exists(target_skill, original_name, source_id)
                auto_match_count += 1

                review_records.append({
                    "source": source,
                    "source_skill": original_name,
                    "normalized_source_skill": normalized_name,
                    "candidate_canonical_skill": target_skill.canonical_name,
                    "confidence": "HIGH",
                    "decision": "AUTO_MATCH",
                    "reason": "Exact normalized string equality match"
                })
                continue

            # 2. Parenthetical qualifier stripped match (MEDIUM confidence)
            # E.g., 'Python (computer programming)' -> 'Python'
            stripped = strip_parenthetical_qualifiers(original_name)
            norm_stripped = normalize_skill_name(stripped)

            if norm_stripped in canonical_map:
                target_skill = canonical_map[norm_stripped]
                alias, created = add_alias_if_not_exists(target_skill, original_name, source_id)
                auto_match_count += 1

                review_records.append({
                    "source": source,
                    "source_skill": original_name,
                    "normalized_source_skill": normalized_name,
                    "candidate_canonical_skill": target_skill.canonical_name,
                    "confidence": "MEDIUM",
                    "decision": "AUTO_MATCH",
                    "reason": f"Taxonomic parenthetical equivalent of '{target_skill.canonical_name}'"
                })
                continue

            # 3. Ambiguity check: Partial token overlap / substring containment (LOW confidence)
            # E.g. 'Cloud Management' vs 'Cloud Computing'
            ambiguous_canonical = None
            for can_norm, can_skill in canonical_map.items():
                if is_ambiguous_match(normalized_name, can_norm):
                    ambiguous_canonical = can_skill
                    break

            if ambiguous_canonical:
                review_count += 1
                review_records.append({
                    "source": source,
                    "source_skill": original_name,
                    "normalized_source_skill": normalized_name,
                    "candidate_canonical_skill": ambiguous_canonical.canonical_name,
                    "confidence": "LOW",
                    "decision": "REVIEW",
                    "reason": f"Shares tokens with '{ambiguous_canonical.canonical_name}' but represents distinct concept - DO NOT AUTO MERGE"
                })
                continue

            # 4. Unmatched: Completely distinct skill concept
            unmatched_count += 1
            review_records.append({
                "source": source,
                "source_skill": original_name,
                "normalized_source_skill": normalized_name,
                "candidate_canonical_skill": "",
                "confidence": "LOW",
                "decision": "UNMATCHED",
                "reason": "Distinct specialized skill outside current benchmark set"
            })

    return auto_match_count, review_count, unmatched_count, review_records


def migrate_benchmark_career_skills(canonical_map: Dict[str, CanonicalSkill]) -> Tuple[int, int, int, int]:
    """
    Populate canonical_skill_id in career_skills table for benchmark IT careers.
    Returns (total_records, successfully_mapped, ambiguous, unmatched).
    """
    career_skills = CareerSkill.query.all()
    total = len(career_skills)
    mapped = 0
    ambiguous = 0
    unmatched = 0

    # Build alias-to-canonical lookup from DB
    alias_lookup = {}
    aliases = SkillAlias.query.all()
    for a in aliases:
        alias_lookup[a.normalized_alias] = a.canonical_skill_id

    for cs in career_skills:
        norm = normalize_skill_name(cs.skill_name)

        if norm in canonical_map:
            cs.canonical_skill_id = canonical_map[norm].id
            mapped += 1
        elif norm in alias_lookup:
            cs.canonical_skill_id = alias_lookup[norm]
            mapped += 1
        else:
            # Check if ambiguous
            is_amb = any(is_ambiguous_match(norm, can_norm) for can_norm in canonical_map.keys())
            if is_amb:
                ambiguous += 1
            else:
                unmatched += 1

    return total, mapped, ambiguous, unmatched


def migrate_student_skills(canonical_map: Dict[str, CanonicalSkill]) -> Tuple[int, int, int]:
    """
    Populate canonical_skill_id in student skills table where matches exist.
    Returns (total_records, successfully_mapped, unmatched).
    """
    student_skills = Skill.query.all()
    total = len(student_skills)
    mapped = 0
    unmatched = 0

    alias_lookup = {a.normalized_alias: a.canonical_skill_id for a in SkillAlias.query.all()}

    for s in student_skills:
        norm = normalize_skill_name(s.skill_name)
        if norm in canonical_map:
            s.canonical_skill_id = canonical_map[norm].id
            mapped += 1
        elif norm in alias_lookup:
            s.canonical_skill_id = alias_lookup[norm]
            mapped += 1
        else:
            unmatched += 1

    return total, mapped, unmatched


def run_phase_2_pipeline():
    app = create_app()

    with app.app_context():
        print("=================================================================")
        print("AI Career Navigator — Phase 2 Canonical Mapping & Migration")
        print("=================================================================")

        source_map = get_data_source_map()
        print(f"Registered Data Sources: {list(source_map.keys())}")

        # 1. Establish Benchmark Canonical Skills
        print("\nStep 2 & 3: Populating Canonical Skills and Exact Matching...")
        canonical_map = populate_benchmark_canonical_skills(source_map)
        print(f"Active Canonical Skills in Catalog: {len(canonical_map)}")

        # 2. Evaluate Candidate Pool
        print("\nStep 4 & 5: Evaluating Candidate Pool & Ambiguity Classification...")
        auto_count, rev_count, unmatch_count, review_records = process_candidates_and_generate_review(
            canonical_map, source_map
        )
        print(f"  AUTO_MATCH (High/Med Confidence): {auto_count}")
        print(f"  REVIEW (Ambiguous / Token Overlap): {rev_count}")
        print(f"  UNMATCHED (Distinct Catalog Skills): {unmatch_count}")
        print(f"  Total Processed Candidate Records: {len(review_records)}")

        # 3. Write Persistent Review CSVs
        MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
        review_fields = [
            "source",
            "source_skill",
            "normalized_source_skill",
            "candidate_canonical_skill",
            "confidence",
            "decision",
            "reason"
        ]

        for out_path in [REVIEW_OUTPUT_FILE, MAPPINGS_REVIEW_FILE]:
            with open(out_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=review_fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(review_records)
            print(f"Wrote mapping review artifact to: {out_path}")

        # 4. Migrate Benchmark Career Skills (Step 8)
        print("\nStep 8: Migrating Existing Benchmark Career Skills...")
        cs_total, cs_mapped, cs_amb, cs_unmatched = migrate_benchmark_career_skills(canonical_map)
        print(f"  Total Career-Skill Records: {cs_total}")
        print(f"  Successfully Mapped to CanonicalSkill: {cs_mapped}")
        print(f"  Ambiguous Records: {cs_amb}")
        print(f"  Unmatched Records: {cs_unmatched}")

        # 5. Migrate Existing Student Profile Skills
        st_total, st_mapped, st_unmatched = migrate_student_skills(canonical_map)
        print(f"\nStudent Profile Skills Migration:")
        print(f"  Total Student Skills: {st_total}")
        print(f"  Successfully Linked: {st_mapped}")
        print(f"  Unmatched / Null: {st_unmatched}")

        db.session.commit()
        print("\nDatabase transaction successfully committed!")


if __name__ == "__main__":
    run_phase_2_pipeline()
