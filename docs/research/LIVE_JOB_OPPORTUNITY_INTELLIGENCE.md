# Live Job Opportunity Intelligence & Career Action Center

## 1. Objective

Phase 12 Module 12.2 introduces the **Live Job Opportunity Intelligence & Career Action Center** for AI Career Navigator. The primary objective is to bridge student career planning with actual market opportunities by orchestrating live employer postings with the platform's multi-layered career intelligence engines.

Rather than treating job search as an isolated listing directory, the Action Center transforms every live posting into an actionable pedagogical roadmap. Students can instantly evaluate how their current profile aligns with an active vacancy, identify precise skill gaps, explore prioritized return-on-investment (ROI) learning paths, review aligned portfolio capstones, inspect market demand signals, map multi-hop career trajectory transitions, and practice technical interview simulations tailored to the role.

> [!IMPORTANT]
> **Educational Decision Support Disclaimer**:
> The live-job opportunity layer provides job listings and deterministic skill alignment. It does not guarantee employment or placement.

---

## 2. Architecture & Orchestration

The module follows a strictly decoupled, modular orchestration architecture. Rather than implementing redundant scraping, matching, or recommendation logic, `JobActionCenterService` serves as a read-only coordinator integrating seven verified services:

```
                      +---------------------------------------+
                      |         Live Job Postings             |
                      | (Arbeitnow / Mock Fallback Cache)     |
                      +-------------------+-------------------+
                                          |
                                          v
+------------------------+    +-----------------------+    +------------------------+
|   Candidate Profile    |--->|  JobActionCenter      |<---|    Career Model        |
| (Database / Custom)    |    |  Orchestration Service|    | (10 Canonical Tracks)  |
+------------------------+    +-----------+-----------+    +------------------------+
                                          |
        +---------------------------------+---------------------------------+
        |                 |               |                |                |
        v                 v               v                v                v
+---------------+ +---------------+ +------------+ +---------------+ +---------------+
| Skill ROI     | | Portfolio     | | Industry   | | Multi-Hop     | | Interview     |
| Engine        | | Capstones     | | Demand     | | Trajectory    | | Readiness     |
| (Phase 11.1)  | | (Phase 11.2)  | | (Phase 11.4| | (Phase 11.5)  | | (Phase 11.6)  |
+---------------+ +---------------+ +------------+ +---------------+ +---------------+
        |                 |               |                |                |
        +---------------------------------+---------------------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |     Synthesized Career Action Plan    |
                      |   - Vacancy Match vs Career Readiness |
                      |   - Prioritized Skill ROI Actions     |
                      |   - Targeted Portfolio Capstone       |
                      |   - Advisory Next Steps Checklist     |
                      +---------------------------------------+
```

### Component Roles:
1. **LiveJobsService**: Ingests, normalizes, caches, and matches live vacancy data.
2. **Deterministic Career Mapper**: Aligns vacancy job titles and tech tags with canonical career tracks.
3. **SkillRoiService (Phase 11.1)**: Computes marginal readiness gain and ROI tier for missing vacancy skills.
4. **PortfolioProjectService (Phase 11.2)**: Identifies capstone projects that tangibly demonstrate missing skills.
5. **IndustryDemandService (Phase 11.4)**: Provides contextual market temperature and growth indicators.
6. **CareerTrajectoryService (Phase 11.5)**: Evaluates multi-hop transition feasibility and bridge skills.
7. **InterviewSimulationService (Phase 11.6)**: Connects vacancy tech requirements to interview simulations.

---

## 3. Live Jobs Source Layer

The live jobs ingestion layer (`LiveJobsService`) operates through a clean provider abstraction:
- **Primary Source (`arbeitnow`)**: Integrates with the Arbeitnow job board API, supporting pagination, remote/hybrid filtering, and keyword search.
- **Local Fallback Cache**: Provides deterministic offline datasets ensuring high reliability during network downtime or test environments.
- **Normalized Schema**:
  - `provider_id`: Unique identifier within the source provider.
  - `title`: Sanitized job title.
  - `employer`: Company or organization name.
  - `location`: Geographical location or "Remote".
  - `work_mode`: Categorized into `REMOTE`, `HYBRID`, or `ON_SITE`.
  - `experience_level`: Categorized into `ENTRY`, `MID`, `SENIOR`, or `ANY`.
  - `tech_tags`: Canonicalized technical skills extracted from job metadata and description.
  - `description`: Plain-text sanitized job description (HTML tags stripped).
  - `url`: Direct source posting URL.

