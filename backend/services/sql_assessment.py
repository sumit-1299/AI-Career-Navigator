"""Draft SQL diagnostic content and deterministic scoring.

Keep published versions immutable. New questions/rubrics require a new version.
SQL references and research limitations are recorded in docs/SQL_ASSESSMENT.md.
"""

from copy import deepcopy


ASSESSMENT = {
    "skill_key": "sql",
    "title": "SQL foundations diagnostic",
    "version": "sql-foundations-v1",
    "scoring_version": "equal-weight-with-skips-v1",
    "review_status": "draft_pending_human_review",
    "interpretation": (
        "Results describe performance on these questions, not a validated SQL "
        "proficiency level or a job-readiness score. Skipped questions are unassessed."
    ),
}

QUESTIONS = [
    {
        "id": "sql-filter-1", "topic": "filtering",
        "prompt": "Which clause filters individual rows before grouping?",
        "options": {"a": "HAVING", "b": "WHERE", "c": "ORDER BY", "d": "GROUP BY"},
        "correct_option_id": "b",
        "explanation": "WHERE filters input rows; HAVING filters groups after grouping.",
    },
    {
        "id": "sql-filter-2", "topic": "filtering",
        "prompt": "Which condition selects rows whose email column is SQL NULL?",
        "options": {
            "a": "email = NULL", "b": "email = ''",
            "c": "email IS NULL", "d": "email = 'NULL'",
        },
        "correct_option_id": "c",
        "explanation": "IS NULL tests for a missing SQL value. NULL is not an empty string.",
    },
    {
        "id": "sql-join-1", "topic": "joins",
        "prompt": (
            "customers has exactly two rows with id 1 and 2. orders has exactly "
            "two rows, both with customer_id 1. How many rows does this return? "
            "SELECT c.id FROM customers c INNER JOIN orders o ON o.customer_id = c.id;"
        ),
        "options": {"a": "1", "b": "3", "c": "4", "d": "2"},
        "correct_option_id": "d",
        "explanation": "Customer 1 produces one row per matching order; customer 2 has no match.",
    },
    {
        "id": "sql-join-2", "topic": "joins",
        "prompt": (
            "customers has exactly two rows with id 1 and 2. orders has exactly "
            "two rows, both with customer_id 1. How many rows does this return? "
            "SELECT c.id FROM customers c LEFT JOIN orders o ON o.customer_id = c.id;"
        ),
        "options": {"a": "3", "b": "2", "c": "1", "d": "4"},
        "correct_option_id": "a",
        "explanation": "Two rows match customer 1. LEFT JOIN also retains customer 2 as one row.",
    },
    {
        "id": "sql-aggregate-1", "topic": "aggregation",
        "prompt": (
            "Complete the query so it returns only customers with at least two orders: "
            "SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id ...;"
        ),
        "options": {
            "a": "WHERE COUNT(*) >= 2", "b": "HAVING COUNT(*) >= 2",
            "c": "ORDER BY COUNT(*) >= 2", "d": "LIMIT 2",
        },
        "correct_option_id": "b",
        "explanation": "HAVING applies a condition to each group and can use its aggregate count.",
    },
    {
        "id": "sql-aggregate-2", "topic": "aggregation",
        "prompt": (
            "A table contains exactly three rows with amount values 10, NULL and 20. "
            "What does SELECT COUNT(amount) FROM payments return?"
        ),
        "options": {"a": "3", "b": "30", "c": "2", "d": "NULL"},
        "correct_option_id": "c",
        "explanation": "COUNT(amount) counts non-NULL values; COUNT(*) would count all three rows.",
    },
]


def new_snapshot():
    return {"metadata": deepcopy(ASSESSMENT), "questions": deepcopy(QUESTIONS)}


def public_questions(questions):
    """Explicit allowlist: do not expose the answer key before submission."""
    return [
        {key: deepcopy(question[key]) for key in ("id", "topic", "prompt", "options")}
        for question in questions
    ]


def grade_answers(questions, answers):
    """Grade one option (or an explicit skip) per assigned question."""
    if not isinstance(answers, list) or len(answers) != len(questions):
        raise ValueError("Supply one answer per question; use option_id null to skip.")
    question_by_id = {question["id"]: question for question in questions}
    submitted = {}
    for answer in answers:
        if not isinstance(answer, dict) or set(answer) != {"question_id", "option_id"}:
            raise ValueError("Each answer must contain only question_id and option_id.")
        question_id, option_id = answer["question_id"], answer["option_id"]
        if not isinstance(question_id, str) or question_id not in question_by_id:
            raise ValueError("An answer refers to an unassigned question.")
        if question_id in submitted:
            raise ValueError("A question was answered more than once.")
        options = question_by_id[question_id]["options"]
        if option_id is not None and (not isinstance(option_id, str) or option_id not in options):
            raise ValueError("An answer contains an invalid option_id.")
        submitted[question_id] = option_id

    topics = {}
    feedback = []
    for question in questions:
        chosen = submitted[question["id"]]
        topic = topics.setdefault(question["topic"], {
            "topic": question["topic"], "question_count": 0,
            "answered_count": 0, "correct_count": 0,
        })
        answered = chosen is not None
        correct = answered and chosen == question["correct_option_id"]
        topic["question_count"] += 1
        topic["answered_count"] += int(answered)
        topic["correct_count"] += int(correct)
        feedback.append({
            "question_id": question["id"], "topic": question["topic"],
            "selected_option_id": chosen,
            "outcome": "unassessed" if not answered else ("correct" if correct else "incorrect"),
            "correct_option_id": question["correct_option_id"],
            "explanation": question["explanation"],
        })

    for topic in topics.values():
        topic["unanswered_count"] = topic["question_count"] - topic["answered_count"]
        topic["incorrect_count"] = topic["answered_count"] - topic["correct_count"]
        topic["practice_suggested"] = topic["incorrect_count"] > 0
        topic["additional_evidence_needed"] = topic["unanswered_count"] > 0
        if topic["answered_count"] == 0:
            topic["evidence_status"] = "not_assessed"
        elif topic["unanswered_count"]:
            topic["evidence_status"] = "incomplete"
        else:
            topic["evidence_status"] = "assessed_on_this_question_set"

    correct = sum(topic["correct_count"] for topic in topics.values())
    answered = sum(topic["answered_count"] for topic in topics.values())
    total = len(questions)
    return {
        "question_count": total, "answered_count": answered,
        "correct_count": correct, "incorrect_count": answered - correct,
        "unanswered_count": total - answered,
        "accuracy_on_answered_percent": round(100 * correct / answered, 2) if answered else None,
        "coverage_percent": round(100 * answered / total, 2),
        "topics": list(topics.values()), "feedback": feedback,
    }
