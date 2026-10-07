import csv
import os
import sys

# Add backend directory to Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import create_app
from extensions import db
from models.career import Career
from models.career_skill import CareerSkill


PROJECT_ROOT = os.path.dirname(BASE_DIR)

CAREERS_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "careers.csv"
)

CAREER_SKILLS_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "career_skills.csv"
)


def import_careers():
    app = create_app()

    with app.app_context():

        print("Starting career dataset import...")

        # -----------------------------
        # Import Careers
        # -----------------------------
        with open(CAREERS_FILE, "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            career_count = 0

            for row in reader:

                existing = Career.query.filter_by(
                    title=row["title"]
                ).first()

                if existing:
                    career = existing
                else:
                    career = Career(
                        title=row["title"],
                        domain=row["domain"],
                        description=row["description"]
                    )

                    db.session.add(career)
                    db.session.flush()

                    career_count += 1

        db.session.commit()

        print(f"Careers imported: {career_count}")

        # -----------------------------
        # Import Career Skills
        # -----------------------------
        with open(CAREER_SKILLS_FILE, "r", encoding="utf-8") as file:

            reader = csv.DictReader(file)

            skill_count = 0

            for row in reader:

                career = Career.query.filter_by(
                    title=row["career_title"]
                ).first()

                if not career:
                    print(
                        f"WARNING: Career not found: "
                        f"{row['career_title']}"
                    )
                    continue

                existing = CareerSkill.query.filter_by(
                    career_id=career.id,
                    skill_name=row["skill_name"]
                ).first()

                if existing:
                    continue

                career_skill = CareerSkill(
                    career_id=career.id,
                    skill_name=row["skill_name"],
                    required_level=int(row["required_level"]),
                    importance=int(row["importance"])
                )

                db.session.add(career_skill)

                skill_count += 1

        db.session.commit()

        print(f"Career-skill mappings imported: {skill_count}")

        print("Dataset import completed successfully!")


if __name__ == "__main__":
    import_careers()
