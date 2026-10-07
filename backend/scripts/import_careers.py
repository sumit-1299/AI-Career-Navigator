import csv
import os
import sys
from pathlib import Path

# Add backend directory to Python path
BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app import create_app
from extensions import db
from models.career import Career
from models.career_skill import CareerSkill


def resolve_data_file(filename: str) -> Path:
    """
    Resolve the career seed files.

    The current main branch stores the benchmark seed data under
    data/prototype/, while older versions of the importer expected the
    files directly under data/. Prefer the legacy path when present,
    otherwise use the canonical prototype seed location.
    """
    candidates = [
        PROJECT_ROOT / "data" / filename,
        PROJECT_ROOT / "data" / "prototype" / filename,
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    checked = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        f"Could not find {filename}. Checked: {checked}"
    )


CAREERS_FILE = resolve_data_file("careers.csv")
CAREER_SKILLS_FILE = resolve_data_file("career_skills.csv")


def import_careers():
    app = create_app()

    with app.app_context():
        print("Starting career dataset import...")
        print(f"Careers file: {CAREERS_FILE}")
        print(f"Career skills file: {CAREER_SKILLS_FILE}")

        career_count = 0
        skill_count = 0

        # -----------------------------
        # Import Careers
        # -----------------------------
        with CAREERS_FILE.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                title = (row.get("title") or "").strip()
                domain = (row.get("domain") or "").strip()
                description = (row.get("description") or "").strip()

                if not title or not domain:
                    continue

                existing = Career.query.filter_by(title=title).first()

                if existing:
                    existing.domain = domain
                    existing.description = description
                else:
                    career = Career(
                        title=title,
                        domain=domain,
                        description=description,
                    )
                    db.session.add(career)
                    career_count += 1

        db.session.commit()
        print(f"Careers created: {career_count}")

        # -----------------------------
        # Import Career Skills
        # -----------------------------
        with CAREER_SKILLS_FILE.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)

            for row in reader:
                career_title = (row.get("career_title") or "").strip()
                skill_name = (row.get("skill_name") or "").strip()

                if not career_title or not skill_name:
                    continue

                career = Career.query.filter_by(title=career_title).first()

                if not career:
                    print(f"WARNING: Career not found: {career_title}")
                    continue

                try:
                    required_level = int(row.get("required_level", 0))
                    importance = int(row.get("importance", 1))
                except (TypeError, ValueError):
                    print(
                        f"WARNING: Invalid skill levels for "
                        f"{career_title} / {skill_name}"
                    )
                    continue

                existing = CareerSkill.query.filter_by(
                    career_id=career.id,
                    skill_name=skill_name
                ).first()

                if existing:
                    existing.required_level = required_level
                    existing.importance = importance
                    continue

                db.session.add(
                    CareerSkill(
                        career_id=career.id,
                        skill_name=skill_name,
                        required_level=required_level,
                        importance=importance,
                    )
                )
                skill_count += 1

        db.session.commit()

        print(f"Career-skill mappings created: {skill_count}")
        print("Dataset import completed successfully!")


if __name__ == "__main__":
    import_careers()
