# Diagnostic content review form

Prepared 29 September 2026 from the question snapshots in application commit `272efb0`.
**All decisions below are pending. No human review has been completed by this form.**

Copy this form into `data/research/study-v1/` before entering reviewer details.
This answer-key packet is for content reviewers; do not show it to study participants.
It is not a saved-review JSON file and cannot be imported into the annotation page.

## Reviewer record

- Reviewer ID / relevant expertise: ____
- Review date: ____
- Developer or question-author conflict/exposure: ____
- Resources and practical tasks reviewed separately: pending

For each item, check answer correctness, unique best answer under stated assumptions,
wording/ambiguity, topic relevance, plausible distractors and accessibility.
Review both items per topic for duplication and breadth. Check resource relevance
using [MULTISKILL_ASSESSMENTS.md](../MULTISKILL_ASSESSMENTS.md).

Decisions: accept / revise / reject. Sign-off checks content; it does not validate
proficiency measurement. Later item/rubric changes require a new bank version.
Retain the old snapshots and freeze the reviewed bank before participant sessions.

## SQL foundations diagnostic

Bank: `sql-foundations-v1` · Review status: `draft_pending_human_review`

### sql-filter-1

Topic: `filtering`

```text
Which clause filters individual rows before grouping?
```

- **A** — HAVING
- **B** — WHERE
- **C** — ORDER BY
- **D** — GROUP BY

**Proposed key:** B

**Proposed explanation:** WHERE filters input rows; HAVING filters groups after grouping.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### sql-filter-2

Topic: `filtering`

```text
Which condition selects rows whose email column is SQL NULL?
```

- **A** — email = NULL
- **B** — email = ''
- **C** — email IS NULL
- **D** — email = 'NULL'

**Proposed key:** C

**Proposed explanation:** IS NULL tests for a missing SQL value. NULL is not an empty string.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### sql-join-1

Topic: `joins`

```text
customers has exactly two rows with id 1 and 2. orders has exactly two rows, both with customer_id 1. How many rows does this return? SELECT c.id FROM customers c INNER JOIN orders o ON o.customer_id = c.id;
```

- **A** — 1
- **B** — 3
- **C** — 4
- **D** — 2

**Proposed key:** D

**Proposed explanation:** Customer 1 produces one row per matching order; customer 2 has no match.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### sql-join-2

Topic: `joins`

```text
customers has exactly two rows with id 1 and 2. orders has exactly two rows, both with customer_id 1. How many rows does this return? SELECT c.id FROM customers c LEFT JOIN orders o ON o.customer_id = c.id;
```

- **A** — 3
- **B** — 2
- **C** — 1
- **D** — 4

**Proposed key:** A

**Proposed explanation:** Two rows match customer 1. LEFT JOIN also retains customer 2 as one row.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### sql-aggregate-1

Topic: `aggregation`

```text
Complete the query so it returns only customers with at least two orders: SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id ...;
```

- **A** — WHERE COUNT(*) >= 2
- **B** — HAVING COUNT(*) >= 2
- **C** — ORDER BY COUNT(*) >= 2
- **D** — LIMIT 2

**Proposed key:** B

**Proposed explanation:** HAVING applies a condition to each group and can use its aggregate count.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### sql-aggregate-2

Topic: `aggregation`

```text
A table contains exactly three rows with amount values 10, NULL and 20. What does SELECT COUNT(amount) FROM payments return?
```

- **A** — 3
- **B** — 30
- **C** — 2
- **D** — NULL

**Proposed key:** C

**Proposed explanation:** COUNT(amount) counts non-NULL values; COUNT(*) would count all three rows.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

## Python foundations diagnostic

Bank: `python-foundations-v1` · Review status: `draft_pending_human_review`

### python-functions-1

Topic: `functions`

```text
A Python function reaches its end without executing a return statement. What value does the call return?
```

- **A** — 0
- **B** — None
- **C** — An empty string
- **D** — The last local variable

**Proposed key:** B

**Proposed explanation:** Falling off the end of a Python function returns None. Printing a value does not return it.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### python-functions-2

Topic: `functions`

```text
What does this Python code print?
def total(price, quantity=2):
    return price * quantity
print(total(4, quantity=3))
```

- **A** — 12
- **B** — 8
- **C** — 7
- **D** — It raises TypeError

**Proposed key:** A

**Proposed explanation:** The explicit quantity=3 overrides the default of 2; 4 multiplied by 3 is 12.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### python-collections-1

Topic: `collections`

```text
What does this Python code print?
values = [3, 5]
alias = values
alias.append(8)
print(len(values))
```

