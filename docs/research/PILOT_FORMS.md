# Pilot record forms

Copy each relevant blank form into **`data/research/study-v1/`** before filling it.
The templates in this public repository must remain blank. Real participants,
ratings and consent records are not supplied by this batch.

These are study notes. **Do not upload them into the app or “Resume a saved review”.**
The job-annotation page accepts its own packet/review JSON format only. The RQ1
command-line evaluator does not analyse the RQ2 forms below.

## A. Practical-task content review — before sessions

| Field | Value to record |
| --- | --- |
| Task ID and version | |
| Skill and three topic IDs | |
| Author ID / relevant expertise | |
| Independent content checker ID / expertise | |
| Prompt, data and environment assumptions | Save exact versioned task separately |
| Criteria and acceptable solutions per topic | Save privately before sessions |
| Enough evidence for each topic? | pending |
| Distinct from the published MCQ and roadmap exercises? | pending |
| Ambiguities, acceptable alternate solutions and corrections | |
| Review decision / date | pending |
| Freeze hash and private file path | |

Do not use the diagnostic outcome as the practical-task rubric. If a question is
ambiguous, resolve it before data collection or classify the affected reference
as insufficient with a recorded task-design reason.

## B. Participant session record — one per person

| Field | Value to record |
| --- | --- |
| Participant ID | |
| Session date/time and timezone | |
| Voluntary participation recorded privately | pending |
| Developer/team member? Prior exposure to questions or system? | |
| Target skill / three topics | |
| Frozen job ID, source URL, text hash and snapshot path | |
| Reviewer-confirmed skill requirement and supporting passage | |
| Self-rating before tasks (integer 1–10 or missing) | |
| Fresh practical-task ID/version | |
| Original response path and hash | |
| Assistance, interruption, accommodation or technical issues | |
| App assessment attempt ID / bank version / scoring version | |
| Original assessment result snapshot path | |
| Prior/repeated attempt? | |
| Withdrawal or exclusion and reason, if any | |

Record practical work before the MCQ feedback is shown. Keep the full practical
response available to reference raters but withhold self-ratings and MCQ outputs.
Use one first-exposure attempt in the primary pilot; report exceptions separately.

## C. Independent practical-response reference — separate copy per rater

Reviewer ID: ____  Relevant expertise: ____  Date: ____
Case/participant ID: ____  Task ID/version: ____

Disclosure: I have / have not seen this person's self-rating, quiz score, policy
outputs or the other review. Describe any exposure: ____

| Topic | Observable work / rubric criterion | Label | Reason for insufficient reference, if applicable |
| --- | --- | --- | --- |
| Topic 1 | | pending | |
| Topic 2 | | pending | |
| Topic 3 | | pending | |

Allowed labels: `practice_supported`, `no_targeted_practice_supported`,
`insufficient_reference`. These refer to the sampled task only.

Do not choose a label because it agrees with the application or AI-generated
answers. Record the specific observable response and the frozen criterion.

## D. Reference reconciliation — preserve both originals

| Topic | Rater 1 label | Rater 2 label | Agreed? | Final reference | Resolver ID / rationale |
| --- | --- | --- | --- | --- | --- |
| Topic 1 | pending | pending | pending | pending | |
| Topic 2 | pending | pending | pending | pending | |
| Topic 3 | pending | pending | pending | pending | |

Resolve from the original practical response and frozen rubric before viewing
condition outcomes. If evidence remains unresolved, use `insufficient_reference`
and record `rater_disagreement`; do not force consensus to favour a method.
Calculate agreement on original labels, not on the reconciled copy.

## E. Condition actions and utility — coordinator plus a second checker

Participant ID: ____  Frozen reference record: ____  Rule version:
`career-pilot-protocol-v1`  Coordinator/checker IDs: ____ / ____

| Topic | Pre-test rating | MCQ correct / wrong / skipped | B0 action | B1 action | B2 action | Independent reference |
| --- | --- | --- | --- | --- | --- | --- |
| Topic 1 | | | pending | pending | pending | pending |
| Topic 2 | | | pending | pending | pending | pending |
| Topic 3 | | | pending | pending | pending | pending |

| Topic | B0 utility | B1 utility | B2 utility | Primary eligible? | Exclusion / mismatch note |
| --- | --- | --- | --- | --- | --- |
| Topic 1 | pending | pending | pending | pending | |
| Topic 2 | pending | pending | pending | pending | |
| Topic 3 | pending | pending | pending | pending | |

Apply the exact rules and 0–2 utility table in [PILOT_PROTOCOL.md](PILOT_PROTOCOL.md).
Primary eligibility requires paired condition data and a resolved practical
reference. Keep insufficient-reference outcomes for the separate sensitivity table.
The coordinator must retain the B2 app topic result and check that the action
matches it; a discrepancy is a software/study issue to record and resolve.

Participant-level mean B2−B0 over eligible topics: ____
Participant-level mean B2−B1 over eligible topics: ____
Eligible topic count: ____  Skipped-topic count: ____
If no topic is eligible, enter N/A with its reason.

## F. Optional usefulness feedback

Keep actual method identities in a coordinator-only mapping. Rotate presentation:
P01 B0/B1/B2, P02 B1/B2/B0, P03 B2/B0/B1, then repeat. Use neutral card labels
1/2/3, the same layout, similar explanation length and the same available links.
Record actual order. Names can be masked, but the content may reveal the condition;
do not call this fully blinded. Raters of practical responses should not do this
step before their independent references are frozen.

| Field | Value |
| --- | --- |
| Participant ID / actual display order | |
| Card 1 usefulness, 1–5 | pending |
| Card 2 usefulness, 1–5 | pending |
| Card 3 usefulness, 1–5 | pending |
| Meaning: 1 = unusable; 3 = partly helpful; 5 = clearly helps choose the next action | |
| Explanation was misleading or overstated skill? Quote the wording. | |
| What action would you take next, and why? | |
| Time to choose, if measured consistently | |

Do not turn satisfaction into a proficiency, correctness or learning-gain result.

## G. Results table skeleton — leave pending until measured

| Outcome | B0 | B1 | B2 | Denominator / exclusions |
| --- | --- | --- | --- | --- |
| Mean participant utility on resolved references | pending | pending | pending | |
| Practice on reference-adequate topics | pending | pending | pending | numerator / denominator |
| No practice on reference-error topics | pending | pending | pending | numerator / denominator |
| Evidence deferrals | pending | pending | pending | numerator / denominator |
| Appropriate deferrals on insufficient references | pending | pending | pending | separate from primary |
| Usefulness, if collected | pending | pending | pending | participants per condition |

| Paired contrast | Actual participants | Mean | Median | Individual participant differences |
| --- | --- | --- | --- | --- |
| B2−B0 utility, primary | pending | pending | pending | |
| B2−B1 utility, secondary | pending | pending | pending | |

Always report missingness, actual participant counts, original rater agreement,
exposure and deviations. Use N/A for zero denominators. Preserve negative and tied
results. A blank table is not evidence that the study succeeded or failed.
