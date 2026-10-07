# Friend Branch Backend Integration & Rolled-Back Module Analysis

> **Mandatory Architecture Statement:**
> "Friend branch UI was intentionally excluded from integration. The friend's implementation was treated as a donor/reference implementation, while the current AI Career Navigator remained the source of truth."

---

## 1. Reference Origin & Identification
- **Donor / Reference Branch:** `origin/integration/collaborative-final`
- **Donor Project Location:** `~/Desktop/projects/AI-Career-Navigator-integration-collaborative-final/`
- **GitHub Repository:** `https://github.com/sumit-1299/AI-Career-Navigator`
- **Donor Fork Commit:** Forked off commit `1acf662` (`feat(phase11.2): implement portfolio project recommendation engine`)
- **Donor Commits:**
  - `5ffb337`: `feat: integrate research intelligence backend` (jprajwal282002)
  - `c184775`: `release: finalize AI Career Navigator integration` (jprajwal282002)
- **Source of Truth:** Current project repository (`~/Desktop/projects/AI-Career-Navigator/`) containing verified Phases 1–10, 11.1–11.6, and 12.1.

---

## 2. Previously Rolled-Back & Donor Modules Identified

### Primary Identified Module:
**Real-Time Live Job Board Feeds & Vacancy Skill Alignment Engine** (`LiveJobsService` / `JobMatchingService`)
- **Context:** In earlier planning iterations of market intelligence (Phase 5/9.2), live job-board feeds (Greenhouse, Ashby, Lever) and real-time posting skill-matching had been explored but deferred/rolled back in favor of deterministic canonical O*NET/ESCO career tracks and macro industry projections.
- **Evidence:**
  1. `backend/services/live_jobs.py` (708 lines): Direct connectors to Greenhouse, Ashby, and Lever public job feeds.
  2. `backend/services/job_matching.py` (208 lines): Heading-based requirement extraction and skill-to-vacancy alignment.
  3. `backend/routes/jobs.py` (519 lines) & `backend/routes/job_matches.py` (157 lines): Endpoints for live job browsing, filtering, and candidate comparison.
  4. `frontend/src/pages/TechJobsPage.jsx` & `JobAlignmentPage.jsx`: Candidate browsing interface.

### Secondary Identified Module:
**Practical Technical Foundations Diagnostic Bank** (`SqlAssessmentService`)
- **Context:** Discrete, versioned multiple-choice diagnostic covering SQL relational fundamentals (filtering, join cardinality, aggregation, null semantics, subqueries).
- **Evidence:**
  1. `backend/services/sql_assessment.py` & `assessment_catalog.py`: 6-question MCQ diagnostic with deterministic scoring.
  2. `backend/scripts/try_sql_assessment.py`: Standalone CLI execution script.

### Distinct Container Orchestration Note:
- Module 10.4 (Docker Compose Orchestration) was intentionally rolled back in commit `b0a8ea3`. The friend's branch did not restore or reimplement Docker Compose, respecting that rollback.

---

## 3. File-by-File Comparison Matrix

