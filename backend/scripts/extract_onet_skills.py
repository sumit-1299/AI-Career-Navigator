import csv
from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "onet" / "db_31_0_csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "onet"

INPUT_FILE = RAW_DIR / "essential_skills.csv"
OUTPUT_FILE = OUTPUT_DIR / "essential_skills_candidates.csv"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = []

    with open(INPUT_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append({
                "onet_soc_code": row["O*NET-SOC Code"],
                "occupation_title": row["Title"],
                "element_id": row["Element ID"],
                "element_name": row["Element Name"],
                "scale_id": row["Scale ID"],
                "scale_name": row["Scale Name"],
                "data_value": row["Data Value"],
                "date": row["Date"],
                "domain_source": row["Domain Source"]
            })

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        fieldnames = [
            "onet_soc_code",
            "occupation_title",
            "element_id",
            "element_name",
            "scale_id",
            "scale_name",
            "data_value",
            "date",
            "domain_source"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("O*NET skill extraction completed.")
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Rows extracted: {len(rows)}")


if __name__ == "__main__":
    main()
