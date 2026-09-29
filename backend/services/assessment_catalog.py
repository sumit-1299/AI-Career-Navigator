"""Draft, versioned diagnostics. The original SQL bank remains unchanged.

Questions are original project content, not copied from the linked learning
resources. Six items sample foundations; they do not validate proficiency.
"""

from copy import deepcopy

from services import sql_assessment
from services.skill_catalog import BY_KEY


def metadata(key, title, version):
    return {
        "skill_key": key, "title": title, "version": version,
        "scoring_version": "equal-weight-with-skips-v1",
        "review_status": "draft_pending_human_review",
        "interpretation": (
            "Results describe performance on these questions, not a validated "
            f"{BY_KEY[key]['label']} proficiency level or a job-readiness score. "
            "Skipped questions are unassessed."
        ),
    }


PYTHON_QUESTIONS = [
    {
        "id": "python-functions-1", "topic": "functions",
        "prompt": "A Python function reaches its end without executing a return statement. What value does the call return?",
        "options": {"a": "0", "b": "None", "c": "An empty string", "d": "The last local variable"},
        "correct_option_id": "b",
        "explanation": "Falling off the end of a Python function returns None. Printing a value does not return it.",
    },
    {
        "id": "python-functions-2", "topic": "functions",
        "prompt": "What does this Python code print?\ndef total(price, quantity=2):\n    return price * quantity\nprint(total(4, quantity=3))",
        "options": {"a": "12", "b": "8", "c": "7", "d": "It raises TypeError"},
        "correct_option_id": "a",
        "explanation": "The explicit quantity=3 overrides the default of 2; 4 multiplied by 3 is 12.",
    },
    {
        "id": "python-collections-1", "topic": "collections",
        "prompt": "What does this Python code print?\nvalues = [3, 5]\nalias = values\nalias.append(8)\nprint(len(values))",
        "options": {"a": "2", "b": "8", "c": "1", "d": "3"},
        "correct_option_id": "d",
        "explanation": "Assignment makes alias refer to the same list. Appending through alias changes that list.",
    },
    {
        "id": "python-collections-2", "topic": "collections",
        "prompt": "What does this Python code print?\ncounts = {'ready': 2}\nprint(counts.get('waiting', 0))",
        "options": {"a": "2", "b": "None", "c": "0", "d": "It raises KeyError"},
        "correct_option_id": "c",
        "explanation": "dict.get returns the supplied default when the key is absent, without adding the key.",
    },
    {
        "id": "python-exceptions-1", "topic": "exceptions",
        "prompt": "Which exception does int('pear') raise in Python?",
        "options": {"a": "KeyError", "b": "ValueError", "c": "IndexError", "d": "It returns 0"},
        "correct_option_id": "b",
        "explanation": "The string has the right input type for int but does not represent an integer, so conversion raises ValueError.",
    },
    {
        "id": "python-exceptions-2", "topic": "exceptions",
        "prompt": "In normal Python execution, which block is used for cleanup whether the associated try block succeeds or raises an exception?",
        "options": {"a": "else only", "b": "except ValueError only", "c": "A new unrelated try block", "d": "finally"},
        "correct_option_id": "d",
        "explanation": "A finally block runs as control leaves the try statement, including normal completion and exception propagation.",
    },
]

REST_QUESTIONS = [
    {
        "id": "rest-methods-1", "topic": "http_methods",
        "prompt": "An HTTP API provides /books/42. Which method is intended to retrieve the book representation without requesting a state change?",
        "options": {"a": "GET", "b": "POST", "c": "DELETE", "d": "PATCH"},
        "correct_option_id": "a",
        "explanation": "GET requests a representation and is defined as safe; incidental effects such as server logging can still occur.",
    },
    {
        "id": "rest-methods-2", "topic": "http_methods",
        "prompt": "For an HTTP API that follows standard method semantics, what does it mean that PUT is idempotent?",
        "options": {"a": "PUT cannot change server state", "b": "Every response must be identical", "c": "Repeating the identical request has the same intended server effect as sending it once", "d": "PUT never needs authentication"},
        "correct_option_id": "c",
        "explanation": "Idempotence concerns the intended effect on the server, not identical response codes, logs or authentication requirements.",
    },
    {
        "id": "rest-status-1", "topic": "status_codes",
        "prompt": "A POST request successfully creates a new resource. Which HTTP status specifically communicates that creation?",
        "options": {"a": "404", "b": "201", "c": "204", "d": "500"},
        "correct_option_id": "b",
        "explanation": "201 Created reports successful creation. 204 means success without response content, not specifically creation.",
    },
    {
        "id": "rest-status-2", "topic": "status_codes",
        "prompt": "An API documents that authenticated callers receive 404 when a requested item does not exist. Which response should GET /items/999 return when that item is absent?",
        "options": {"a": "500", "b": "201", "c": "301", "d": "404"},
        "correct_option_id": "d",
        "explanation": "Under the stated contract, 404 reports that the requested item was not found; its absence alone is not an internal server failure.",
    },
    {
        "id": "rest-representations-1", "topic": "representations",
        "prompt": "A client sends a JSON request body. Which request header declares the media type of that body?",
        "options": {"a": "Content-Type: application/json", "b": "Accept: application/json", "c": "Location: application/json", "d": "Authorization: application/json"},
        "correct_option_id": "a",
        "explanation": "Content-Type describes the representation being sent. Accept states preferences for response media types.",
    },
    {
        "id": "rest-representations-2", "topic": "representations",
        "prompt": "A JSON-only API returns HTTP 204 No Content after a successful deletion. How should the client handle the response body?",
        "options": {"a": "Require a JSON object with deleted=true", "b": "Parse an empty body as JSON null", "c": "Treat the request as successful without parsing a JSON body", "d": "Retry until a body appears"},
        "correct_option_id": "c",
        "explanation": "A 204 response has no content. Success does not require a JSON body, and parsing an empty body as JSON would fail.",
    },
]

BANKS = {
    "sql": {"metadata": sql_assessment.ASSESSMENT, "questions": sql_assessment.QUESTIONS},
    "python": {"metadata": metadata("python", "Python foundations diagnostic", "python-foundations-v1"), "questions": PYTHON_QUESTIONS},
    "rest_api": {"metadata": metadata("rest_api", "REST API HTTP foundations diagnostic", "rest-http-foundations-v1"), "questions": REST_QUESTIONS},
}


def new_snapshot(skill_key):
    return deepcopy(BANKS[skill_key])


def public_description(skill_key):
    bank = BANKS[skill_key]
    return {
        **deepcopy(bank["metadata"]), "label": BY_KEY[skill_key]["label"],
        "question_count": len(bank["questions"]),
        "topics": list(dict.fromkeys(question["topic"] for question in bank["questions"])),
        "claim_aliases": [BY_KEY[skill_key]["label"], *BY_KEY[skill_key]["aliases"]],
    }
