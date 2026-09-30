# Research positioning and claim boundaries

Draft, 29 September 2026. Implementation inspected at commit `272efb0`.
Related work: [LITERATURE_MATRIX.md](LITERATURE_MATRIX.md).
Study design: [PILOT_PROTOCOL.md](PILOT_PROTOCOL.md).

## Working title

**AI Career Navigator: Assessment Evidence and Missing-Data Handling in
Job-Linked Learning Guidance**

Avoid “A Novel AI Model” until a model contribution and its evidence exist.

## Problem statement

A job posting can mention a skill that is absent from a candidate profile. That
absence can reflect missing information, rather than inability. Similarly, an
unanswered diagnostic question is not an observed wrong answer. A career guidance
system should expose these distinctions when suggesting a next learning action.
The research task is to measure the consequences of these decisions on an explicit,
limited set of skills and candidate cases.

## Proposed contribution

The current implementation separates self-reported claims, unverified project and
certificate records, diagnostic answers, and self-reported learning activity. It
retains versioned job, candidate, assessment and recommendation snapshots. It uses
fixed rules to distinguish practice suggested by errors from a need to collect
more evidence. A proposed controlled pilot compares the resulting actions with
self-report-only guidance and an assessment rule that counts skips as errors.

This is a proposed **system and empirical evaluation contribution**. Prior work
already covers embeddings, skills taxonomies, assessments and learning/job
recommendations. The literature comparison does not establish that our policy or
record structure is globally new. A useful result would be a transparent,
reproducible account of when this policy helps, harms or makes no difference.

## Research questions

- **RQ1 — extraction:** With the same frozen job texts, what changes when semantic
  suggestions are added to the current keyword/alias baseline?
- **RQ2 — recommendation:** With job requirements held fixed, how do assessment
  evidence and the handling of unanswered questions affect the appropriateness of
  topic-level recommendations?

RQ1 and RQ2 need separate reference data and metrics. Better extraction does not
establish better learning guidance. Higher quiz scores do not establish successful
learning, employability or job suitability.

## Operational states

| Evidence | Current interpretation | Learning action within the sampled topic |
| --- | --- | --- |
| No submitted assessment | Knowledge is unassessed | Request an assessment or review |
| All questions in the topic skipped | No assessed answers | Collect evidence; resources are optional |
| At least one wrong answer | An error occurred on this small diagnostic | Suggest topic practice; also show remaining skips |
| All topic answers correct and complete | This question set was answered correctly | No targeted remedial step from this attempt; broader evidence still needed |
| Project/certificate tag | Candidate-submitted, unverified claim | Show as context; do not convert to a score |
| Practice marked complete | Self-reported activity | Do not rewrite the assessment result |

Two questions per topic cannot support a calibrated proficiency scale. These
states describe available observations; they do not diagnose an entire skill.

## What is actually implemented

- Flask/PostgreSQL candidate workspace with a plain JavaScript UI.
- Six-question SQL, Python and REST/HTTP diagnostic banks, all draft content.
- A ten-concept skill catalogue; keyword/alias matching plus optional pretrained
  MiniLM suggestions and conservative context-review rules.
- Selected cached employer-board postings, manual refresh, timestamps and source
  versions; this is not an exhaustive labour-market feed.
- Job cards link to relevant supported skill diagnostics. A diagnostic's roadmap
  is selected by topic outcomes. It is **not yet filtered or prioritised by the
  exact topics in an individual posting**; call it job-linked guidance.
- Immutable comparisons use the latest submitted attempt per skill, not the best
  score. A new comparison incorporates updated records without rewriting old ones.
- Curated courses/references, original ungraded practice tasks and activity tracking.

There is no calibrated hiring score, automatic credential verification, adaptive
item selection, learned course ranking or combined project/certificate/quiz score.

## Claims and required evidence

| Claim | Status now | Evidence needed before claiming more |
| --- | --- | --- |
| The software performs the described flow | Functional checks completed | Maintain reproducible setup and demo checks |
| The new banks measure overall proficiency | Unsupported | Content review, broader tasks and appropriate measurement validation |
| Semantic suggestions improve extraction | Untested on an independent reference; current AI diagnostic gives no method separation | Reviewed labels, exposure audit, paired frozen evaluation |
| Missing-data handling improves guidance | Hypothesis | RQ2 comparison with independent practical-task references and reported trade-offs |
| Our approach is first or unique | Not established | Broader prior-art review; use a bounded claim even if no identical system is located |
| Course completion improves skill | Unsupported | Fresh outcome measures and an appropriate longitudinal/intervention design |
| We trained a career recommendation model | False for the current version | A defined training task, reviewed data, training run and independent evaluation |

## Stored data and live data

The pinned MiniLM encoder runs inference; current roadmap rules are not a trained
recommender. Historic datasets, frozen job packets and snapshots support review and
reproducibility. Live postings are refreshed inputs for inference, not automatic
training labels. A future supervised task needs a documented label definition,
reviewed train/validation/test partitions and grouping to control duplicate leakage.
The initial 24-job AI-labelled packet is development material, not sufficient
independent evidence for model training claims.

## Language for Saturday

“We built a working prototype connecting selected job postings with skill claims,
short diagnostics and learning resources. Our proposed study tests how assessment
evidence and unanswered-question handling change learning recommendations. We can
trace each output to the records used. The related-work review shows substantial
feature overlap, so we are evaluating a specific policy rather than claiming the
first integrated career platform. Independent evaluation is [state actual status].”

Replace the bracket with the true status at presentation time. Never replace it
with estimated or AI-generated participant results.
