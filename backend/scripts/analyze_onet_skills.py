import csv
import re
from collections import Counter
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
    / "onet_skill_candidates.csv"
)


def normalize_name(name):
    """
    Normalize terminology for comparison.

    This does NOT decide whether two different
    concepts are actually the same skill.
    """
    name = name.strip().lower()
    name = re.sub(r"\s+", " ", name)
    return name


def main():

    skill_counter = Counter()
    original_names = {}

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            element_name = row["element_name"].strip()

            normalized = normalize_name(element_name)

            skill_counter[normalized] += 1

            if normalized not in original_names:
                original_names[normalized] = element_name

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "normalized_name",
            "original_name",
            "occurrence_count"
        ])

        for normalized, count in sorted(
            skill_counter.items(),
            key=lambda x: (-x[1], x[0])
        ):

            writer.writerow([
                normalized,
                original_names[normalized],
                count
            ])

    print("O*NET skill candidate analysis completed.")
    print(f"Unique normalized terms: {len(skill_counter)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
