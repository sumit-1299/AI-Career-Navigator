"""Interactive LOCAL demonstration using a newly created demonstration account.

Run with --demo while the Flask API is running at http://127.0.0.1:5000.
Creates demo data in the local database. It never prints passwords or tokens.
"""

import argparse
import json
import secrets
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


BASE_URL = "http://127.0.0.1:5000"


def api(method, path, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(BASE_URL + path, data=payload, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except HTTPError as exception:
        try:
            details = json.load(exception)
            message = details.get("message", details.get("msg", "Request failed"))
        except (ValueError, AttributeError):
            message = "The server returned an unexpected response."
        raise RuntimeError(f"HTTP {exception.code}: {message}") from None
    except URLError:
        raise RuntimeError("Cannot reach the local API. Start Flask at http://127.0.0.1:5000 first.") from None


def run_demo():
    print("Creating a LOCAL DEMO candidate with a self-reported SQL claim of 7/10.")
    print("These demonstration records must not be treated as research participant data.")
    print("The six-question bank is a draft awaiting human review.")
    account = {
        "name": "DEMO - SQL Assessment",
        "email": f"sql-demo-{uuid4().hex}@example.test",
        "password": secrets.token_urlsafe(24),
    }
    api("POST", "/api/register", account)
    token = api("POST", "/api/login", account)["access_token"]
    api("POST", "/api/skills", {"skill_name": "SQL", "proficiency": 7}, token)
    attempt = api("POST", "/api/assessments/sql/attempts", {}, token)["attempt"]
    print("Assessment:", attempt["assessment_version"])
    print("Enter an option letter, or press Enter to leave a question unassessed.")
    answers = []
    for index, question in enumerate(attempt["questions"], start=1):
        print(f"\n{index}. [{question['topic']}] {question['prompt']}")
        for option_id, text in question["options"].items():
            print(f"  {option_id}: {text}")
        while True:
            choice = input("Your answer (a/b/c/d, Enter to skip): ").strip().lower()
            if not choice or choice in question["options"]:
                break
            print("Choose one of the displayed letters, or press Enter to skip.")
        answers.append({"question_id": question["id"], "option_id": choice or None})

    # Refresh after the interactive section, which may outlast the token lifetime.
    token = api("POST", "/api/login", account)["access_token"]
    saved = api("POST", f"/api/assessments/attempts/{attempt['id']}/submit", {"answers": answers}, token)["attempt"]
    result = saved["result"]
    print(f"\nSaved attempt: {saved['id']}")
    print(f"Correct: {result['correct_count']} of {result['answered_count']} answered questions")
    print(f"Coverage: {result['answered_count']} of {result['question_count']} questions answered")
    print(f"Unassessed questions: {result['unanswered_count']}")
    for topic in result["topics"]:
        print(f"{topic['topic']}: {topic['correct_count']}/{topic['answered_count']} answered correctly; "
              f"evidence={topic['evidence_status']}; practice suggested={topic['practice_suggested']}")
    skills = api("GET", "/api/skills", token=token)["skills"]
    claim = next(skill for skill in skills if skill["skill_name"] == "SQL")
    print(f"Original self-reported SQL claim: {claim['proficiency']}/10")
    history = api("GET", "/api/assessments/sql/attempts", token=token)["attempts"]
    if not any(item["id"] == saved["id"] and item["status"] == "submitted" for item in history):
        raise RuntimeError("The submitted attempt was not returned in candidate history.")
    print("PASS: submitted result retrieved from candidate history.")
    print(saved["assessment"]["interpretation"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", required=True,
                        help="Create a local demo account, claim and assessment attempt.")
    parser.parse_args()
    try:
        run_demo()
    except (RuntimeError, TimeoutError, OSError, ValueError) as exception:
        print(f"STOPPED: {exception}")
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nDemo interrupted; any created records remain in the local database.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