| Friend File | Type | Purpose | Current Equivalent | Decision | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `backend/services/live_jobs.py` | Service | Read-only connectors for Greenhouse, Ashby, Lever | None | **SAFE TO ADAPT** | Adapt into `live_jobs_service.py` with offline fallback fixtures and in-memory TTL caching. |
| `backend/services/job_matching.py` | Service | Vacancy requirement extraction & candidate match | Partial (`skill_gap_service.py`) | **SAFE TO ADAPT** | Integrated deterministic keyword & canonical skill matching; skipped heavy ONNX model. |
| `backend/services/sql_assessment.py` | Service | In-memory 6-question SQL diagnostic | `interview_simulation_service.py` (Phase 11.6) | **SAFE TO ADAPT** | Adapted as lightweight in-memory diagnostic utility (`sql_assessment_service.py`). |
| `backend/services/assessment_catalog.py` | Service | Python MCQ questions & catalog wrapper | `interview_simulation_service.py` (Phase 11.6) | **DUPLICATE** | Phase 11.6 provides comprehensive multi-track technical interview simulation. |
| `backend/services/candidate_evidence.py` | Service | Portfolio link & certification URL validation | `portfolio_project_service.py` (Phase 11.2) | **SAFE TO ADAPT** | URL validation logic incorporated into `live_jobs_service.py`. |
| `backend/services/resume_evidence.py` | Service | Resume keyword scanning | `resume_extraction_service.py` (Phase 4) | **DUPLICATE** | Phase 4 already contains full multi-format parsing and career scoring. |
| `backend/services/resume_parser.py` | Service | PDF/DOCX text parsing | `resume_extraction_service.py` (Phase 4) | **DUPLICATE** | Phase 4 already supports PDF, DOCX, and TXT parsing. |
| `backend/services/learning_roadmap.py` | Service | Basic study roadmap generation | `roadmap_service.py` (Phase 6) | **DUPLICATE** | Phase 6 contains complete DAG sequencing, duration estimates, and prerequisites. |
| `backend/services/foundations_resources.py`| Service | Static SQL/Python link dictionary | `learning_resource_service.py` (Phase 8) | **DUPLICATE** | Phase 8 curated database catalog is authoritative. |
| `backend/services/research_diagnostic.py` | Service | Research diagnostic logging | `recommendation_evaluation_service.py` (Phase 12.1)| **DUPLICATE** | Phase 12.1 provides comprehensive evaluation suite. |
| `backend/services/research_evaluation.py` | Service | Offline research evaluation script | `recommendation_evaluation_service.py` (Phase 12.1)| **DUPLICATE** | Phase 12.1 contains full benchmark dataset with 32 dedicated tests. |
| `backend/services/semantic_encoder.py` | Service | ONNX MiniLM CPU inference | None | **REJECT / OBSOLETE** | Requires heavy external dependencies (`onnxruntime`, `tokenizers`, 90MB weights); violates sandbox constraints. |
| `backend/services/skill_catalog.py` | Service | Hardcoded 10-skill in-memory dictionary | `canonical_skills` table (30 canonical skills) | **DUPLICATE** | Relational taxonomy in database is authoritative. |
| `backend/models/job_comparison.py` | Model | Table `job_comparisons` | None | **REJECT** | Violates strict 11-table database constraint. Comparisons run on-the-fly. |
| `backend/models/assessment_attempt.py` | Model | Table `assessment_attempts` | None | **REJECT** | Violates strict 11-table database constraint. Scoring is deterministic in-memory. |
| `backend/models/candidate_evidence.py` | Model | Table `candidate_evidence` | None | **REJECT** | Violates strict 11-table database constraint. |
| `backend/models/candidate_resume.py` | Model | Table `candidate_resumes` | None | **REJECT** | Violates strict 11-table database constraint. |
| `backend/models/learning_roadmap.py` | Model | Table `learning_roadmaps` | None | **REJECT** | Violates strict 11-table database constraint. |
| `backend/models/password_reset_token.py`| Model | Table `password_reset_tokens` | None | **REJECT** | Violates strict 11-table database constraint. |
| `backend/routes/jobs.py` | Route | Live jobs search & detail endpoints | None | **SAFE TO ADAPT** | Integrated as `/api/jobs` blueprint. |
| `backend/routes/job_matches.py` | Route | Candidate job match routes | None | **SAFE TO ADAPT** | Merged cleanly into `/api/jobs` (`/match` and `/match-custom`). |
| `backend/routes/assessments.py` | Route | Assessment CRUD routes | None | **SAFE TO ADAPT** | Expose read-only SQL diagnostic under `/api/jobs/diagnostics/sql`. |
| `backend/routes/evidence.py` | Route | Evidence submission endpoints | None | **REJECT** | Requires rejected database tables. |
| `backend/routes/resume.py` | Route | Resume endpoints | `routes/skills.py` (`/extract-resume`) | **DUPLICATE** | Existing `/api/skills/extract-resume` is authoritative. |
| `backend/routes/roadmaps.py` | Route | Roadmap endpoints | `routes/careers.py` (`/roadmap`) | **DUPLICATE** | Existing Phase 6 roadmap endpoints are authoritative. |
| `backend/routes/backend_learning_resources_fixed.py` | Route | Accidental duplicate of Phase 8 routes | `routes/learning_resources.py` | **DUPLICATE** | Existing `learning_resources.py` is authoritative. |
| `frontend/src/pages/TechJobsPage.jsx` | UI | Public tech jobs browsing page | None | **SKIP — UI** | Skipped per strict instruction. |
| `frontend/src/pages/JobAlignmentPage.jsx` | UI | Job comparison page | None | **SKIP — UI** | Skipped per strict instruction. |
| `frontend/src/pages/PracticalTasksPage.jsx`| UI | Practical tasks page | None | **SKIP — UI** | Skipped per strict instruction. |
| `frontend/src/pages/LandingPage.jsx` | UI | Marketing landing page | None | **SKIP — UI** | Skipped per strict instruction. |
| `frontend/src/pages/ForgotPasswordPage.jsx`| UI | Password reset request UI | None | **SKIP — UI** | Skipped per strict instruction. |
| `frontend/src/pages/ResetPasswordPage.jsx` | UI | Password reset submission UI | None | **SKIP — UI** | Skipped per strict instruction. |
| `frontend/src/pages/DashboardPage.jsx` | UI | Friend's rewritten dashboard | Current `DashboardPage.jsx` | **SKIP — UI** | Preserved current dashboard intact. |
| `frontend/src/services/api.js` | Service | Frontend API client methods | Current `api.js` | **SAFE TO ADAPT** | Added minimal helper client methods (`listLiveJobs`, `matchLiveJob`, etc.). |
| `frontend/src/services/jobApi.js` | Service | Friend's standalone job API wrapper | Current `api.js` | **SKIP — UI** | Standardized into unified `api.js`. |

