import csv
import re
import unicodedata
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]

ONET_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "onet"
    / "onet_skill_candidates.csv"
)

ESCO_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "esco"
    / "skills.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "skill_candidates.csv"


def normalize_skill_name(name):
    """
    Create a deterministic comparison form.

    This does NOT create a canonical skill.
    It only makes source terminology easier to compare.
    """

    name = unicodedata.normalize("NFKC", name)

    name = name.strip().lower()

    name = re.sub(r"\s+", " ", name)

    name = re.sub(r"[^\w\s+#./-]", "", name)

    return name


def load_onet_candidates():
    candidates = []

    with open(
        ONET_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            original_name = row["original_name"].strip()

            if not original_name:
                continue

            candidates.append({
                "source": "O*NET",
                "source_version": "31.0",
                "source_skill_id": "",
                "original_name": original_name,
                "normalized_name": normalize_skill_name(original_name),
                "occurrence_count": row["occurrence_count"],
            })

    return candidates


def load_esco_candidates():
    candidates = []

    with open(
        ESCO_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            original_name = row["skill_label"].strip()

            if not original_name:
                continue

            candidates.append({
                "source": "ESCO",
                "source_version": "1.2.1",
                "source_skill_id": row["skill_uri"],
                "original_name": original_name,
                "normalized_name": normalize_skill_name(original_name),
                "occurrence_count": "1",
            })

    return candidates


def remove_duplicates(candidates):
    """
    Keep one record for each source + original skill identifier.
    """

    unique = {}

    for candidate in candidates:

        key = (
            candidate["source"],
            candidate["source_skill_id"],
            candidate["original_name"],
        )

        unique[key] = candidate

    return list(unique.values())


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Building cross-source skill candidate dataset...")
    print()

    onet_candidates = load_onet_candidates()
    esco_candidates = load_esco_candidates()

    print(f"O*NET candidates loaded: {len(onet_candidates)}")
    print(f"ESCO candidates loaded: {len(esco_candidates)}")

    candidates = onet_candidates + esco_candidates

    candidates = remove_duplicates(candidates)

    fields = [
        "source",
        "source_version",
        "source_skill_id",
        "original_name",
        "normalized_name",
        "occurrence_count",
    ]

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            lineterminator="\n"
        )

        writer.writeheader()

        for candidate in sorted(
            candidates,
            key=lambda x: (
                x["normalized_name"],
                x["source"]
            )
        ):
            writer.writerow(candidate)

    print()
    print(f"Total candidates: {len(candidates)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
