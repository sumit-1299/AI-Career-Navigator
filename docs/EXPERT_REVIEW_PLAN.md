# Final submission plan — Thursday 8 October 2026

Plan updated 5 October 2026 after the submission date changed. Target: a coherent, reproducible research prototype
and an honest preliminary evaluation. Keep extending the existing repository and
credit the original team contribution. Do not restart the project.

The focused literature comparison, precise claim boundaries and study forms are now
available in [research/START_HERE.md](research/START_HERE.md). They remain drafts
pending human review and collection; do not mark the evaluation complete.

## Central research question

**Does assessment evidence, with explicit treatment of missing evidence, improve
job-linked learning recommendations compared with self-reported skills alone?**

This is a proposed question, not an established novelty claim. Semantic skill
extraction already has substantial prior work; for example,
[SkillSpan (NAACL 2022)](https://arxiv.org/abs/2204.12811) provides
annotated job-posting skill spans and extraction baselines. The combination of
assessment, provenance and uncertainty needs comparison with existing career and
learning systems before asserting a gap. A collection of useful features alone
is not proof of a new research contribution.

## What works after the resume/UI batch

- Local authenticated candidate workspace and database records.
- Resume extraction preview, reviewed saved text, versioned resume/job alignment
  and responsive navigation across the complete candidate workflow.
- SQL, Python and REST/HTTP foundation diagnostics with immutable results.
- Curated topic-linked resources, original practice tasks and activity tracking.
- Self-reported skills, project and certificate records, labelled unverified.
- Ten-concept keyword and pretrained MiniLM comparison, with manual context review.
- Cached jobs from two selected employer boards, freshness and source snapshots.
- Job-to-assessment-to-roadmap navigation and new comparisons with updated evidence.
- Frozen-job annotation, adjudication and extraction evaluation tools.

Limits: six draft questions per skill, two employer boards, manual job refresh,
uncalibrated semantic thresholds, no project-specific training, no validated
proficiency scale, no verified credentials and no overall job suitability ranking.
Live listings can change or close. A comparison is an explanation, not proof of
eligibility, employability or comprehensive skill coverage.

## Remaining work, in priority order

| Work | Concrete output | Completion condition |
| --- | --- | --- |
| Question/content review | Human review of each item, answer, ambiguity and topic coverage | Record reviewer, date, issue and resolution; version any later bank change |
| Literature source check | Eight-work comparison drafted in `research/LITERATURE_MATRIX.md` | Verify reading limits and metadata, inspect remaining full texts and refine the bounded contribution |
| Independent extraction pilot | Original frozen text, independent reviews and adjudication | Use genuinely independent reviewers; preserve disagreements and evaluate held-out data only after decisions are fixed |
| Recommendation pilot | Prespecified protocol, candidate cases and expert ratings | Test whether evidence changes the appropriateness of recommended actions; report the sample and limits |
| Review documents | Project report, paper draft and short slide deck | Methods match implementation; distinguish observations, preliminary results and planned work |
| Demonstration | Reproducible local run, prepared test account, cached example jobs and backup recording | Demonstrate the full flow without depending on new live fetches during review |
| Portfolio/reproducibility | Focused commits, setup instructions, versioned run commands and contribution notes | Another reviewer can identify what was built and reproduce the stated checks |

## Keep two experiments distinct

**Extraction experiment:** compare keyword/alias extraction with keyword plus
semantic suggestions on the same frozen job texts and independently reviewed
labels. Report per-skill precision/recall/F1, coverage, disagreements and the
uncertain-label policy. The existing tooling supports this experiment.

The current AI-draft development diagnostic is debugging evidence. After the
context correction, both methods agree with its scored development labels and
produce identical skill sets. This does not establish independent accuracy or a
semantic advantage. Do not turn AI answers into nominal human reviewers. Texts
or labels inspected during development are not a clean independent test; obtain
new held-out jobs where required and record the actual exposure history.

**Recommendation experiment:** hold job requirements and extraction output fixed.
Compare a documented self-report-only baseline against the assessment-informed
policy. Use a small, explicitly exploratory set of consenting pilot participants
or clearly labelled scenario cases if participants are unavailable. Avoid mixing
synthetic scenarios with observed participant outcomes.

Collect independently judged reference recommendations or fresh practical task
evidence, not just ratings that reproduce our own decision rules. Blind and
counterbalance the displayed methods when feasible. Record recommendation
appropriateness, unsupported deficit assertions, usefulness and time to select a
next step. Report disagreement, sample size and uncertainty. A convenience pilot
cannot establish general effectiveness. Do not claim learning gains without an
appropriate pre/post design and fresh tasks.

Projects/certificates provide review context in this version; they do not alter
roadmap scoring. Do not claim tested multi-source evidence fusion unless it is
actually implemented and evaluated. Claims about practicality, traceability or
usability must be separated from claims about recommendation accuracy.

## Stored data, live data and training

Use frozen, versioned, reviewed datasets for evaluation and any future supervised
training. Current live postings are inference inputs; save source, timestamp and
posting version with outputs. Do not automatically retrain on unreviewed live
jobs. Prevent duplicate jobs, employers or near-identical texts leaking across
training and evaluation partitions where relevant to the experiment.

The current model is a pretrained encoder used for inference. Roadmap decisions
are explicit rules. This is a valid prototype architecture for testing the stated
research question; label it accurately. If institutional requirements specifically
require training, define one small supervised task with reviewed training data,
validation and an untouched test set. Do not fine-tune on the 24 AI-labelled jobs
and present the result as independent validation or a new foundation model.

## Schedule

| Date | Deliverable |
| --- | --- |
| Mon 5 Oct | Apply resume/UI update, run the complete local flow and commit it; review report/paper drafts and settle author attribution |
| Tue 6 Oct | Complete feasible human content/source checks and independent pilot work only after freezing inputs; record actual counts and exclusions |
| Wed 7 Oct | Freeze code; insert only measured results, prepare slides, rehearse the cached-data demo and record a backup |
| Thu 8 Oct | Submit the verified application and documents with completed/pending work stated accurately |

If independent data collection cannot finish, present the evaluation protocol and
clearly marked preliminary diagnostics. Do not invent results to fill the paper.
Draft the architecture/method sections while evaluation proceeds; leave results
explicitly pending until measured.

Defer a new framework, many additional occupations, market-wide job crawling,
automatic certificate verification, large-model fine-tuning, dynamic course
scraping and a general job-ranking model. A reliable complete backend-career
example is the review target.

## Faster delivery cadence

Use complete batches: one patch, one integrated verification pass, one meaningful
portfolio commit. Use a single concise smoke check locally, then move on. Split
research reading, human review and writing among available team members while
implementation progresses. This does not require restarting the codebase.