- **A** — 2
- **B** — 8
- **C** — 1
- **D** — 3

**Proposed key:** D

**Proposed explanation:** Assignment makes alias refer to the same list. Appending through alias changes that list.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### python-collections-2

Topic: `collections`

```text
What does this Python code print?
counts = {'ready': 2}
print(counts.get('waiting', 0))
```

- **A** — 2
- **B** — None
- **C** — 0
- **D** — It raises KeyError

**Proposed key:** C

**Proposed explanation:** dict.get returns the supplied default when the key is absent, without adding the key.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### python-exceptions-1

Topic: `exceptions`

```text
Which exception does int('pear') raise in Python?
```

- **A** — KeyError
- **B** — ValueError
- **C** — IndexError
- **D** — It returns 0

**Proposed key:** B

**Proposed explanation:** The string has the right input type for int but does not represent an integer, so conversion raises ValueError.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### python-exceptions-2

Topic: `exceptions`

```text
In normal Python execution, which block is used for cleanup whether the associated try block succeeds or raises an exception?
```

- **A** — else only
- **B** — except ValueError only
- **C** — A new unrelated try block
- **D** — finally

**Proposed key:** D

**Proposed explanation:** A finally block runs as control leaves the try statement, including normal completion and exception propagation.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

## REST API HTTP foundations diagnostic

Bank: `rest-http-foundations-v1` · Review status: `draft_pending_human_review`

### rest-methods-1

Topic: `http_methods`

```text
An HTTP API provides /books/42. Which method is intended to retrieve the book representation without requesting a state change?
```

- **A** — GET
- **B** — POST
- **C** — DELETE
- **D** — PATCH

**Proposed key:** A

**Proposed explanation:** GET requests a representation and is defined as safe; incidental effects such as server logging can still occur.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### rest-methods-2

Topic: `http_methods`

```text
For an HTTP API that follows standard method semantics, what does it mean that PUT is idempotent?
```

- **A** — PUT cannot change server state
- **B** — Every response must be identical
- **C** — Repeating the identical request has the same intended server effect as sending it once
- **D** — PUT never needs authentication

**Proposed key:** C

**Proposed explanation:** Idempotence concerns the intended effect on the server, not identical response codes, logs or authentication requirements.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### rest-status-1

Topic: `status_codes`

```text
A POST request successfully creates a new resource. Which HTTP status specifically communicates that creation?
```

- **A** — 404
- **B** — 201
- **C** — 204
- **D** — 500

**Proposed key:** B

**Proposed explanation:** 201 Created reports successful creation. 204 means success without response content, not specifically creation.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### rest-status-2

Topic: `status_codes`

```text
An API documents that authenticated callers receive 404 when a requested item does not exist. Which response should GET /items/999 return when that item is absent?
```

- **A** — 500
- **B** — 201
- **C** — 301
- **D** — 404

**Proposed key:** D

**Proposed explanation:** Under the stated contract, 404 reports that the requested item was not found; its absence alone is not an internal server failure.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### rest-representations-1

Topic: `representations`

```text
A client sends a JSON request body. Which request header declares the media type of that body?
```

- **A** — Content-Type: application/json
- **B** — Accept: application/json
- **C** — Location: application/json
- **D** — Authorization: application/json

**Proposed key:** A

**Proposed explanation:** Content-Type describes the representation being sent. Accept states preferences for response media types.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

### rest-representations-2

Topic: `representations`

```text
A JSON-only API returns HTTP 204 No Content after a successful deletion. How should the client handle the response body?
```

- **A** — Require a JSON object with deleted=true
- **B** — Parse an empty body as JSON null
- **C** — Treat the request as successful without parsing a JSON body
- **D** — Retry until a body appears

**Proposed key:** C

**Proposed explanation:** A 204 response has no content. Success does not require a JSON body, and parsing an empty body as JSON would fail.

| Check | Human response |
| --- | --- |
| Key correct; independently checked against reference | pending |
| One best answer; assumptions/wording clear | pending |
| Topic coverage and distractor quality | pending |
| Accept / revise / reject | pending |
| Correction, reference and reviewer rationale | |

## Bank-level decision

| Skill | Coverage adequate for the stated limited diagnostic? | Resources/tasks checked? | Decision / reviewer / date |
| --- | --- | --- | --- |
| SQL | pending | pending | pending |
| Python | pending | pending | pending |
| REST/HTTP | pending | pending | pending |

No statement of calibrated proficiency, learning gains or job readiness follows
from this review. Preserve unresolved issues in the study limitations.
