"""Python and HTTP learning catalogues, checked 2026-09-29.

Tasks are original, ungraded project exercises. Links are curated, not generated
or ranked by a trained recommendation model. Do not edit released versions.
"""


def resource(title, provider, url, focus, kind="reference"):
    return {"title": title, "provider": provider, "url": url, "kind": kind,
            "focus": focus, "checked_on": "2026-09-29"}


def python_lesson(week, title, focus):
    return resource(title, "Harvard CS50", f"https://cs50.harvard.edu/python/weeks/{week}/",
                    focus, "course_lesson")


def task(title, starter, instructions, self_check, language="Python"):
    return {"title": title, "starter_code": starter, "language": language,
            "instructions": instructions, "self_check": self_check,
            "starter_guidance": "Use the starter in your own editor. Keep your solution and explanation for review."}


PYTHON = {
    "functions": {
        "title": "Return values and use function parameters",
        "objective": "Distinguish returning from printing and use default and keyword arguments.",
        "resources": [
            python_lesson(0, "CS50 Python: Functions, Variables", "Review parameters, return values and the difference between return and print."),
            resource("Defining functions", "Python 3.13 documentation",
                     "https://docs.python.org/3.13/tutorial/controlflow.html#defining-functions",
                     "Review function definitions, default arguments and keyword arguments."),
        ],
        "task": task("Calculate an invoice total", "def invoice_total(unit_price, quantity=1):\n    # Return the total, without printing it.\n    pass",
                     ["Implement invoice_total using its two arguments.",
                      "Check invoice_total(7) and invoice_total(7, quantity=4).",
                      "Explain why printing the total inside the function is different from returning it."],
                     "The returned values should be 7 and 28. A print-only implementation would return None."),
    },
    "collections": {
        "title": "Reason about lists and dictionary lookups",
        "objective": "Trace shared list references and choose a default for a missing dictionary key.",
        "resources": [
            python_lesson(2, "CS50 Python: Loops", "Use the list and dictionary sections, then practise iterating over stored values."),
            resource("Data structures", "Python 3.13 documentation",
                     "https://docs.python.org/3.13/tutorial/datastructures.html",
                     "Review list operations and dictionary access."),
        ],
        "task": task("Update a copy and count a missing category", "original = [2, 4]\ncopy = original.copy()\ncopy.append(6)\ncounts = {'open': 3}\n# Inspect both lists and look up 'closed' with a default of zero.",
                     ["Print original and copy after the append.",
                      "Retrieve counts['closed'] safely with dict.get and a default of zero.",
                      "Repeat with copy = original and explain which list changes."],
                     "With .copy(), original is [2, 4] and copy is [2, 4, 6]. The missing category returns 0. With assignment alone both names refer to the changed list."),
    },
    "exceptions": {
        "title": "Handle a specific conversion error",
        "objective": "Catch expected ValueError failures and explain cleanup in finally.",
        "resources": [
            python_lesson(3, "CS50 Python: Exceptions", "Review try, except and handling invalid integer input."),
            resource("Errors and exceptions", "Python 3.13 documentation",
                     "https://docs.python.org/3.13/tutorial/errors.html",
                     "Review exception handling and the cleanup role of finally."),
        ],
        "task": task("Convert a submitted quantity", "def parse_quantity(text):\n    # Return int(text), or None when conversion raises ValueError.\n    pass",
                     ["Implement the function using try and except ValueError.",
                      "Try inputs '12' and 'pear'. Do not use a bare except.",
                      "Temporarily add a finally block that prints 'finished' and explain when it runs."],
                     "The return values are 12 and None. The finally message appears for both paths during normal execution."),
    },
}

HTTP_OVERVIEW = resource(
    "Client-server overview", "MDN Learn web development",
    "https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/First_steps/Client-Server_overview",
    "Follow the request and response examples in this guided lesson.", "guided_lesson",
)
API_LESSON = resource(
    "CS50 Web: JavaScript — APIs section", "Harvard CS50",
    "https://cs50.harvard.edu/web/notes/5/#apis",
    "Study API requests and JSON responses. JavaScript familiarity helps; this is not a complete REST design course.", "course_lesson",
)
REST = {
    "http_methods": {
        "title": "Choose HTTP methods and reason about retries",
        "objective": "Separate read requests from updates and explain the intended effect of repeated PUT requests.",
        "resources": [HTTP_OVERVIEW, resource(
            "HTTP request methods", "MDN",
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods",
            "Compare safe and idempotent methods. Responses to repeated requests need not be identical.",
        )],
        "task": task("Specify a book resource", "Resource: /books/42\nCurrent representation: {\"title\": \"First edition\"}",
                     ["Write the method and path for reading the current representation.",
                      "Specify a PUT request replacing it with a title of 'Second edition'.",
                      "Explain the intended final state if that identical PUT request is sent twice."],
                     "Read with GET /books/42. Under a replacement contract, PUT with the new representation leaves the title as 'Second edition' after one or two identical requests. This does not promise identical responses.", "HTTP design notes"),
    },
    "status_codes": {
        "title": "Describe success, missing resources and empty responses",
        "objective": "Use status codes to communicate outcomes rather than treating every response as JSON data.",
        "resources": [HTTP_OVERVIEW, resource(
            "HTTP response status codes", "MDN",
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status",
            "Read the definitions of 201, 204 and 404, including the absence of content in 204.",
        )],
        "task": task("Document three API outcomes", "POST /notes -> a new note is created\nGET /notes/999 -> the note does not exist\nDELETE /notes/42 -> deletion succeeds with no content",
                     ["For this exercise, document 201 for creation, 404 for a missing note and 204 for deletion without content.",
                      "Give an example JSON response for the new note and identify its resource URL.",
                      "Explain why the deletion response must not require a JSON body."],
                     "The stated contract yields 201, 404 and 204 respectively. A created note could have {\"id\": 43}; a Location header can identify /notes/43. A 204 response has no content.", "HTTP design notes"),
    },
    "representations": {
        "title": "Handle JSON representations and their headers",
        "objective": "Distinguish Content-Type from Accept and handle a successful response without content.",
        "resources": [API_LESSON, resource(
            "Overview of HTTP", "MDN",
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview",
            "Review the structure of requests, responses, headers and bodies.",
        )],
        "task": task("Write a JSON request and an empty-response rule", "POST /notes\n# Add request headers and a JSON body.\n\n# Describe client handling for a successful 204 response.",
                     ["Declare a JSON request body using Content-Type and request a JSON response using Accept.",
                      "Write a valid JSON object for a note with title 'Plan'.",
                      "Describe a client rule that handles 204 before attempting JSON parsing."],
                     "Use Content-Type: application/json and Accept: application/json with {\"title\": \"Plan\"}. For 204, record success without parsing a body; parse JSON only when the response contract and content support it.", "HTTP design notes"),
    },
}

CATALOGS = {
    "python": {"catalog": PYTHON, "version": "python-resources-2026-09-29-v1",
               "ordering": "Functions, collections, then exceptions; topics with no flagged need are omitted."},
    "rest_api": {"catalog": REST, "version": "rest-http-resources-2026-09-29-v1",
                 "ordering": "HTTP methods, status codes, then representations; topics with no flagged need are omitted."},
}
