"""Versioned, curated SQL learning resources and an explainable baseline policy.

Resources were checked on 2026-09-26. Practice tasks are original project content.
Do not modify a published version: bump the version for future catalogue changes.
Saved roadmaps contain snapshots so later edits do not rewrite past recommendations.
"""

from copy import deepcopy

from services.foundations_resources import CATALOGS


CATALOG_VERSION = "sql-resources-2026-09-26-v1"
POLICY_VERSION = "topic-evidence-rules-v1"
REVIEWED_ON = "2026-09-26"
TOPIC_ORDER = ("filtering", "joins", "aggregation")


def resource(title, provider, url, kind, focus):
    return {
        "title": title, "provider": provider, "url": url,
        "kind": kind, "focus": focus, "checked_on": REVIEWED_ON,
    }


QUERYING = resource(
    "CS50 SQL: Querying", "Harvard CS50",
    "https://cs50.harvard.edu/sql/weeks/0/", "course_lesson",
    "Use the sections on WHERE, NULL and aggregate functions.",
)
RELATING = resource(
    "CS50 SQL: Relating", "Harvard CS50",
    "https://cs50.harvard.edu/sql/weeks/1/", "course_lesson",
    "Use the sections on table relationships, joins, GROUP BY and HAVING.",
)

CATALOG = {
    "filtering": {
        "title": "Filter rows and handle missing values",
        "objective": "Use WHERE with multiple conditions and distinguish NULL from zero.",
        "resources": [QUERYING, resource(
            "Querying a table", "PostgreSQL 18 documentation",
            "https://www.postgresql.org/docs/18/tutorial-select.html", "reference",
            "Review row selection and sorting with SELECT, WHERE and ORDER BY.",
        )],
        "task": {
            "title": "Find items with an unknown discount",
            "starter_sql": (
                "WITH items(item_id, price, discount) AS (\n"
                "  VALUES (101, 450, NULL), (102, 650, 10),\n"
                "         (103, 300, 0), (104, 520, NULL)\n"
                ")\n-- Add your SELECT below."
            ),
            "instructions": [
                "Return item_id for items priced at least 400 whose discount is NULL.",
                "Sort the IDs in ascending order.",
                "Explain why a missing discount and a discount of zero are different.",
            ],
            "self_check": "The result contains exactly item IDs 101 and 104, in that order.",
        },
    },
    "joins": {
        "title": "Connect tables without losing unmatched rows",
        "objective": "Explain how matching orders and unmatched customers affect join results.",
        "resources": [RELATING, resource(
            "Joins between tables", "PostgreSQL 18 documentation",
            "https://www.postgresql.org/docs/18/tutorial-join.html", "reference",
            "Compare inner joins with left joins, including unmatched rows.",
        )],
        "task": {
            "title": "Keep customers who have no orders",
            "starter_sql": (
                "WITH customers(customer_id, name) AS (\n"
                "  VALUES (11, 'Anaya'), (12, 'Kabir'), (13, 'Mira')\n"
                "), orders(order_id, customer_id) AS (\n"
                "  VALUES (501, 11), (502, 11), (503, 13)\n"
                ")\n-- Add your SELECT below."
            ),
            "instructions": [
                "Write an INNER JOIN returning customer_id and order_id, sorted by both IDs.",
                "Repeat with a LEFT JOIN from customers to orders.",
                "Explain why one customer appears twice and another appears only in the left join.",
            ],
            "self_check": (
                "The inner join returns (11, 501), (11, 502), (13, 503). "
                "The left join also includes (12, NULL), giving four rows."
            ),
        },
    },
    "aggregation": {
        "title": "Summarise groups and count missing values correctly",
        "objective": "Combine GROUP BY, HAVING, COUNT(*) and COUNT(column) with NULL values.",
        "resources": [QUERYING, RELATING, resource(
            "Aggregate functions", "PostgreSQL 18 documentation",
            "https://www.postgresql.org/docs/18/tutorial-agg.html", "reference",
            "Review grouping and the different roles of WHERE and HAVING.",
        )],
        "task": {
            "title": "Summarise customer payments",
            "starter_sql": (
                "WITH payments(payment_id, customer_id, amount) AS (\n"
                "  VALUES (801, 11, 100), (802, 11, NULL), (803, 11, 250),\n"
                "         (804, 12, 75), (805, 12, 125), (806, 13, NULL)\n"
                ")\n-- Add your SELECT below."
            ),
            "instructions": [
                "For each customer, return customer_id, COUNT(*), COUNT(amount) and SUM(amount).",
                "Keep only customers with at least two payment rows using HAVING.",
                "Sort by customer_id and explain the two different counts for customer 11.",
            ],
            "self_check": (
                "Rows are (11, 3, 2, 350) and (12, 2, 2, 200). "
                "Customer 13 is excluded by the group-size condition."
            ),
        },
    },
}


