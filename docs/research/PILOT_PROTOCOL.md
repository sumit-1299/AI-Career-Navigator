# Pilot protocol — extraction and learning-action evaluation

Version: **career-pilot-protocol-v1**. Written 29 September 2026.
Status: **proposed; no new observations collected by this document**.
Code baseline inspected: `272efb0`. Freeze the actual code commit and protocol
before collecting outcomes; use [study_register.template.json](../../research/protocol/study_register.template.json).
This is an internally prespecified exploratory pilot, not a registered trial or
proof of effectiveness. Record deviations with dates and reasons.

## 1. Scope and feasibility

RQ1 evaluates ten job-skill concepts. RQ2 evaluates topic-level next actions for
SQL, Python and REST/HTTP. Keep their cases, labels and results separate.

Suggested feasibility targets, not statistically justified sample sizes:

- RQ1: one frozen packet of 24 jobs, with the tool's 12 development / 12 test split;
  two independent reviewers and adjudication if needed.
- RQ2: six adult volunteers, preferably two per supported skill, one target skill
  and its three topics per person. Two qualified raters review the task evidence.
  More participants may be added only under a revised plan fixed before outcomes.
- Complete the feasible observations by 1 October; prepare the review on 2 October.
  If fewer cases are available, report the actual count and missing work. Do not
  call this sample representative of students, employers or the labour market.

A person must not act as two independent raters. Developer ratings must be labelled
internal if independent review is unavailable. Team members used as participants
must be identified as developers/exposed participants in the study record and
reported separately; familiarity with the question bank is a major limitation.

## 2. Freeze and record before scoring

Record the protocol version, Git commit, dirty-file status, model identifier and
revision, catalogue/question-bank versions, inclusion rule, intended sample size,
reviewer IDs/qualifications, outcome definitions and exclusions. Keep real names
and consent notes separately from public project files.

All raw study records belong under the existing ignored `data/research/` folder.
Keep blanks/templates and protocol in Git. Ignoring files is not encryption or an
access-control system; avoid adding private study records to public commits.
Use participant IDs such as P01. Collect only the information needed for the pilot.
Participants should understand the prototype and voluntary nature of participation;
results are not employment or academic grades. Follow the institution's applicable
research process before recruitment. This document does not recruit anyone.

Do not fill unknown values with zero, fabricate participants, reuse AI-draft labels
as two human reviews, or change a failed/uncertain case merely to improve results.

## 3. RQ1 — job-skill extraction

### 3.1 Inputs and comparison

Use the existing keyword/alias method and keyword-plus-MiniLM method with identical
frozen job descriptions, vocabulary, context rules and empty candidate context.
Record cosine threshold 0.58, margin 0.08 and the actual pinned model revision.
This compares the incremental semantic suggestions; it is not semantic-only
matching and does not evaluate a candidate's proficiency or job suitability.

The earlier `pilot-v1.json` and AI draft are development material. If humans review
that same packet now, report a retrospectively human-reviewed development pilot.
Do not relabel it as a clean prospective test merely because the file contains a
`test` split. The earlier development-fit diagnostic is not an independent result.

For a fresh packet, a coordinator who has not examined new predictions should
freeze selection and audit overlap with all previously seen postings. A new
filename, new seed or newer retrieval timestamp alone does not ensure new text.
Check provider IDs, normalized text, employer/title groups and near-duplicate
content. Document any overlap and its handling before evaluation. The current
exporter groups within a packet; it does not automatically exclude old pilot jobs.
If fresh independent cases cannot be obtained in time, retain the original pilot
and state its exposure limitation rather than inventing a holdout.

### 3.2 Practical commands

Use the existing documented exporter/review UI. An example for a deliberately new
candidate packet, after refreshing the selected job boards:

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\research_evaluation.py export --size 24 --seed career-review-2026-09-30-v1 --out .\data\research\pilot-v2.json
```

Audit this candidate packet before assigning reviewers. Do not hand-edit sealed
text, labels or splits. If the selection rule needs changing, make a documented
exporter change before freezing a replacement packet, or label this pilot exposed.

R1 and R2 open the same packet in `research/review.html`, independently label all
ten concepts per case as present/absent/uncertain, cite job passages and record
ambiguities. They must not use the model output, the earlier AI draft or each
other's labels. If they already saw those materials, disclose that and use other
reviewers where possible. Save original review JSON files separately.

With actual completed review files:

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\research_evaluation.py prepare-adjudication --dataset .\data\research\pilot-v2.json --review-a .\data\research\review-R1.json --review-b .\data\research\review-R2.json --out .\data\research\adjudication-v2.json
```