---

## 4. Backend Logic Integrated
1. **`LiveJobsService` (`backend/services/live_jobs_service.py`)**:
   - Ingests public feeds from 9 configured employer boards across Greenhouse (Canonical, Razorpay), Ashby (Notion, Vercel, Linear, Ramp), and Lever (Dun & Bradstreet, Spreetail, Zūm).
   - Sanitizes raw descriptions using bounded `PlainDescription` parser (discards `<script>`, `<style>`, `<iframe>`, trims whitespace, bounds size).
   - Normalizes locations, work modes (`Remote`, `Hybrid`, `On-site`), and experience levels (`Intern`, `Entry / Junior`, `Senior / Lead`, `Staff / Principal`, `Management`).
   - Technical job classifier (`classify_tech_job`) filtering out non-technical roles (sales, recruiting, legal, PR) using strict title and department rules.
   - Technology tag extractor (`extract_tech_tags`) matching against canonical skill vocabulary.
   - Concurrent source polling with `ThreadPoolExecutor` and in-memory TTL caching (300 seconds).
   - Deterministic offline fallback fixtures allowing continuous functionality in offline or sandboxed testing environments.
   - Skill-to-vacancy matching engine (`match_job_to_skills`) calculating match score, matched competencies, missing skills, and actionable recommendations.
2. **`SqlAssessmentService` (`backend/services/sql_assessment_service.py`)**:
   - In-memory 6-question SQL foundations diagnostic question bank.
   - Deterministic answer evaluator with topic breakdown (`filtering`, `joins`, `aggregation`, `null_semantics`, `subqueries`), percentage score, and detailed explanations.
   - Completely stateless; zero database writes.
3. **`jobs_bp` (`backend/routes/jobs.py`)**:
   - `GET /api/jobs`: Search and filter live tech vacancies with pagination.
   - `GET /api/jobs/<source_key>/<provider_id>`: Individual vacancy inspection.
   - `POST /api/jobs/<source_key>/<provider_id>/match`: Candidate-to-job skill match against student profile or custom skills.
   - `POST /api/jobs/match-custom`: Custom job posting text analysis and match.
   - `GET /api/jobs/sources`: Configured source registry and provider metadata.
   - `GET /api/jobs/diagnostics/sql`: SQL foundations diagnostic question prompts and options.
   - `POST /api/jobs/diagnostics/sql/evaluate`: Evaluation of submitted diagnostic answers.
4. **`backend/app.py`**:
   - Clean registration of `jobs_bp` blueprint alongside existing blueprints.

---

## 5. Backend Logic Rejected
1. **Database Models (`job_comparison.py`, `assessment_attempt.py`, `candidate_evidence.py`, `candidate_resume.py`, `learning_roadmap.py`, `password_reset_token.py`)**:
   - Rejected because they introduce 6 new tables, violating the strict requirement to maintain exactly 11 PostgreSQL tables without schema mutations.
2. **Semantic Encoder (`semantic_encoder.py`)**:
   - Rejected because it relies on `onnxruntime`, `tokenizers`, and downloading a 90MB MiniLM model. Violates the requirement for self-contained, lightweight, sandbox-friendly execution.
