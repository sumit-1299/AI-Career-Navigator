# Research batch: what to do now

Prepared 29 September 2026; delivery checklist updated 30 September 2026,
against application commit `272efb0`.
This batch adds research documents and blank forms. It does not change the running
application, collect participant data or produce research results.

## Read this first

The original feature combination overlaps existing work. Our proposed contribution
is a reproducible evaluation of assessment evidence and missing-answer handling in
job-linked learning guidance. Novelty and improved effectiveness remain unproven.

| File | Use |
| --- | --- |
| [RESEARCH_POSITIONING.md](RESEARCH_POSITIONING.md) | Problem, proposed contribution, exact implementation scope and wording for the expert |
| [LITERATURE_MATRIX.md](LITERATURE_MATRIX.md) | Eight primary works, overlaps, reading limits and source links |
| [PILOT_PROTOCOL.md](PILOT_PROTOCOL.md) | Two separate experiments, fixed comparators, reference labels and analysis rules |
| [CONTENT_REVIEW_FORM.md](CONTENT_REVIEW_FORM.md) | All 18 questions with keys/explanations and blank human review fields |
| [PILOT_FORMS.md](PILOT_FORMS.md) | Task review, session, independent reference, reconciliation and results forms |
| [references.bib](references.bib) | Eight bibliography records, with metadata discrepancies flagged |
| [study_register.template.json](../../research/protocol/study_register.template.json) | Record the actual freeze, people, exposure, versions and deviations privately |

## Three actions today — 30 September

1. **Prajwal:** commit this batch and read the positioning document. Record the
   actual study choices and code version in a private copy of the register.
2. **Content reviewer:** check the 18 items, answer keys and mapped resources. Review
   a fresh practical exercise/rubric for each skill used in the candidate pilot.
3. **Two independent reviewers:** prepare to label the frozen job packet and judge
   practical responses independently. Record relevant expertise and any prior
   exposure. Recruit available volunteers only under the team's research process.

These are proposed roles, not assignments already accepted by team members.
No invitations or messages have been sent. If reviewers or participants are not
available, prepare the protocol and demonstration for Saturday and state that
independent validation is pending. AI-generated reviews cannot replace it.

## Where filled records go

From the repository root, create the private working folder and copy templates:

```powershell
New-Item -ItemType Directory -Force .\data\research\study-v1 | Out-Null
Copy-Item .\research\protocol\study_register.template.json .\data\research\study-v1\study-register.json
Copy-Item .\docs\research\CONTENT_REVIEW_FORM.md .\data\research\study-v1\content-review.md
Copy-Item .\docs\research\PILOT_FORMS.md .\data\research\study-v1\pilot-forms.md
```

Run those copy commands once: re-running them can overwrite filled copies. Keep
separate copies for independent raters. The existing ignore rule excludes
`data/research/` from normal commits. Do not force-add it.

The Markdown forms and study-register JSON are **not app uploads** and are **not
saved-review files for the annotation page**. They are documentation/recordkeeping.
Use only the existing exporter and review-page formats in that page.

## Sequence to Saturday 3 October

- **30 September:** install this batch; settle scope and roles, complete feasible
  content/source checks, freeze actual study inputs and begin independent work
  only after the required reviews. Draft the report methods in parallel.
- **1 October:** finish feasible collection and descriptive analysis; record what
  remains incomplete. Keep negative/tied outcomes and exclusions.
- **2 October:** finish the report/paper draft/slides and rehearse a stable demo.
  Methods can be drafted earlier while data collection proceeds; results remain
  explicitly pending until measured.
- **3 October:** present working functionality, available evidence and limits.

The next writing batch can turn these materials into the formal report and paper
draft without waiting for results. It must retain “pending” wherever observations
have not been collected.
