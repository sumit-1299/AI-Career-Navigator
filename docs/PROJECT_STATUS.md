# AI Career Navigator — implementation and research status

Updated 30 September 2026. This file distinguishes working functionality from
planned research claims. See [PROJECT_SCOPE.md](PROJECT_SCOPE.md) for the broader
product vision; not every part of that vision is implemented.

| Area | Current implementation | Remaining work / limits |
| --- | --- | --- |
| Local application | Flask, PostgreSQL, authentication and browser workspace | Deployment hardening and a hosted demo remain separate work |
| Skill assessments | SQL, Python and REST/HTTP six-question diagnostics, immutable attempts, accuracy/coverage and topic feedback | Draft content; independent review and proficiency validation pending; HTTP questions do not assess full REST design |
| Learning roadmap | Curated SQL/Python/HTTP resources and original tasks linked to topic evidence; job cards lead to assessments and new comparisons | Progress is self-reported; tasks are ungraded and learning effectiveness is unvalidated |
| Candidate evidence | Projects/certificates with skill tags, edits, version checks and archive/restore | Records remain unverified; no automatic credential verification |
| Job comparison | Keyword/alias baseline and keywords plus pretrained MiniLM suggestions; latest submitted SQL/Python/REST evidence per skill and context review | Rules and thresholds need independent validation; no overall hiring probability, suitability rank or proficiency score |
| Live jobs | Selected Canonical/Razorpay boards, cached freshness, filtering and versioned comparison snapshots | Limited employer coverage, manual refresh, no market-wide feed |
| Evaluation tools | Frozen job exporter, independent annotation page, adjudication, paired extraction metrics and a separate AI-draft development diagnostic | Human validation remains pending; agreement with an AI draft is preliminary and cannot establish accuracy |
| Research contribution | Evidence distinctions and source snapshots implemented; focused eight-work literature matrix and two-part pilot protocol drafted | Close prior-work overlap exists; novelty and recommendation benefit remain unproven; human source/content review and data collection pending |
| Training | Pretrained model used for inference | No project-specific supervised training or fine-tuning completed |

The next research task is documented in
[RESEARCH_EVALUATION.md](RESEARCH_EVALUATION.md). It measures job-skill extraction
first. A separate study is needed to test whether assessment/evidence context
improves skill-gap decisions. Synthetic smoke-test metrics are not research results.
The `diagnose` command can inspect development disagreements against an explicitly
AI-assisted draft while human validation is pending. It does not score test jobs,
train a model or satisfy the independent-review requirements of `evaluate`.
The [context correction](MATCHING_CONTEXT.md) resolves two observed development
disagreements against the AI draft. Both methods still produce identical skill
sets on that subset; these rule changes do not establish a semantic advantage.

## Earlier career knowledge base

The earlier team work includes career and career-skill database models, an initial
10-role / 50-mapping prototype, occupational-data processing scripts and reference
vocabulary work. Preserve this contribution in the project history.

Current prototype CSV locations are:

```text
data/prototype/careers.csv
data/prototype/career_skills.csv
```

The older `backend/scripts/import_careers.py` paths still require alignment before
rerunning that importer. The current job comparison uses the explicit ten-concept
catalogue in `backend/services/skill_catalog.py`; the earlier occupational datasets
are not yet a fully integrated recommendation model or labelled training dataset.

The next delivery sequence and study priorities are in [EXPERT_REVIEW_PLAN.md](EXPERT_REVIEW_PLAN.md).

The research preparation batch starts at [research/START_HERE.md](research/START_HERE.md).
It contains blank forms and a proposed protocol, not new study results.

## Relevant implementation notes

- [MULTISKILL_ASSESSMENTS.md](MULTISKILL_ASSESSMENTS.md)
- [SQL_ASSESSMENT.md](SQL_ASSESSMENT.md)
- [ASSESSMENT_UI.md](ASSESSMENT_UI.md)
- [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md)
- [CANDIDATE_EVIDENCE.md](CANDIDATE_EVIDENCE.md)
- [SEMANTIC_MATCHING.md](SEMANTIC_MATCHING.md)
- [MATCHING_CONTEXT.md](MATCHING_CONTEXT.md)
- [LIVE_JOBS.md](LIVE_JOBS.md)
- [RESEARCH_EVALUATION.md](RESEARCH_EVALUATION.md)
