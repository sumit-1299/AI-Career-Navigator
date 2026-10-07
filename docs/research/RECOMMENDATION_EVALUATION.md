# Recommendation Evaluation & Research Validation

## 1. Objective

Phase 12.1 introduces a deterministic research evaluation layer for the
AI Career Navigator.

The purpose is to evaluate the behavior of the career recommendation
pipeline on a controlled benchmark rather than to claim real-world
employment prediction accuracy.

The evaluation layer is read-only and does not modify the PostgreSQL
database.

It evaluates recommendation ranking, skill-gap diagnostics, robustness,
cross-module consistency, and explanation validity.

## 2. Evaluation Dataset

The benchmark dataset is located at:

data/prototype/evaluation/career_recommendation_benchmark.json

The dataset contains controlled career recommendation scenarios covering
the project's standardized IT career tracks.

The benchmark is explicitly classified as:

DEMO / SAMPLE / PROTOTYPE RESEARCH BENCHMARK

It is not real student ground truth.

It must not be interpreted as an official university dataset, employer
dataset, labor-market ground truth, or employment-outcome dataset.

## 3. Evaluation Methodology

The evaluation process is deterministic and consists of the following
general stages:

1. Extract benchmark profile information.
2. Generate career recommendations.
3. Evaluate the ranked career list.
4. Evaluate expected skill gaps.
5. Execute controlled robustness checks.
6. Validate consistency across intelligence modules.
7. Aggregate evaluation metrics.

The evaluation layer reuses the existing career intelligence
architecture rather than creating a separate recommendation engine.

## 4. Career Ranking Metrics

The evaluation supports Top-K ranking metrics.

The evaluated K values are:

- K = 1
- K = 3
- K = 5

### 4.1 Precision@K

Precision@K is calculated as the number of relevant careers appearing in
the first K recommendations divided by K.

Precision@K = relevant recommendations in Top-K / K

The value is bounded between 0 and 1.

### 4.2 Recall@K

Recall@K measures how many of the benchmark's relevant careers appear
within the first K recommendations.

Recall@K = relevant recommendations in Top-K / total relevant careers

The value is bounded between 0 and 1.

### 4.3 Hit Rate@K

Hit Rate@K is 1 when at least one relevant career appears in the first
K recommendations.

Otherwise it is 0.

### 4.4 Mean Reciprocal Rank

Mean Reciprocal Rank evaluates the position of the first relevant
recommendation.

For each case:

MRR = 1 / rank of the first relevant recommendation

If no relevant recommendation occurs in the evaluated ranking, the
reciprocal rank is 0.

### 4.5 NDCG@K

Normalized Discounted Cumulative Gain evaluates the ranking position of
relevant recommendations.

The implementation supports NDCG at the configured Top-K values and
keeps the resulting metric within the normalized range.

## 5. Skill-Gap Diagnostic Evaluation

Phase 12.1 also evaluates the system's identification of expected
missing competencies.

The evaluation includes:

- skill-gap precision
- skill-gap recall
- skill-gap F1 score
- skill coverage
- false-positive gap rate
- false-negative gap rate

Canonical skill representations are preferred where available so that
equivalent terminology does not unnecessarily appear as different
skills.

The evaluation distinguishes expected benchmark gaps from predicted
gaps.

## 6. Robustness Evaluation

The benchmark includes controlled perturbation checks intended to detect
unstable recommendation behavior.

The implemented robustness categories include:

1. Input order invariance
2. Casing and whitespace invariance
3. Duplicate skill stability
4. Monotonic skill addition
5. Irrelevant skill stability

These checks do not claim that every additional skill must always improve
a career ranking.

Instead, they verify that harmless representation changes do not
unexpectedly alter system behavior.

## 7. Cross-Module Consistency

The evaluation validates consistency between the major career
intelligence layers.

The evaluated architecture connects:

- Core career readiness
- Counterfactual Skill ROI
- Portfolio and Capstone recommendations
- Academic benchmarking
- Industry demand weighting
- Multi-Hop Career Trajectory
- Interview readiness diagnostics
- Live Job alignment

The purpose of this validation is consistency, not identical scoring.

Each module measures a different aspect of career intelligence.

A consistency check therefore verifies that module outputs do not
contradict the underlying career and skill information without requiring
all modules to produce the same numerical result.

## 8. Explainability Validation

Recommendation explanations are checked for factual grounding and
appropriate educational language.