3. **Resume Parsers & Evidence (`resume_evidence.py`, `resume_parser.py`)**:
   - Rejected because Phase 4 `ResumeExtractionService` already provides superior multi-format extraction and scoring.
4. **Learning Roadmaps (`learning_roadmap.py`, `roadmaps.py`)**:
   - Rejected because Phase 6 `RoadmapService` is more complete with full DAG dependencies and milestone timelines.
5. **Research Evaluation (`research_evaluation.py`)**:
   - Rejected because Phase 12.1 `RecommendationEvaluationService` is far more rigorous (32 tests, benchmark profiles, ranking metrics).
6. **Database Setup Script (`configure_local_db.py`)**:
   - Rejected because it attempts to execute `db.create_all()` and schema alterations.

---

## 6. Frontend UI Intentionally Skipped
As mandated by the user:
- `TechJobsPage.jsx` — Excluded.
- `JobAlignmentPage.jsx` — Excluded.
- `PracticalTasksPage.jsx` — Excluded.
- `LandingPage.jsx` — Excluded.
- `ForgotPasswordPage.jsx` & `ResetPasswordPage.jsx` — Excluded.
- `DashboardPage.jsx` modifications — Excluded; current dashboard preserved.
- `Layout.jsx` & navigation changes — Excluded.
- All friend UI CSS, styles, layouts, and components — Excluded.
- Frontend adaptation was limited strictly to adding minimal client helper methods in `frontend/src/services/api.js`.

---

## 7. Database Impact & Integrity Verification
- **Migrations:** Zero migrations created or executed.
- **DDL Execution:** Zero DDL executed.
- **Table Count:** **Strictly 11 tables** preserved in PostgreSQL.
- **Verified Public Schema Tables:**
  1. `canonical_skills` (30 rows)
  2. `career_preferences` (2 rows)
  3. `career_skills` (50 rows)
  4. `careers` (10 rows)
  5. `data_sources` (4 rows)
  6. `learning_resources` (33 rows)
  7. `skill_aliases` (32 rows)
  8. `skills` (7 rows)
  9. `student_profiles` (4 rows)
  10. `user_learning_progress` (2 rows)
  11. `users` (6 rows)

---

## 8. API Verification & Backward Compatibility
- **All Pre-Existing Endpoints Preserved:**
  - `/api/auth/*`
  - `/api/profile/*`
  - `/api/career-preferences/*`
  - `/api/skills/*`
  - `/api/careers/*`
  - `/api/learning-resources/*`
  - `/api/health`
- **New Endpoints Added under `/api/jobs`:**
  - `GET /api/jobs`
  - `GET /api/jobs/sources`
  - `GET /api/jobs/<source_key>/<provider_id>`
  - `POST /api/jobs/<source_key>/<provider_id>/match`
  - `POST /api/jobs/match-custom`
  - `GET /api/jobs/diagnostics/sql`
  - `POST /api/jobs/diagnostics/sql/evaluate`
- Zero naming conflicts; zero breaking changes.

---

## 9. Test Suite Verification Metrics
- **Previous Baseline:** 320 tests PASS
- **New Integration Tests Added:** 21 tests (`backend/tests/test_live_jobs_integration.py`)
- **Final Backend Regression:** **341 / 341 tests PASS (100% passing)**
- **Test Execution Time:** 62.08s
- **Frontend Production Build:** **PASS (exit code 0, 10.56s)** with Vite 5.4.21.

---

## 10. Security & Operational Assessment
- **IDOR Protection:** Match endpoints resolve skills from verified JWT token context or explicit payload without exposing other users' profiles.
- **SSRF Prevention:** Public source URLs are constrained to the hardcoded `SOURCE_REGISTRY`. Arbitrary outbound HTTP fetches to user-supplied hosts are forbidden.
- **XSS & Content Injection Prevention:** All vacancy HTML descriptions are stripped through the bounded `PlainDescription` HTML parser before returning to clients.
- **DoS Prevention:** Thread pools and HTTP downloads enforce strict byte limits (15 MB), description limits (60 KB), and timeouts (8s), with in-memory TTL caching (300s).

---

## 11. Git Status & Safety Compliance
- **Commit / Push Operations:** None executed.
- **Git Reset / Checkout / Restore / Clean / Stash:** None executed.
- **Working Tree:** All newly integrated services, routes, tests, and documentation remain intact as clean uncommitted changes.
