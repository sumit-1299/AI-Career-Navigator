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

INPUT_FILE = RAW_DIR / "software_skills.csv"

EVIDENCE_FILE = OUTPUT_DIR / "software_skill_evidence.csv"
CANDIDATE_FILE = OUTPUT_DIR / "software_skill_candidates.csv"

WORKPLACE_CANDIDATE_FILE = (
    OUTPUT_DIR / "software_workplace_example_candidates.csv"
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
    Convert a name into a consistent comparison form.

    Example:
        'Atlassian JIRA'
        -> 'atlassian jira'
    """

    value = unicodedata.normalize("NFKC", value)
    value = value.strip().lower()
    value = re.sub(r"\s+", " ", value)

    return value


# ---------------------------------------------------------
# MAIN PROCESSING FUNCTION
# ---------------------------------------------------------

def main():

    # Create output directory if it does not exist.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------
    # DATA STRUCTURES
    # -----------------------------------------------------

    # Stores complete O*NET source-level evidence.
    evidence_rows = []

    # Stores normalized Element Name candidates.
    candidate_data = defaultdict(
        lambda: {
            "original_name": "",
            "occurrence_count": 0,
            "occupation_codes": set(),
            "hot_technology_count": 0,
            "in_demand_count": 0
        }
    )

    # Stores normalized Workplace Example candidates.
    workplace_data = defaultdict(
        lambda: {
            "original_name": "",
            "occurrence_count": 0,
            "occupation_codes": set(),
            "hot_technology_count": 0,
            "in_demand_count": 0
        }
    )

    # -----------------------------------------------------
    # STEP 1: READ RAW O*NET SOFTWARE SKILLS CSV
    # -----------------------------------------------------

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            # ---------------------------------------------
            # SOFTWARE CATEGORY
            # ---------------------------------------------

            technology_name = row["Element Name"].strip()

            if not technology_name:
                continue

            normalized_name = normalize_name(technology_name)

            # ---------------------------------------------
            # WORKPLACE EXAMPLE
            # ---------------------------------------------

            workplace_example = row["Workplace Example"].strip()

            if workplace_example:

                normalized_example = normalize_name(
                    workplace_example
                )

                workplace = workplace_data[
                    normalized_example
                ]

                if not workplace["original_name"]:
                    workplace["original_name"] = (
                        workplace_example
                    )

                workplace["occurrence_count"] += 1

                workplace["occupation_codes"].add(
                    row["O*NET-SOC Code"].strip()
                )

                if (
                    row["Hot Technology"]
                    .strip()
                    .upper()
                    == "Y"
                ):
                    workplace["hot_technology_count"] += 1

                if (
                    row["In Demand"]
                    .strip()
                    .upper()
                    == "Y"
                ):
                    workplace["in_demand_count"] += 1

            # ---------------------------------------------
            # PRESERVE SOURCE-LEVEL EVIDENCE
            # ---------------------------------------------

            evidence_rows.append({
                "source": SOURCE,
                "source_version": SOURCE_VERSION,
                "onet_soc_code": row[
                    "O*NET-SOC Code"
                ].strip(),
                "occupation_title": row[
                    "Title"
                ].strip(),
                "workplace_example": row[
                    "Workplace Example"
                ].strip(),
                "element_id": row[
                    "Element ID"
                ].strip(),
                "element_name": technology_name,
                "hot_technology": row[
                    "Hot Technology"
                ].strip(),
                "in_demand": row[
                    "In Demand"
                ].strip()
            })

            # ---------------------------------------------
            # BUILD SOFTWARE CATEGORY STATISTICS
            # ---------------------------------------------

            candidate = candidate_data[
                normalized_name
            ]

            if not candidate["original_name"]:
                candidate["original_name"] = (
                    technology_name
                )

            candidate["occurrence_count"] += 1

            candidate["occupation_codes"].add(
                row["O*NET-SOC Code"].strip()
            )

            if (
                row["Hot Technology"]
                .strip()
                .upper()
                == "Y"
            ):
                candidate["hot_technology_count"] += 1

            if (
                row["In Demand"]
                .strip()
                .upper()
                == "Y"
            ):
                candidate["in_demand_count"] += 1

    # -----------------------------------------------------
    # STEP 2: WRITE SOURCE EVIDENCE
    # -----------------------------------------------------

    with open(
        EVIDENCE_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        fieldnames = [
            "source",
            "source_version",
            "onet_soc_code",
            "occupation_title",
            "workplace_example",
            "element_id",
            "element_name",
            "hot_technology",
            "in_demand"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            lineterminator="\n"
        )

        writer.writeheader()
        writer.writerows(evidence_rows)

    # -----------------------------------------------------
    # STEP 3: WRITE SOFTWARE CATEGORY CANDIDATES
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
            "occurrence_count",
            "occupation_count",
            "hot_technology_count",
            "in_demand_count"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            lineterminator="\n"
        )

        writer.writeheader()

        for normalized_name, candidate in sorted(
            candidate_data.items()
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
                ],
                "occupation_count": len(
                    candidate["occupation_codes"]
                ),
                "hot_technology_count": candidate[
                    "hot_technology_count"
                ],
                "in_demand_count": candidate[
                    "in_demand_count"
                ]
            })

    # -----------------------------------------------------
    # STEP 4: WRITE WORKPLACE EXAMPLE CANDIDATES
    # -----------------------------------------------------

    with open(
        WORKPLACE_CANDIDATE_FILE,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        fieldnames = [
            "source",
            "source_version",
            "original_name",
            "normalized_name",
            "occurrence_count",
            "occupation_count",
            "hot_technology_count",
            "in_demand_count"
        ]

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            lineterminator="\n"
        )

        writer.writeheader()

        for normalized_name, workplace in sorted(
            workplace_data.items()
        ):

            writer.writerow({
                "source": SOURCE,
                "source_version": SOURCE_VERSION,
                "original_name": workplace[
                    "original_name"
                ],
                "normalized_name": normalized_name,
                "occurrence_count": workplace[
                    "occurrence_count"
                ],
                "occupation_count": len(
                    workplace["occupation_codes"]
                ),
                "hot_technology_count": workplace[
                    "hot_technology_count"
                ],
                "in_demand_count": workplace[
                    "in_demand_count"
                ]
            })

    # -----------------------------------------------------
    # STEP 5: SUMMARY
    # -----------------------------------------------------

    print("O*NET software skills processing completed.")
    print()

    print(f"Input: {INPUT_FILE}")
    print(f"Evidence output: {EVIDENCE_FILE}")
    print(f"Category candidates: {CANDIDATE_FILE}")
    print(
        f"Workplace candidates: "
        f"{WORKPLACE_CANDIDATE_FILE}"
    )

    print()

    print(
        f"Evidence rows: "
        f"{len(evidence_rows)}"
    )

    print(
        f"Unique software categories: "
        f"{len(candidate_data)}"
    )

    print(
        f"Unique workplace examples: "
        f"{len(workplace_data)}"
    )


# ---------------------------------------------------------
# PROGRAM ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    main()