---

## 4. Job Matching Engine

The matching engine deterministically compares candidate skills against vacancy requirements:
- **Normalization**: All skills undergo lowercase folding and canonical alias resolution via `normalize_skill_name`.
- **Set Overlap Calculation**:
  $$\text{Matched Skills} = \text{Candidate Skills} \cap \text{Job Tech Tags}$$
  $$\text{Missing Skills} = \text{Job Tech Tags} \setminus \text{Candidate Skills}$$
- **Deterministic Match Score**:
  $$\text{Match Score} = \begin{cases} 100.0 & \text{if } |\text{Job Tech Tags}| = 0 \\ \min\left(100.0, \text{round}\left(\frac{|\text{Matched Skills}|}{|\text{Job Tech Tags}|} \times 100, 1\right)\right) & \text{otherwise} \end{cases}$$
- **Score Distinction**:
  - **Job Match Score**: Direct, vacancy-specific keyword and tag overlap (0%–100%).
  - **Career Readiness Score**: Comprehensive multi-skill proficiency across the complete career track curriculum.

---

## 5. Action Center Orchestration

The `JobActionCenterService.get_action_center` method coordinates all intelligence layers:
1. Validates the `source_key` and fetches the job record via `LiveJobsService`.
2. Resolves candidate skills from either explicit input (`custom_skills`) or the authenticated user's database profile (`Skill.query`).
3. Executes deterministic job skill matching.
4. Performs career mapping to find the canonical IT track.
5. Gathers enriched intelligence: Skill ROI, Capstone Recommendations, Market Demand, Career Trajectory, and Interview Readiness.
6. Synthesizes an advisory "What Should I Do Next?" action checklist.

---

## 6. Skill ROI Integration (Phase 11.1)

When a vacancy is successfully mapped to a canonical career track, missing skills are cross-referenced with `SkillRoiService`:
- Missing skills obtain their `roi_tier` (`QUICKEST_WIN`, `HIGH`, `MEDIUM`, `LOW`).
- Provides `marginal_readiness_gain` (+% boost toward career qualification).
- Estimates required study hours.
- Prioritizes skills in the Action Center UI so students tackle the highest-leverage gaps first.

---

## 7. Portfolio Capstone Integration (Phase 11.2)

To move beyond theoretical study, the Action Center queries `PortfolioProjectService`:
- Recommends capstones specifically tailored to the mapped career track.
- Automatically identifies which project addresses the missing skills of the specific job vacancy (`addresses_missing_skills`).
- Presents concrete deliverables (e.g., GitHub repository, deployed API, architecture diagram) that the candidate can showcase to employers.

---

## 8. Deterministic Career Mapping

Live job postings feature varied, non-standardized titles. `JobActionCenterService.map_job_to_career` applies deterministic pattern matching to map vacancies into one of the 10 canonical database career tracks:

| Career ID | Canonical Career Title | Primary Title Patterns & Tech Signals |
|---|---|---|
| 1 | Software Developer | Software Engineer, Backend Developer, Python/Java/Go |
| 2 | Web Developer | Frontend Developer, React, Vue, Angular, Fullstack |
| 3 | Data Analyst | Data Analyst, BI Analyst, SQL, Tableau, Power BI |
| 4 | Data Scientist | Data Scientist, Deep Learning Scientist, Statistics |
| 5 | AI/ML Engineer | Machine Learning Engineer, AI Engineer, NLP, PyTorch |
| 6 | Cloud Engineer | Cloud Architect, AWS, Azure, GCP, Infrastructure |
| 7 | DevOps Engineer | DevOps, SRE, Site Reliability, CI/CD, Kubernetes |
| 8 | Cybersecurity Analyst | Security Engineer, Infosec, SOC Analyst, AppSec |
| 9 | Network Engineer | Network Administrator, Sysadmin, CCNA, Routing |
| 10 | Database Administrator | DBA, Database Engineer, PostgreSQL, Database Reliability |

### Fallback Guarantee:
If a vacancy does not match any canonical title pattern and lacks required tech tags (e.g., Sales, HR, or non-technical roles), the service returns an explicit fallback:
```json
{
  "status": "unavailable",
  "career_id": null,
  "career_title": null,
  "confidence": "NONE",
  "message": "Career mapping unavailable"
}
```
The Action Center gracefully renders the job matching results while safely omitting career-specific modules.

