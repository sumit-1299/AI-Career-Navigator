import csv
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "onet" / "db_31_0_csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "onet"

INPUT_FILE = RAW_DIR / "knowledge.csv"

RELATIONSHIP_FILE = (
    OUTPUT_DIR / "knowledge_relationships.csv"
)

CANDIDATE_FILE = (
    OUTPUT_DIR / "knowledge_candidates.csv"
)


# ---------------------------------------------------------
# SOURCE INFORMATION
# ---------------------------------------------------------

SOURCE = "O*NET"
SOURCE_VERSION = "31.0"


# ---------------------------------------------------------
# NORMALIZATION FUNCTION
# ---------------------------------------------------------

def normalize_name(value):
    """
    Convert a knowledge-area name into a consistent
    comparison form.

    Example:
        'Computers and Electronics'
        -> 'computers and electronics'
    """

    value = unicodedata.normalize("NFKC", value)
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)

    return value


# ---------------------------------------------------------
# MAIN PROCESSING FUNCTION
# ---------------------------------------------------------

def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------
    # DATA STRUCTURES
    # -----------------------------------------------------

    relationships = defaultdict(dict)

    candidates = {}

    # -----------------------------------------------------
    # STEP 1: READ RAW O*NET KNOWLEDGE DATA
    # -----------------------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            soc_code = row["O*NET-SOC Code"].strip()
            title = row["Title"].strip()
            element_id = row["Element ID"].strip()
            element_name = row["Element Name"].strip()

            if not element_name:
                continue

            # ---------------------------------------------
            # Create one relationship per occupation
            # and knowledge area.
            # ---------------------------------------------

            key = (
                soc_code,
                element_id
            )

            relationships[key].update({
                "source": SOURCE,
                "source_version": SOURCE_VERSION,
                "onet_soc_code": soc_code,
                "occupation_title": title,
                "element_id": element_id,
                "element_name": element_name,
                "date": row["Date"].strip(),
                "domain_source": row["Domain Source"].strip()
            })

            # ---------------------------------------------
            # Store Importance and Level separately.
            # ---------------------------------------------

            scale_name = row["Scale Name"].strip().lower()
            value = row["Data Value"].strip()

            if scale_name == "importance":
                relationships[key]["importance"] = value

            elif scale_name == "level":
                relationships[key]["level"] = value

            # ---------------------------------------------
            # Build knowledge-area candidates.
            # ---------------------------------------------

            normalized_name = normalize_name(element_name)

            if normalized_name not in candidates:

                candidates[normalized_name] = {
                    "original_name": element_name,
                    "occurrence_count": 0
                }

            candidates[
                normalized_name
            ]["occurrence_count"] += 1

    # -----------------------------------------------------
    # STEP 2: WRITE KNOWLEDGE RELATIONSHIPS
    # -----------------------------------------------------

    with open(
        RELATIONSHIP_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        fieldnames = [
            "source",
            "source_version",
            "onet_soc_code",
            "occupation_title",
            "element_id",
            "element_name",
            "importance",
            "level",
            "date",
            "domain_source"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            lineterminator="\n"
        )

        writer.writeheader()

        for relationship in relationships.values():

            writer.writerow({
                "source": relationship.get(
                    "source", ""
                ),
                "source_version": relationship.get(
                    "source_version", ""
                ),
                "onet_soc_code": relationship.get(
                    "onet_soc_code", ""
                ),
                "occupation_title": relationship.get(
                    "occupation_title", ""
                ),
                "element_id": relationship.get(
                    "element_id", ""
                ),
                "element_name": relationship.get(
                    "element_name", ""
                ),
                "importance": relationship.get(
                    "importance", ""
                ),
                "level": relationship.get(
                    "level", ""
                ),
                "date": relationship.get(
                    "date", ""
                ),
                "domain_source": relationship.get(
                    "domain_source", ""
                )
            })

    # -----------------------------------------------------
    # STEP 3: WRITE KNOWLEDGE CANDIDATES
    # -----------------------------------------------------

    with open(
        CANDIDATE_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        fieldnames = [
            "source",
            "source_version",
            "original_name",
            "normalized_name",
            "occurrence_count"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            lineterminator="\n"
        )

        writer.writeheader()

        for normalized_name, candidate in sorted(
            candidates.items()
        ):

            writer.writerow({
                "source": SOURCE,
                "source_version": SOURCE_VERSION,
                "original_name": candidate[
                    "original_name"
                ],
                "normalized_name": normalized_name,
                "occurrence_count": candidate[
                    "occurrence_count"
                ]
            })

    # -----------------------------------------------------
    # STEP 4: SUMMARY
    # -----------------------------------------------------

    print("O*NET knowledge processing completed.")
    print()

    print(f"Input: {INPUT_FILE}")

    print(
        f"Relationship output: "
        f"{RELATIONSHIP_FILE}"
    )

    print(
        f"Candidate output: "
        f"{CANDIDATE_FILE}"
    )

    print()

    print(
        f"Unique occupation-knowledge relationships: "
        f"{len(relationships)}"
    )

    print(
        f"Unique knowledge candidates: "
        f"{len(candidates)}"
    )


# ---------------------------------------------------------
# PROGRAM ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    main()
