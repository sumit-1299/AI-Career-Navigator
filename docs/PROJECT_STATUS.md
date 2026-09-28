# AI Career Navigator — implementation and research status

Updated 28 September 2026. This file distinguishes working functionality from
planned research claims. See [PROJECT_SCOPE.md](PROJECT_SCOPE.md) for the broader
product vision; not every part of that vision is implemented.

| Area | Current implementation | Remaining work / limits |
| --- | --- | --- |
| Local application | Flask, PostgreSQL, authentication and browser workspace | Deployment hardening and a hosted demo remain separate work |
| SQL assessment | Six-question diagnostic, immutable attempts, accuracy/coverage and topic feedback | Draft content; independent content review and proficiency validation pending |
| Learning roadmap | Curated SQL resources and practice steps linked to diagnostic results | Progress is self-reported; broader Python/REST assessment and roadmaps pending |
| Candidate evidence | Projects/certificates with skill tags, edits, version checks and archive/restore | Records remain unverified; no automatic credential verification |
| Job comparison | Keyword/alias baseline and keywords plus pretrained MiniLM suggestions for ten skill concepts | Thresholds uncalibrated; no overall hiring probability, suitability rank or proficiency score |
| Live jobs | Selected Canonical/Razorpay boards, cached freshness, filtering and versioned comparison snapshots | Limited employer coverage, manual refresh, no market-wide feed |
| Evaluation tools | Frozen job exporter, independent annotation page, adjudication, paired extraction metrics and a separate AI-draft development diagnostic | Human validation remains pending; agreement with an AI draft is preliminary and cannot establish accuracy |
| Research contribution | Candidate evidence, uncertainty and source snapshots form the proposed approach | Literature gap/novelty and added decision value are not established by working features alone |
| Training | Pretrained model used for inference | No project-specific supervised training or fine-tuning completed |

The next research task is documented in
[RESEARCH_EVALUATION.md](RESEARCH_EVALUATION.md). It measures job-skill extraction
first. A separate study is needed to test whether assessment/evidence context
improves skill-gap decisions. Synthetic smoke-test metrics are not research results.
The `diagnose` command can inspect development disagreements against an explicitly
AI-assisted draft while human validation is pending. It does not score test jobs,
train a model or satisfy the independent-review requirements of `evaluate`.

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

## Relevant implementation notes

- [SQL_ASSESSMENT.md](SQL_ASSESSMENT.md)
- [ASSESSMENT_UI.md](ASSESSMENT_UI.md)
- [LEARNING_ROADMAP.md](LEARNING_ROADMAP.md)
- [CANDIDATE_EVIDENCE.md](CANDIDATE_EVIDENCE.md)
- [SEMANTIC_MATCHING.md](SEMANTIC_MATCHING.md)
- [LIVE_JOBS.md](LIVE_JOBS.md)
- [RESEARCH_EVALUATION.md](RESEARCH_EVALUATION.md)
