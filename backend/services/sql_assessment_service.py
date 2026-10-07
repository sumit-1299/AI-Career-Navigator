"""SQL Foundations Diagnostic Service.

Provides immutable question bank and deterministic scoring for relational database
foundations (WHERE vs HAVING, NULL handling, JOIN cardinality, aggregation, subqueries).
Operates completely in-memory with zero database mutation.
"""

from copy import deepcopy

ASSESSMENT_METADATA = {
    "skill_key": "sql",
    "title": "SQL Foundations Diagnostic",
    "version": "sql-foundations-v1",
    "scoring_version": "equal-weight-with-skips-v1",
    "description": (
        "Foundational diagnostic evaluating knowledge of core relational SQL principles, "
        "filtering mechanisms, join semantics, null arithmetic, and query aggregation."
    ),
}

QUESTIONS = [
    {
        "id": "sql-filter-1",
        "topic": "filtering",
        "prompt": "Which SQL clause filters individual rows before grouping occurs?",
        "options": {
            "a": "HAVING",
            "b": "WHERE",
            "c": "ORDER BY",
            "d": "GROUP BY",
        },
        "correct_option_id": "b",
        "explanation": "WHERE filters source rows before aggregation; HAVING filters aggregated groups after GROUP BY.",
    },
    {
        "id": "sql-filter-2",
        "topic": "filtering",
        "prompt": "Which condition correctly selects rows where the email column is SQL NULL?",
        "options": {
            "a": "email = NULL",
            "b": "email = ''",
            "c": "email IS NULL",
            "d": "email = 'NULL'",
        },
        "correct_option_id": "c",
        "explanation": "In ANSI SQL, IS NULL tests for missing values. Comparing with = NULL yields UNKNOWN/false.",
    },
    {
        "id": "sql-join-1",
        "topic": "joins",
        "prompt": (
            "Table 'customers' has 2 rows (id 1, 2). Table 'orders' has 2 rows (both with customer_id = 1). "
            "How many rows does 'SELECT c.id FROM customers c INNER JOIN orders o ON o.customer_id = c.id' return?"
        ),
        "options": {
            "a": "0",
            "b": "1",
            "c": "2",
            "d": "4",
        },
        "correct_option_id": "c",
        "explanation": "Customer 1 matches both rows in orders, producing 2 joined rows. Customer 2 has no match.",
    },
    {
        "id": "sql-aggregate-1",
        "topic": "aggregation",
        "prompt": "What does 'SELECT department_id, COUNT(*) FROM employees GROUP BY department_id' return?",
        "options": {
            "a": "The total count of all employees in the entire table",
            "b": "The count of employees for each distinct department_id",
            "c": "Only departments with more than 1 employee",
            "d": "A syntax error because COUNT(*) cannot be used with GROUP BY",
        },
        "correct_option_id": "b",
        "explanation": "GROUP BY partitions rows by department_id and COUNT(*) evaluates the row count for each group.",
    },
    {
        "id": "sql-null-1",
        "topic": "null_semantics",
        "prompt": "What is the result of the SQL expression '10 + NULL'?",
        "options": {
            "a": "10",
            "b": "0",
            "c": "NULL",
            "d": "A syntax error",
        },
        "correct_option_id": "c",
        "explanation": "In standard SQL three-valued logic, arithmetic operations involving NULL evaluate to NULL.",
    },
    {
        "id": "sql-subquery-1",
        "topic": "subqueries",
        "prompt": "Which operator tests whether a subquery returns at least one row?",
        "options": {
            "a": "IN",
            "b": "EXISTS",
            "c": "ANY",
            "d": "BETWEEN",
        },
        "correct_option_id": "b",
        "explanation": "EXISTS returns TRUE as soon as the subquery produces at least one row, offering efficient short-circuiting.",
    },
]


class SqlAssessmentService:
    """Service providing SQL foundations diagnostic questions and deterministic scoring."""

    @classmethod
    def get_assessment(cls, include_solutions=False):
        """Return the assessment metadata and questions list."""
        questions_copy = []
        for q in QUESTIONS:
            item = {
                "id": q["id"],
                "topic": q["topic"],
                "prompt": q["prompt"],
                "options": deepcopy(q["options"]),
            }
            if include_solutions:
                item["correct_option_id"] = q["correct_option_id"]
                item["explanation"] = q["explanation"]
            questions_copy.append(item)

        return {
            "status": "success",
            "metadata": deepcopy(ASSESSMENT_METADATA),
            "total_questions": len(QUESTIONS),
            "questions": questions_copy,
        }

    @classmethod
    def evaluate(cls, answers):
        """Evaluate submitted user answers and compute score and topic breakdowns."""
        if not isinstance(answers, dict):
            answers = {}

        total = len(QUESTIONS)
        correct_count = 0
        answered_count = 0
        skipped_count = 0

        topic_stats = {}
        itemized_results = []

        for q in QUESTIONS:
            qid = q["id"]
            topic = q["topic"]
            correct_opt = q["correct_option_id"]

            if topic not in topic_stats:
                topic_stats[topic] = {"total": 0, "correct": 0}
            topic_stats[topic]["total"] += 1

            user_choice = answers.get(qid)
            if user_choice is None or str(user_choice).strip() == "":
                skipped_count += 1
                is_correct = False
                result_entry = {
                    "question_id": qid,
                    "topic": topic,
                    "prompt": q["prompt"],
                    "status": "skipped",
                    "user_answer": None,
                    "correct_answer": correct_opt,
                    "explanation": q["explanation"],
                }
            else:
                answered_count += 1
                cleaned_choice = str(user_choice).strip().lower()
                is_correct = (cleaned_choice == correct_opt.lower())
                if is_correct:
                    correct_count += 1
                    topic_stats[topic]["correct"] += 1

                result_entry = {
                    "question_id": qid,
                    "topic": topic,
                    "prompt": q["prompt"],
                    "status": "correct" if is_correct else "incorrect",
                    "user_answer": cleaned_choice,
                    "correct_answer": correct_opt,
                    "explanation": q["explanation"],
                }

            itemized_results.append(result_entry)

        score_percent = round((correct_count / total) * 100, 1) if total > 0 else 0.0

        topic_breakdown = {}
        for topic, stats in topic_stats.items():
            t_total = stats["total"]
            t_correct = stats["correct"]
            topic_breakdown[topic] = {
                "total": t_total,
                "correct": t_correct,
                "percentage": round((t_correct / t_total) * 100, 1) if t_total > 0 else 0.0,
            }

        readiness_level = "Foundational Mastery" if score_percent >= 80 else (
            "Developing Competency" if score_percent >= 50 else "Prerequisite Review Required"
        )

        return {
            "status": "success",
            "metadata": deepcopy(ASSESSMENT_METADATA),
            "score_percentage": score_percent,
            "readiness_level": readiness_level,
            "total_questions": total,
            "correct_count": correct_count,
            "answered_count": answered_count,
            "skipped_count": skipped_count,
            "topic_breakdown": topic_breakdown,
            "itemized_results": itemized_results,
        }
