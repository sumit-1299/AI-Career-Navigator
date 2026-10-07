# Practical Skill Assessment & Hands-On Task Engine

## 1. Objective

Phase 12 Module 12.3 establishes the **Practical Skill Assessment & Hands-On Task Engine** for AI Career Navigator. The overarching objective is to provide students with structured, scenario-driven technical exercises linked directly to:
- their target career track among the 10 canonical IT pathways,
- active skill gaps identified during profile diagnostics,
- missing competencies extracted from live employer job vacancies (Phase 12.2),
- portfolio capstone deliverables (Phase 11.2), and
- technical interview simulation preparation (Phase 11.6).

Unlike generic chatbots or unconstrained generative evaluators, this engine provides a controlled, deterministic evaluation framework. It delivers immediate, explainable feedback on technical submissions without external API dependencies or opaque non-reproducible grading.

> [!IMPORTANT]
> **Educational Assessment Disclaimer**:
> Practical task scores are deterministic educational assessment signals and do not represent employment probability, interview probability, or guaranteed job readiness.

---

## 2. Architecture & System Design

The Practical Skill Assessment Engine is designed as a stateless, read-only orchestration layer operating in-memory over indexed data structures and relational models.

```
                      +---------------------------------------+
                      |         Candidate Context             |
                      | (Student Profile, Skill Gaps, Vacancy)|
                      +-------------------+-------------------+
                                          |
                                          v
+------------------------+    +-----------------------+    +------------------------+
|   Live Jobs Context    |--->|  PracticalTaskService |<---|  Career Models         |
| (Phase 12.2 Vacancies) |    |  (Task Bank & Scorer) |    | (10 Canonical Tracks)  |
+------------------------+    +-----------+-----------+    +------------------------+
                                          |
        +---------------------------------+---------------------------------+
        |                 |               |                |                |
        v                 v               v                v                v
+---------------+ +---------------+ +------------+ +---------------+ +---------------+
| Skill ROI     | | Portfolio     | | Academic   | | Industry      | | Trajectory    |
| Priority      | | Alignment     | | Deficits   | | Demand        | | Bridge Skills |
| (Phase 11.1)  | | (Phase 11.2)  | | (Phase 11.3| | (Phase 11.4)  | | (Phase 11.5)  |
+---------------+ +---------------+ +------------+ +---------------+ +---------------+
                                          |
                                          v
                      +---------------------------------------+
                      |      Deterministic Task Bank          |
                      |   - 30 Scenario-Driven Tasks          |
                      |   - Beginner / Intermediate / Advanced|
                      +-------------------+-------------------+
                                          |
                                (Student Submission)
                                          v
                      +---------------------------------------+
                      |     Deterministic Evaluation Engine   |
                      |   - Concept Coverage (40%)            |
                      |   - Requirement Coverage (25%)        |
                      |   - Criteria Coverage (20%)           |
                      |   - Completeness (10%)                |
                      |   - Structure (5%)                    |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |     Skill Evidence & Formative Band   |
                      |   - Mastery Bands (85+, 70+, 55+, <55)|
                      |   - Matched vs Missing Concepts       |
                      |   - Recommended Next Task             |
                      +---------------------------------------+
```

---

## 3. Task Taxonomy & Structure

The engine organizes tasks across 12 concrete technical disciplines:
1. `CODING`
2. `DATABASE`
3. `API_DEVELOPMENT`
4. `DEBUGGING`
5. `SYSTEM_DESIGN`
6. `CLOUD`
7. `DEVOPS`
8. `SECURITY`
9. `DATA_ANALYSIS`
10. `MACHINE_LEARNING`
11. `NETWORKING`
12. `CONCEPTUAL_PRACTICE`

