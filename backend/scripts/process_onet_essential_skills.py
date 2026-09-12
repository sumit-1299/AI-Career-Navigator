import csv
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "onet"
    / "essential_skills_candidates.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "onet"
    / "onet_essential_skill_relationships.csv"
)


def main():

    relationships = defaultdict(dict)

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            key = (
                row["onet_soc_code"],
                row["element_id"]
            )

            relationships[key].update({
                "onet_soc_code": row["onet_soc_code"],
                "occupation_title": row["occupation_title"],
                "element_id": row["element_id"],
                "element_name": row["element_name"],
                "date": row["date"],
                "domain_source": row["domain_source"]
            })

            scale_name = row["scale_name"].strip().lower()
            value = row["data_value"].strip()

            if scale_name == "importance":
                relationships[key]["importance"] = value

            elif scale_name == "level":
                relationships[key]["level"] = value

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "onet_soc_code",
        "occupation_title",
        "element_id",
        "element_name",
        "importance",
        "level",
        "date",
        "domain_source"
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for relationship in relationships.values():

            writer.writerow({
                "onet_soc_code": relationship.get("onet_soc_code", ""),
                "occupation_title": relationship.get("occupation_title", ""),
                "element_id": relationship.get("element_id", ""),
                "element_name": relationship.get("element_name", ""),
                "importance": relationship.get("importance", ""),
                "level": relationship.get("level", ""),
                "date": relationship.get("date", ""),
                "domain_source": relationship.get("domain_source", "")
            })

    print("O*NET essential skill relationships processed.")
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Relationships created: {len(relationships)}")


if __name__ == "__main__":
    main()