If there are disagreements, a third reviewer opens the generated adjudication
packet in the review page and saves a completed review, for example
`adjudicated-R3.json`. The packet itself is not a completed review.

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\research_evaluation.py evaluate --dataset .\data\research\pilot-v2.json --review-a .\data\research\review-R1.json --review-b .\data\research\review-R2.json --adjudication .\data\research\adjudicated-R3.json --split test --out .\data\research\human-pilot-v2-test
```

Omit `--adjudication` and its path when R1/R2 have no disagreements. Output folders
must be new. The command's `test` choice is a technical split, not a certificate of
independence. Record actual exposure in the study register and written report.
See [the existing evaluator guide](../RESEARCH_EVALUATION.md) for schema details.

### 3.3 Outcomes

Primary: paired difference in micro-F1, hybrid minus keyword, on resolved cells.
Also report precision, recall, per-skill support/F1, fraction of resolved cells,
manual-review coverage and error examples. Treat both methods' uncertain labels
with the same exclusion mask. Never silently treat uncertain as absent.

Report the tool's pre-adjudication agreement and kappa, noting domination by absent
labels when present. Its paired job-level bootstrap interval is descriptive for
a small convenience sample; employer/template clustering remains a limitation.
The target is 12 test jobs, not 120 independent observations. Do not select a best
seed/run after seeing its result. If methods tie, report the tie.

## 4. RQ2 — appropriateness of the learning action

### 4.1 Unit, inputs and independent reference

One case is one participant, one frozen target job, one supported skill and one
of that skill's diagnostic topics. Three topic cases for a person remain a single
participant cluster in analysis. Six participants can provide up to 18 topic cases;
this is not a sample of 18 independent people.

Choose a job whose relevant skill is confirmed by a human reading the frozen text.
Hold that confirmed requirement constant across conditions. The three foundation
topics are the diagnostic's scope, not a claim that the job demands each exact
quiz concept. Do not change the extraction method between recommendation arms.

Before collecting outcomes, a qualified person creates and checks a fresh practical
exercise with three independently scorable parts for the chosen skill. It must
require application/explanation beyond the published six-question quiz and roadmap
practice examples. The exercise, rubric and acceptable solutions are frozen,
versioned and retained privately; reviewers record errors or ambiguities. This
batch provides forms, not a validated exercise bank. Study collection must wait
until this content review is complete, or be reported only as a protocol demonstration.

A suitable structure is a small SQL querying exercise, a Python function with
collections/error handling, or an HTTP request/response design task. Include all
necessary data and environment assumptions. If a task cannot measure one topic,
mark that topic's reference insufficient instead of inventing an outcome.

### 4.2 Session order (approximately 20–30 minutes)

1. Record voluntary participation, exposure to the project and selected skill/job.
2. Record the candidate's optional 1–10 self-rating **before** tests or feedback.
3. Complete the fresh practical exercise first, saving the original response. Use
   a fixed assistance rule: no external assistance, including generative AI, during
   this brief evaluation; document accidental assistance or task interruptions.
   Skipping is allowed. Do not pressure participants into answers.
4. Complete one first-exposure app diagnostic for that skill. Save its attempt ID,
   version and exact result. Do not substitute the best of repeated attempts.
5. Have raters independently judge the fresh task response without seeing the
   self-rating, quiz score, policy outputs or each other's ratings. Retain both
   original reviews and reconcile disagreement before unmasking method outcomes.
6. Generate the three condition outputs using the frozen definitions below. Preserve
   the original candidate record; hypothetical comparator outputs are separate study
   records, never changes to the candidate's assessment or live app guidance.
7. Optional: show uniformly formatted, masked condition cards in a prespecified
   rotating order and collect usefulness comments. These are usability opinions,
   not independent evidence that the recommendation is correct.

Freeze and document timing, tools allowed and any accommodations. Failed application
requests are technical missing data; retain them in the flow log rather than
scoring the candidate as incorrect.

### 4.3 Three fixed conditions

These are deliberately simple, researcher-defined controls. They are not replicas
of R1–R8 and cannot support a claim of superiority over state-of-the-art systems.
Use the same action vocabulary, resources and presentation layout across conditions.

| Condition | Information used | Rule for each topic |
| --- | --- | --- |
| B0 — self-report-only control | Pre-test rating for the selected skill | Rating 1–5 → `practice`; 6–10 → `no_targeted_practice`; no rating → `collect_evidence`. Apply the skill-wide rating to each topic and disclose this coarse baseline. The cutoff is a prespecified convenience, not a validated proficiency threshold. |
| B1 — assessment with skips counted as errors | The same quiz responses as B2 | If wrong plus unanswered count is above zero → `practice`; otherwise → `no_targeted_practice`. An entirely absent submitted assessment → `collect_evidence`. This is an experimental ablation, not the deployed app policy. |
| B2 — current evidence policy | The same quiz responses as B1 | Any wrong answer → `practice`; otherwise any unanswered item → `collect_evidence`; all correct/complete → `no_targeted_practice`. No submitted attempt → `collect_evidence`. Preserve the count of skips when practice is suggested. |

`no_targeted_practice` means this limited observation does not prescribe remediation;
it never means “proficient” or “job-ready”. `collect_evidence` means a fresh task or
review is needed, not that a course must be taken. Projects and certificates are
held constant as unverified context. This study does not test a fusion model.

For this small pilot the coordinator may fill condition rows manually from the
exact rules and saved app result, with a second person checking them. Record rule
versions and row checks in the form. B0/B1 are not new application features. RQ1's
`evaluate` command cannot process these recommendation forms.

### 4.4 Independent reference labels and outcome rubric

For each practical-task topic, raters select one label and quote the observable
response supporting it:

- `practice_supported`: an identified conceptual/procedural error supports targeted
  practice on the sampled topic.
- `no_targeted_practice_supported`: the response satisfies the frozen practical-task
  criteria for this topic. It does not establish complete skill mastery.
- `insufficient_reference`: skipped/incomplete/ambiguous work or a flawed task prevents
  a defensible topic judgement. Record whether the cause is candidate nonresponse,
  task design, rater disagreement or a technical failure.

Do not derive these labels from the MCQ answer key, our recommendation rule or an
AI answer. Two human raters may still be wrong; report expertise and agreement.
Use [PILOT_FORMS.md](PILOT_FORMS.md) for independent records and adjudication.

Prespecified decision utility (0–2), an operational study rubric rather than a
validated educational scale:

| Independent practical-task reference | `practice` | `collect_evidence` | `no_targeted_practice` |
| --- | ---: | ---: | ---: |
| `practice_supported` | 2 | 1 | 0 |
| `no_targeted_practice_supported` | 0 | 1 | 2 |
| `insufficient_reference` | 0 | 2 | 0 |

This rewards a justified decisive action over indefinite evidence collection when
reference evidence is adequate. It also allows B2 to lose: if the quiz topic is
skipped but the practical task shows errors, B1 can receive 2 while B2 receives 1.
The rubric and baseline cutoff must be accepted/frozen before outcomes are viewed;
if changed later, record an exploratory amendment and report both analyses.

### 4.5 Analysis, denominators and decision rules

**Primary contrast:** for each participant, average B2 minus B0 utility across
eligible topics with resolved practical references (`practice_supported` or
`no_targeted_practice_supported`). Report the mean/median of these participant
contrasts, individual values and number of participants/topics retained. Exclude
participants with no resolved topic from this primary mean, report how many and why.
This avoids obtaining a favourable primary result solely by rewarding abstention
on tasks our reviewers could not evaluate.

**Secondary contrast:** B2 minus B1 utility with the same resolved-topic rule;
report separately on topics with skips and without skips. If there are no skips,
B1/B2 cannot identify the effect of skip handling. State that limitation; do not
ask participants to fabricate skips or manufacture a positive finding.

Also report, per condition, raw numerators/denominators for:

- Practice recommendations on reference-adequate topics / all reference-adequate
  topics (unnecessary practice relative to the sampled task).
- `no_targeted_practice` on reference-error topics / all reference-error topics
  (missed practice relative to the sampled task).
- `collect_evidence` / all evaluable topic cases (deferral rate), and its breakdown
  by resolved/insufficient reference.
- Appropriate deferrals on `insufficient_reference`, with each reason category shown.
- Rater agreement before reconciliation; missing records and technical failures.

A zero denominator is **N/A**, not zero. Report insufficient-reference utility as a
separate sensitivity table using the rubric; never mix it into the primary contrast
without also reporting the resolved-only result. Equal-weight participants, not
quiz items or duplicated topic cards, for the main summary. Missing condition data
are paired exclusions with recorded reasons, not imputed successes.

For this feasibility pilot, use descriptive results and case analysis. Do not report
population-level significance, statistical power or learning gains. Optional
usefulness ratings (1–5) and presentation time are secondary usability observations.
Show ties, negative differences and counterexamples as explicitly as improvements.

## 5. Content review, reproducibility and threats

Review all 18 diagnostic items and mapped resources using
[CONTENT_REVIEW_FORM.md](CONTENT_REVIEW_FORM.md). A human sign-off means checked
content, not validated proficiency measurement. If a published question or answer
changes, create a new bank version and freeze it before participant collection.
Do not rewrite snapshots or pool different bank versions without reporting them.

Retain exact job text, provenance, IDs, anonymised practical responses, first-attempt
results, independent ratings, reconciliations, condition actions and rule version.
Do not publish identifiable participant data or third-party content without the
necessary permission. Public reporting can use aggregate results and permitted
short examples; retain full audit material privately.

Main threats: a tiny convenience sample, developer/participant exposure, two items
per topic, hand-written narrow controls, uncertain practical-task validity, rater
bias, assistance/guessing, clustered employers, limited language/role coverage,
fixed questions and missing responses that are not random. Snapshot traceability
improves auditability but does not remove these threats.

## 6. What can be presented on 3 October

| Evidence available | Defensible presentation |
| --- | --- |
| Working software only | Demonstration and proposed protocol; results pending |
| AI diagnostic only | Development error analysis, clearly labelled AI-assisted |
| Exposed packet plus real independent labels | Retrospective, limited extraction evaluation with exposure disclosure |
| Fresh reviewed job sample | Small frozen extraction pilot within the stated vocabulary/sampling scope |
| Independently reviewed practical-task cases | Exploratory recommendation-policy comparison with sample, missingness and trade-offs |

Report each study's actual status. Never replace missing human data with simulated
participants or synthetic labels and then call the output a real study.