---

## 9. Industry Demand Benchmarking (Phase 11.4)

When available, market demand benchmarks are surfaced from `IndustryDemandService`:
- Overlapping high-demand skills between the vacancy and current market indicators.
- Overall market growth temperature (`HIGH_GROWTH`, `STEADY_DEMAND`, `BALANCED`).

> [!WARNING]
> **Research Provenance Notice**:
> Industry demand signals remain DEMO / SAMPLE / PROTOTYPE benchmarks and must not be interpreted as live labor-market ground truth.

---

## 10. Multi-Hop Career Trajectory (Phase 11.5)

For students transitioning into the vacancy's target role from a different primary career track (e.g., Software Developer transitioning to DevOps or Cloud Engineer), `CareerTrajectoryService` evaluates:
- Multi-hop transition feasibility score.
- Bridge skills required for the pivot.
- Progressive career milestone roadmap.

---

## 11. AI Interview Simulation Integration (Phase 11.6)

The Action Center seamlessly integrates with `InterviewSimulationService`:
- Links the active vacancy directly to technical interview simulation for the mapped career track.
- Recommends tailored technical knowledge checks and interview practice scenarios.

---

## 12. Security Architecture

1. **Path Traversal Defense**: The `provider_id` route parameter uses `<path:provider_id>` with rigorous sanitization to prevent directory traversal attacks.
2. **Safe Deserialization**: All JSON payloads are parsed using `request.get_json(silent=True)`, gracefully handling malformed input.
3. **SSRF & Network Isolation**: The live-jobs service restricts outbound network calls to whitelisted provider domains and incorporates deterministic local fallback.
4. **Authentication & Authorization**: Supports optional JWT authentication (`verify_jwt_in_request(optional=True)`). Authenticated users automatically link their stored skill profiles, while guest users can supply arbitrary custom skills without authentication bypass risks.
5. **No Data Tampering**: Client-submitted skills are treated as ephemeral search filters and are never written to other users' profiles.

---

## 13. Performance & Caching

- **In-Memory Job Cache**: Live postings fetched from external APIs are cached with TTL to minimize redundant upstream requests.
- **Sub-100ms Orchestration**: Because all underlying intelligence engines (ROI, Portfolio, Demand, Trajectory) execute deterministic algorithms over indexed relational schemas or in-memory benchmarks, composite Action Center queries complete in under 50ms.
- **Pagination & Throttling**: Job listing queries enforce page size constraints (`page_size` max 50) to prevent memory ballooning.

---

## 14. Database Boundary & Zero Schema Mutation

The Action Center strictly adheres to read-only boundaries:
- **Table Count**: Preserves the exact PostgreSQL baseline of **11 tables**:
  - `canonical_skills`, `career_preferences`, `career_skills`, `careers`, `data_sources`, `learning_resources`, `skill_aliases`, `skills`, `student_profiles`, `user_learning_progress`, `users`.
- **Zero Schema Migrations**: Zero Alembic/Flask-Migrate revisions added.
- **Zero DDL**: No temporary tables or table alterations.
- **Zero Persistent Writes**: Ingested vacancies, matching scores, and action plans are generated transiently on read and are never persisted to the relational database.

---

## 15. Limitations

1. **Third-Party Job Availability**: Live job listings depend on upstream external APIs or curated cache snapshots.
2. **Deterministic Heuristics**: Job-to-career mapping relies on keyword heuristics and canonical skill overlap; highly novel, non-standard corporate job titles may trigger the "Career mapping unavailable" fallback.
3. **Self-Reported Skill Alignment**: Match calculations reflect candidate-reported or profile-stored skills rather than verified external credentials.

---

## 16. Research Boundary & Pedagogical Scope

Phase 12.2 is designed strictly as an educational decision support system. The module explicitly rejects predictive placement claims:
- No claims of "guaranteed placement", "guaranteed interview", or "will definitely get".
- Recommendations are framed as non-prescriptive, student-centric guidance (e.g., *"Recommended next step"*, *"Priority skill gap"*, *"Consider applying if this fits your goals"*).
- Industry demand signals are demarcated as prototype research benchmarks.
