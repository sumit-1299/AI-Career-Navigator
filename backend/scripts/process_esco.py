import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "esco"
    / "ESCO dataset - v1.2.1 - classification - en - csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "esco"


OCCUPATIONS_FILE = RAW_DIR / "occupations_en.csv"
SKILLS_FILE = RAW_DIR / "skills_en.csv"
RELATIONS_FILE = RAW_DIR / "occupationSkillRelations_en.csv"


def process_occupations():
    output_file = OUTPUT_DIR / "occupations.csv"

    fields = [
        "occupation_uri",
        "occupation_label",
        "isco_group",
        "occupation_code",
        "definition",
        "description",
        "alternative_labels",
        "status",
        "modified_date",
    ]

    count = 0

    with open(
        OCCUPATIONS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        with open(
            output_file,
            "w",
            encoding="utf-8",
            newline=""
        ) as output:

            writer = csv.DictWriter(
                output,
                fieldnames=fields
            )

            writer.writeheader()

            for row in reader:

                writer.writerow({
                    "occupation_uri": row["conceptUri"],
                    "occupation_label": row["preferredLabel"],
                    "isco_group": row["iscoGroup"],
                    "occupation_code": row["code"],
                    "definition": row["definition"],
                    "description": row["description"],
                    "alternative_labels": row["altLabels"],
                    "status": row["status"],
                    "modified_date": row["modifiedDate"],
                })

                count += 1

    print(f"Occupations processed: {count}")
    print(f"Output: {output_file}")


def process_skills():
    output_file = OUTPUT_DIR / "skills.csv"

    fields = [
        "skill_uri",
        "skill_type",
        "reuse_level",
        "skill_label",
        "alternative_labels",
        "definition",
        "description",
        "status",
        "modified_date",
    ]

    count = 0

    with open(
        SKILLS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        with open(
            output_file,
            "w",
            encoding="utf-8",
            newline=""
        ) as output:

            writer = csv.DictWriter(
                output,
                fieldnames=fields
            )

            writer.writeheader()

            for row in reader:

                writer.writerow({
                    "skill_uri": row["conceptUri"],
                    "skill_type": row["skillType"],
                    "reuse_level": row["reuseLevel"],
                    "skill_label": row["preferredLabel"],
                    "alternative_labels": row["altLabels"],
                    "definition": row["definition"],
                    "description": row["description"],
                    "status": row["status"],
                    "modified_date": row["modifiedDate"],
                })

                count += 1

    print(f"Skills processed: {count}")
    print(f"Output: {output_file}")


def process_relations():
    output_file = OUTPUT_DIR / "occupation_skill_relations.csv"

    fields = [
        "occupation_uri",
        "occupation_label",
        "relation_type",
        "skill_uri",
        "skill_label",
    ]

    count = 0

    with open(
        RELATIONS_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        with open(
            output_file,
            "w",
            encoding="utf-8",
            newline=""
        ) as output:

            writer = csv.DictWriter(
                output,
                fieldnames=fields
            )

            writer.writeheader()

            for row in reader:

                writer.writerow({
                    "occupation_uri": row["occupationUri"],
                    "occupation_label": row["occupationLabel"],
                    "relation_type": row["relationType"],
                    "skill_uri": row["skillUri"],
                    "skill_label": row["skillLabel"],
                })

                count += 1

    print(f"Occupation-skill relationships processed: {count}")
    print(f"Output: {output_file}")


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Processing ESCO v1.2.1...")
    print()

    process_occupations()

    process_skills()

    process_relations()

    print()
    print("ESCO processing completed successfully.")


if __name__ == "__main__":
    main()