Every task in the controlled task bank complies with an immutable JSON schema:
- `id`: Unique identifier (e.g., `pt-sd-01`, `pt-wd-02`).
- `title`: Concise descriptive engineering title.
- `career_id`: Integer foreign key (1–10) referencing the canonical IT career.
- `career_title`: String title of the canonical track.
- `skill`: Normalized canonical skill key (e.g., `Python`, `Docker`, `SQL`).
- `category`: Functional category enum.
- `difficulty`: Deterministic difficulty rating (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`).
- `estimated_minutes`: Estimated time budget (15–45 minutes).
- `scenario`: Realistic enterprise problem statement and context.
- `objective`: Primary technical deliverable or goal.
- `requirements`: Explicit list of 3–4 functional requirements.
- `expected_concepts`: List of 4–6 foundational concepts and keywords.
- `evaluation_criteria`: Qualitative benchmarks for comprehensive solutions.
- `hints`: Progressive technical hints for unblocking learners.
- `expected_outcome`: Clear definition of a successful deliverable.
- `learning_objective`: Pedagogical justification for the exercise.
- `portfolio_relevance`: Direct connection to capstone project deliverables.
- `interview_relevance`: Direct connection to technical interview evaluations.

---

## 4. Multi-Factor Deterministic Task Selection

When a student queries available tasks (`GET /api/practical-tasks`), the engine computes a composite priority score:

$$\text{Priority Score} = \text{Base}(50.0) + \Delta_{\text{Profile Gap}} + \Delta_{\text{Job Gap}} + \Delta_{\text{Skill ROI}} + \Delta_{\text{Academic}} + \Delta_{\text{Demand}} + \Delta_{\text{Portfolio}}$$

### Weighted Signal Contributions:
1. **Candidate Profile Gap (+25.0)**: Boosted if the task's skill is missing from the student's authenticated database profile.
2. **Live Job Vacancy Gap (+35.0)**: Boosted if the task targets a competency missing from an inspected live vacancy (Phase 12.2).
3. **Skill ROI Rank (+15.0 to +20.0)**: Boosted if the skill is classified as a `QUICKEST_WIN` (+20.0) or `HIGH` ROI tier (+15.0) via `SkillRoiService` (Phase 11.1).
4. **Academic Deficit (+10.0)**: Boosted if academic benchmarking identifies a curriculum deficit via `AcademicBenchmarkService` (Phase 11.3).
5. **Industry High Demand (+10.0)**: Boosted if market intelligence indicates `VERY_HIGH` or `HIGH` hiring temperature via `IndustryDemandService` (Phase 11.4).
6. **Portfolio Capstone Synergy (+10.0)**: Boosted if the skill contributes toward a recommended portfolio project via `PortfolioProjectService` (Phase 11.2).

### Determinism Guarantee:
Sorting uses `(-priority_score, task_id)`, ensuring that identical filter parameters and student contexts produce identical task rankings.

---

## 5. Task Difficulty Progression

Difficulty levels are strictly calibrated to support staged learner progression:

| Level | Cognitive Complexity | Expected Student Output |
|---|---|---|
| **BEGINNER** | Foundational syntax, basic input validation, standard queries, simple Dockerfiles. | Direct function implementation, single-table query, baseline markup. |
| **INTERMEDIATE** | Concurrency debugging, multi-table analytical joins, race condition fixes, SIEM log triage. | Multi-component logic, synchronization mechanisms, analytical SQL with CTEs. |
| **ADVANCED** | Scalable system design, zero-downtime Kubernetes deployments, database PITR recovery, imbalanced classification. | Architectural blueprints, multi-step disaster recovery workflows, trade-off analysis. |

---

## 6. Evaluation Methodology & Normalization

Student responses are evaluated in-memory using deterministic linguistic and structural parsing:
1. **Text Normalization**:
   - Lowercase folding.
   - Punctuation removal: `re.sub(r"[^\w\s]", " ", text)`.
   - Whitespace collapsing: reduction of tabs, line breaks, and multiple spaces.
2. **Concept Matching**:
   - Checks presence of exact concept phrases or substantive token overlap (>= 75%).
3. **Requirement Matching**:
   - Strips linguistic stopwords (`the`, `is`, `implement`, etc.) and performs root stemming on key terms.
   - Requirement is marked addressed if >= 35% of key requirement terms appear in the submission.
4. **Criteria Matching**:
   - Evaluates qualitative criteria terms against stemmed response tokens (>= 35% threshold).
5. **Completeness Scoring**:
   - Calibrated word count progression:
     - < 10 words: 15.0
     - < 25 words: 40.0
     - < 50 words: 65.0
     - < 90 words: 85.0
     - >= 90 words: 100.0
6. **Structure Scoring**:
   - Baseline: 40.0
   - Numbered steps / bullet list markers: +25.0
   - Code blocks / functions / SQL declarations: +25.0
   - Section headers / markdown demarcations: +10.0
   - Clamped to 100.0.

---

## 7. Scoring Formula & Result Bands

The final practical score is computed using an explainable, weighted formula:

$$\text{Practical Score} = 0.40 \cdot C_{\text{Concept}} + 0.25 \cdot R_{\text{Requirement}} + 0.20 \cdot Cr_{\text{Criteria}} + 0.10 \cdot Comp + 0.05 \cdot Struct$$

The score is clamped to the range $[0.0, 100.0]$ and rounded to one decimal place.

### Educational Result Bands:
- **85.0 – 100.0**: `STRONG_PRACTICAL_MASTERY`
- **70.0 – 84.9**: `PRACTICE_READY`
- **55.0 – 69.9**: `NEEDS_REINFORCEMENT`
- **0.0 – 54.9**: `FOUNDATION_REQUIRED`

> [!NOTE]
> Bands reflect formative pedagogical readiness. They are never labeled as hiring probabilities or placement predictions.

---

## 8. Skill Evidence & Feedback Synthesis

Upon evaluation, the engine synthesizes an ephemeral skill evidence record:
- `demonstrated_skill`: Canonical skill key.
- `practical_score`: Numerical score (0–100).
- `evidence_strength`: Qualitative category (`STRONG`, `MODERATE`, `LIMITED`, `INSUFFICIENT`).
- `assessment_band`: Result band identifier.
- `is_verified_signal`: Boolean (`True` if score >= 70.0).
- `remaining_gaps`: Constructive technical list of missing concepts and unaddressed requirements.
- `recommended_next_task`: Deterministic next exercise:
  - If score >= 70: steps up to higher difficulty task.
  - If score < 70: suggests reinforcement task targeting the same skill.

---

## 9. Career Track Integration

All 30 tasks are explicitly mapped to the 10 canonical IT careers:
1. Software Developer: Python API validation, Java concurrency, cursor pagination.
2. Web Developer: Semantic accessible HTML, React async race conditions, DOM virtualization.
3. Data Analyst: Python data imputation, SQL cohort retention, statistical anomaly detection.
4. Data Scientist: Feature engineering pipelines, model overfitting mitigation, PR-AUC evaluation.
5. AI/ML Engineer: Sequence tokenization, gradient clipping, low-latency inference architecture.
6. Cloud Engineer: Multi-AZ VPC design, auto-scaling compute groups, S3 security remediation.
7. DevOps Engineer: Multi-stage Dockerfiles, CI/CD pipeline debugging, blue-green Kubernetes rollouts.
8. Cybersecurity Analyst: SQL injection remediation, SIEM brute-force triage, enterprise RBAC design.
9. Network Engineer: Class C subnetting, asymmetric routing diagnostics, stateful firewall policies.
10. Database Administrator: Composite B-tree indexing, PostgreSQL deadlock resolution, PITR recovery.

---

## 10. Live Job Vacancy Integration (Phase 12.2)

In the Phase 12.2 Job Action Center, every identified missing skill includes a *"Practice this skill"* action. This directly links students to practical tasks filtered by that skill and career track. When `job_source` and `job_id` are passed, tasks closing vacancy gaps automatically receive a +35 priority score boost.

---

## 11. Portfolio & Capstone Integration (Phase 11.2)

Every practical task includes a `portfolio_relevance` annotation detailing how the exercise contributes toward concrete capstone deliverables (e.g., repository architecture, CI/CD pipelines, analytical dashboards).

---

## 12. Security Architecture

1. **Zero Code Execution**: Student submissions are evaluated as text. No `eval()`, `exec()`, or shell processes are executed.
2. **Payload Protection**: Answers are capped at 25,000 characters (`MAX_ANSWER_LENGTH`). Oversized submissions return HTTP 413.
3. **Authentication Safety**: Supports optional JWT authentication (`verify_jwt_in_request(optional=True)`). Guest submissions are fully supported without privilege escalation.
4. **Input Sanitization**: Regular expression parsing safely strips hostile characters prior to tokenization.

---

## 13. Database Boundary & Zero Schema Mutation

- **Zero Schema Migrations**: No new tables, migrations, or DDL statements.
- **Relational Integrity**: The PostgreSQL database remains strictly at **11 tables**:
  - `canonical_skills`, `career_preferences`, `career_skills`, `careers`, `data_sources`, `learning_resources`, `skill_aliases`, `skills`, `student_profiles`, `user_learning_progress`, `users`.
- **Zero Persistent Answer Storage**: Student attempts and scores are evaluated ephemerally in-memory and return directly in the response payload.

---

## 14. Reproducibility

Because evaluation uses deterministic token and concept matching without stochastic sampling, temperature variables, or external network dependencies:
- Identical answers to the same task always yield identical numerical scores.
- Unit and integration tests run deterministically in < 5 seconds.

---

## 15. Limitations

1. **Syntactic vs Semantic Nuance**: The deterministic keyword evaluator verifies technical concept presence and structural rigor, but does not execute interactive runtime code tests.
2. **English Language Evaluation**: Current concept tokenizers operate on English technical terminology.
3. **Static Task Bank**: Tasks are curated within the immutable service registry rather than dynamically crowdsourced.

---

## 16. Research Boundary & Pedagogical Scope

Phase 12.3 is explicitly positioned as a formative learning environment. It encourages active hands-on technical reasoning and provides actionable gap analysis before students apply for live roles or participate in mock interviews.

---

## 17. Future Improvements

1. Optional client-side WebAssembly sandboxes (e.g., Pyodide / SQLite in browser) for interactive live code verification.
2. Additional localized language synonyms for technical concept keywords.
3. Automated student progress tracking linked to Phase 7 study plan milestones.