def build_roadmap(result, assessment_version, scoring_version, skill_key="sql"):
    """Derive suggestions from assessment evidence; never infer deficits from skips."""
    if skill_key == "sql":
        catalog, order, version = CATALOG, TOPIC_ORDER, CATALOG_VERSION
        ordering = "Filtering, joins, then aggregation; topics with no flagged need are omitted."
        evidence = "Keep your SQL queries, outputs and explanations for review. "
    elif skill_key in CATALOGS:
        config = CATALOGS[skill_key]
        catalog, order, version = config["catalog"], tuple(config["catalog"]), config["version"]
        ordering = config["ordering"]
        evidence = "Keep your solutions, outputs and explanations for review. "
    else:
        raise ValueError("A resource catalogue is not available for this assessment skill.")
    topics = {topic["topic"]: topic for topic in result["topics"]}
    steps = []
    for name in order:
        topic = topics.get(name)
        if topic is None:
            continue
        incorrect, unanswered = topic["incorrect_count"], topic["unanswered_count"]
        if not incorrect and not unanswered:
            continue
        kind = "practice" if incorrect else "collect_evidence"
        topic_label = name.replace("_", " ")
        if incorrect:
            reason = f"{incorrect} of {topic['answered_count']} answered questions in {topic_label} were incorrect."
            if unanswered:
                reason += f" {unanswered} question(s) also remain unassessed."
        else:
            reason = (
                f"{unanswered} question(s) in {topic_label} remain unassessed. "
                "There is not enough evidence to infer a skill gap from those skips."
            )
        steps.append({
            "id": name, "topic": name, "position": len(steps) + 1,
            "kind": kind, "reason": reason,
            "resource_guidance": (
                "Review the relevant lesson sections, then try the practice task."
                if kind == "practice" else
                "Try the task first. Use the learning resources as optional support if needed."
            ),
            "source_counts": {key: topic[key] for key in (
                "question_count", "answered_count", "correct_count", "incorrect_count", "unanswered_count"
            )},
            **deepcopy(catalog[name]),
        })
    return {
        "catalog_version": version, "policy_version": POLICY_VERSION,
        "source_assessment_version": assessment_version,
        "source_scoring_version": scoring_version,
        "content_review_status": "draft_pending_human_review",
        "ordering": ordering,
        "summary": {key: result[key] for key in (
            "question_count", "answered_count", "correct_count", "incorrect_count", "unanswered_count"
        )},
        "steps": steps,
        "unmapped_topics": sorted(set(topics) - set(catalog)),
        "progress_interpretation": (
            "Completion records self-reported learning activity only. It does not verify "
            "a skill, alter an assessment result, or establish a proficiency improvement."
        ),
        "next_evidence": (
            evidence +
            "Use new, independently reviewed tasks for reassessment; repeating the same "
            "multiple-choice questions does not independently measure learning gains."
        ),
    }
