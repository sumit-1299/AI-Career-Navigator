# Research batch: what to do now

Prepared 29 September 2026; delivery checklist updated 5 October 2026.
Original research baseline: `272efb0`; research documents: `c9d104a`.
The resume/UI update extends that baseline; record its actual commit for any study.
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

## Three actions today — 5 October

1. **Prajwal:** commit this batch and read the positioning document. Record the
   actual study choices and code version in a private copy of the register.
2. **Content reviewer:** check the 18 items, answer keys and mapped resources. Review
   a fresh practical exercise/rubric for each skill used in the candidate pilot.
3. **Two independent reviewers:** prepare to label the frozen job packet and judge
   practical responses independently. Record relevant expertise and any prior
   exposure. Recruit available volunteers only under the team's research process.

These are proposed roles, not assignments already accepted by team members.
No invitations or messages have been sent. If reviewers or participants are not
available, prepare the protocol and demonstration for Thursday 8 October and state that
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

## Sequence to Thursday 8 October

- **5 October:** apply the resume/UI batch and verify the full local flow. Review
  the report and paper drafts; settle authorship and available human reviewers.
- **6 October:** finish feasible source/content checks and independent collection
  after freezing the study record. Analyse only observations actually obtained.
- **7 October:** freeze code, update results/status, prepare slides, rehearse the
  complete demo and record a backup. Keep a successfully refreshed job cache.
- **8 October:** submit the application, report, paper draft and required materials.

The report and paper can describe the implemented system now. Leave independent
results explicitly pending until collected. Resume mentions are new display
context, not a tested proficiency measure or a new outcome in the pilot.