An explanation should be based on actual computed recommendation factors,
skills, gaps, or supporting evidence.

The evaluation also checks for inappropriate guarantee-oriented claims.

Examples of prohibited claims include:

- guaranteed employment
- guaranteed job placement
- placement promise
- foolproof career prediction

The system must communicate recommendations as decision support and
practice guidance rather than guaranteed outcomes.

## 9. API

Phase 12.1 exposes benchmark evaluation through the career evaluation
API.

Supported endpoint forms include:

GET /api/careers/evaluation/benchmark

POST /api/careers/evaluation/benchmark

The evaluation supports configurable parameters including Top-K
selection and optional robustness, consistency, and case-detail output
where supported by the implementation.

The API returns structured evaluation information rather than modifying
student or career records.

## 10. Testing

The dedicated Phase 12.1 test module is:

backend/tests/test_phase12_module1.py

The implementation contains 32 dedicated Phase 12.1 tests.

The tests cover benchmark structure, ranking metrics, skill-gap metrics,
robustness behavior, consistency validation, explanation validation,
determinism, API behavior, and database safety.

The verified complete backend regression baseline after the Phase 12.1
implementation and live-job integration is:

341 / 341 tests passing.

The regression suite reported zero failures and zero errors.

## 11. Reproducibility

The evaluation is designed to be deterministic.

The benchmark operates on controlled structured input and does not
require external LLM calls or expensive model training.

The evaluation service uses in-memory evaluation structures and does not
require persistent evaluation tables.

Repeated evaluation of the same benchmark inputs should produce
reproducible results.

## 12. Database Safety

The evaluation layer does not require a new database schema.

The project retains exactly 11 PostgreSQL tables.

The evaluation process is designed to be read-only with respect to the
application database.

No additional evaluation tables are required.

## 13. Research Limitations

The benchmark has important limitations.

First, the evaluation profiles are controlled prototype scenarios rather
than real longitudinal student records.

Second, the benchmark does not represent the complete population of
students.

Third, benchmark relevance labels are controlled research assumptions
rather than independently verified employment outcomes.

Fourth, recommendation quality on this benchmark does not establish
employment prediction accuracy.

Fifth, the evaluation cannot guarantee that a recommended career will
produce employment, placement, salary, or career success.

Therefore the reported metrics should be interpreted as measurements of
system behavior on a controlled prototype benchmark.

## 14. Research Boundary

The system is intended to provide explainable educational career
decision support.

It is not intended to:

- guarantee employment
- guarantee placement
- predict a person's future with certainty
- diagnose psychological characteristics
- measure intelligence
- replace professional career counselling

The benchmark therefore evaluates recommendation-system behavior rather
than personal worth or employment probability.

## 15. Reproducible Evaluation Procedure

A reproducible evaluation can be performed by:

1. Loading the controlled benchmark dataset.
2. Running the recommendation evaluation service.
3. Generating the ranked career recommendations.
4. Calculating Top-K ranking metrics.
5. Calculating skill-gap metrics.
6. Running robustness checks.
7. Running cross-module consistency checks.
8. Validating explanations.
9. Aggregating the results.
10. Recording the benchmark version and limitations.

The same benchmark input and deterministic implementation should produce
the same evaluation behavior.

## 16. Future Research

Future research may extend the evaluation framework with:

- real student evaluation cohorts
- independently validated relevance labels
- employer or placement outcome datasets
- longitudinal career tracking
- larger benchmark datasets
- external evaluator studies
- adversarial profile generation
- temporal industry-demand evaluation
- human evaluation of explanation quality
- comparison with alternative recommendation algorithms

These are future research directions and are not represented as
currently implemented functionality.

## 17. Provenance Statement

This benchmark is:

DEMO / SAMPLE / PROTOTYPE RESEARCH BENCHMARK — NOT REAL STUDENT
GROUND TRUTH.

Evaluation metrics measure system behavior on the controlled benchmark.

They do not constitute employment prediction accuracy and should not be
interpreted as guaranteed career outcomes.

## 18. Summary

Phase 12.1 establishes a reproducible evaluation layer around the
existing AI Career Navigator intelligence pipeline.

The evaluation covers career ranking, skill-gap identification,
robustness, cross-module consistency, and explainability.

The implementation remains deterministic, lightweight, and compatible
with the existing 11-table PostgreSQL architecture.

The resulting benchmark provides a research-oriented basis for measuring
system behavior while explicitly separating prototype evaluation from
real-world employment prediction.
