import csv
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed" / "esco"


def read_column(filename, column):
    path = DATA_DIR / filename

    values = []

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            value = row[column].strip()

            if value:
                values.append(value)

    return values


def main():

    print("Validating ESCO processed dataset...")
    print()

    occupations = read_column(
        "occupations.csv",
        "occupation_uri"
    )

    skills = read_column(
        "skills.csv",
        "skill_uri"
    )

    relation_path = DATA_DIR / "occupation_skill_relations.csv"

    relation_count = 0
    relation_types = Counter()

    occupation_uris = set(occupations)
    skill_uris = set(skills)

    missing_occupations = set()
    missing_skills = set()

    with open(
        relation_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            relation_count += 1

            occupation_uri = row["occupation_uri"].strip()
            skill_uri = row["skill_uri"].strip()
            relation_type = row["relation_type"].strip()

            relation_types[relation_type] += 1

            if occupation_uri not in occupation_uris:
                missing_occupations.add(occupation_uri)

            if skill_uri not in skill_uris:
                missing_skills.add(skill_uri)

    print(f"Unique occupation URIs: {len(occupation_uris)}")
    print(f"Unique skill URIs: {len(skill_uris)}")
    print(f"Relationships: {relation_count}")

    print()
    print("Relationship types:")

    for relation_type, count in relation_types.items():
        print(f"  {relation_type}: {count}")

    print()
    print(f"Missing occupation references: {len(missing_occupations)}")
    print(f"Missing skill references: {len(missing_skills)}")

    print()

    if not missing_occupations and not missing_skills:
        print("ESCO relationship integrity check: PASSED")
    else:
        print("ESCO relationship integrity check: REVIEW REQUIRED")


if __name__ == "__main__":
    main()
