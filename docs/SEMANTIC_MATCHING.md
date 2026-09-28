# Semantic skill matching — pasted job comparison

This milestone adds **Compare a job** to the candidate workspace. It connects a pasted
job description to saved skill claims, active project/certification submissions and
the latest submitted SQL diagnostic. It provides a keyword baseline and real local
inference with a pretrained Sentence Transformers model.

It does not fetch live vacancies, rank multiple jobs, train on candidate data or
establish research novelty. The next integration is a live-job connector feeding this
comparison pipeline with source and freshness metadata.

## Windows installation

Start from the completed `prajwal/candidate-evidence` branch (commit `a40cfa1`). Stop
Flask with Ctrl+C before applying the patch. Save the downloaded patch in the repository
root, then run:

```powershell
git switch prajwal/candidate-evidence
git switch -c prajwal/semantic-matching
git apply --ignore-space-change --check .\semantic_matching_v1.patch
```

If that check reports no errors:

```powershell
git apply --ignore-space-change .\semantic_matching_v1.patch
Remove-Item -LiteralPath .\semantic_matching_v1.patch
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-semantic.txt
.\.venv\Scripts\python.exe .\backend\scripts\setup_semantic_model.py
```

The setup script downloads approximately **91 MB** of model/tokenizer files from the
official Hugging Face model repository. It pins the revision, verifies SHA-256 hashes
and file sizes, then checks CPU inference. No Hugging Face API key is required for this
public model. Rerunning setup reuses verified files and replaces an incomplete or
incorrect download only after the replacement passes verification.

Expected final setup message:

```text
Model ready: CPU inference returned normalized 384-dimensional embeddings.
```

Model files go in `data/models/minilm-l6-v2/`, which is ignored by Git. They are not part
of the patch or commit. Install the optional semantic requirements into the same `.venv`
that runs Flask. No Node installation or frontend build is needed on Windows.

Now run tests and start Flask:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe .\backend\app.py
```

Expected after successful model setup: **62 tests, OK**, including both real-model
tests. If dependencies or model files are absent, two real-model tests are skipped;
that does not establish that semantic inference works. The other 60 tests cover the
application and keyword/policy behaviour. Tests use isolated SQLite, not your normal
PostgreSQL database.

On application restart, the existing `db.create_all()` setup creates the new
`job_comparisons` table. No existing table definition changes. Open
http://127.0.0.1:5000/app, press Ctrl+F5, sign in and choose **Compare a job**.

## Demonstration

Choose **Use example description**, retain **Keywords + semantic suggestions**, and
choose **Compare and save**. The example is fictional and deliberately contrasts
literal skill names with paraphrases:

| Example passage | Expected prototype output |
| --- | --- |
| Develop backend applications in Python. | Explicit Python mention. |
| Write relational queries to combine tables and summarize records. | SQL semantic suggestion, requiring review. |
| Build web endpoints that accept JSON requests and return responses over HTTP. | REST APIs semantic suggestion, requiring review. HTTP endpoints are not automatically proof of REST design. |
| Use Git to collaborate on source code. | Explicit Git mention. |
| Docker is a bonus. | Explicit Docker mention with optional/preferred wording. |
| No Java experience is required. | Excluded from automatic mapping; shown for manual review. |

With the pinned model and current policy, this example produces **3 named concepts**
and **2 suggested concepts**. Counts involving candidate claims or assessment records
depend on the signed-in account. An account with an existing SQL attempt sees its own
latest result; the application does not substitute the demonstration's 60% score.

Choose **Try keyword baseline** and save the prefilled form to see the three explicit
concepts without the two semantic suggestions. Each new save uses the current profile.
For a controlled baseline experiment, freeze the same candidate snapshot and job text
for both methods; the UI shortcut alone is not an experimental evaluation harness.

Open **Source and comparison method** to inspect the input, snapshot time, model
revision, policy version and threshold settings. The optional source link is stored
as a reference and is not fetched. Saved comparisons can be reopened after signing
out and in, without rerunning the model.

## Matching method

The current catalogue contains ten concepts: Python, SQL, REST APIs, Django, Flask,
PostgreSQL, Git, Docker, JavaScript and Java. Five have ESCO URIs checked against the
repository's processed ESCO skills data. The other five are explicit local concepts;
the code does not invent ESCO identifiers for them. This is a small curated vocabulary,
not complete integration of all ESCO/O*NET occupations and skills.

1. Preserve the original pasted text. Split the description into sentences/lines and
   short fragments; carry recognized Requirements and Preferred skills headings.
2. Find whole-word curated names/aliases. Java does not match JavaScript; SQL does not
   match the substring inside NoSQL or MySQL. Candidate tags use normalized full-name
   aliases rather than unconstrained substring matching.
3. In semantic mode, embed fragments and original skill descriptions with the pinned
   MiniLM model. Attention-mask mean pooling and L2 normalization produce sentence
   embeddings; their dot product is cosine similarity.
4. A fragment's best concept can become a **suggestion** when cosine is at least 0.58
   and its margin over the next concept is at least 0.08. These are uncalibrated
   prototype choices. They are not confidence estimates, probabilities or validated
   skill-match thresholds. At most one semantic suggestion is added per fragment.
5. Link each concept to canonicalized candidate skill ratings and evidence tags.
   Project text and certificate validity are not independently verified. Project
   descriptions are retained in the snapshot, but they are not automatically crawled
   or interpreted as verified proficiency.
6. Display the latest submitted SQL assessment separately. An all-skipped latest
   attempt remains unassessed; the matcher does not select the candidate's best score.
7. Preserve unmapped passages and candidate tags, and show negated statements for
   manual review. A missing record is treated as a need for evidence, not a demonstrated
   deficit. A mapped passage can still contain additional requirements that were missed.

Related technologies remain distinct: Django/Flask can be shown as related to Python,
and PostgreSQL as related to SQL. These relationships do not manufacture direct skill
claims. Required/optional labels describe recognized wording, not a complete logical
parser of hiring criteria. Compound alternatives, ambiguous wording, unsupported
headings, implicit requirements and out-of-vocabulary skills still require review.

Descriptions are limited to 8,000 characters and 60 fragments. Fragmentation retains
the text rather than silently discarding the tail. The encoder rejects inputs that
exceed its 256-word-piece limit. The initial use case is English backend job descriptions.

## Model and data provenance

| Item | Value |
| --- | --- |
| Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Revision | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` |
| Runtime | ONNX Runtime, CPU provider |
| Embedding size | 384 |
| Pooling | Attention-mask mean, followed by L2 normalization |
| Model status | Pretrained inference; no project-specific fine-tuning |
| Catalogue | `backend-skills-2026-09-27-v1` |
| Matching policy | `pasted-job-comparison-v1` |

The publisher's model card identifies the model as Apache-2.0. Model/tokenizer files
are downloaded from the publisher, not bundled into this repository. Setup records the
revision in its output; hard-coded expected digests in `semantic_encoder.py` protect
against incomplete or unexpected files. Runtime requests do not download models, call
external inference providers, fetch candidate URLs or send job/profile text elsewhere.

The existing ESCO/O*NET datasets provide vocabulary and occupational reference data.
They are not labelled candidate-job training examples. Before claiming a learned
improvement, create approved annotations, separate development and held-out evaluation
data, and compare methods on the same frozen inputs. Keep demonstration accounts out.

Primary references:

- Model card, pooling example and intended use: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- Sentence Transformers semantic search: https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html
- ONNX inference and pooling considerations: https://sbert.net/docs/sentence_transformer/usage/efficiency.html
- ESCO source attribution: European Commission, European Skills, Competences, Qualifications and Occupations: https://esco.ec.europa.eu/

## Persistence and API

Each comparison stores the original job input, all included active evidence details
and versions, skill claims, the selected SQL assessment result, and the comparison
output. Later profile edits or archiving do not modify an existing comparison. Snapshot
retention/deletion controls are future work; archiving a profile record does not erase
it from prior comparison snapshots.

Creation uses a per-candidate UUID submission key. An identical retry returns the same
saved comparison even if the profile has since changed. A retry with different input
returns 409. Opening a new form creates a new key. Reads are owner-scoped, and clients
cannot supply a score, owner or candidate snapshot. No update/delete route is exposed.

All endpoints below require authentication and use `Cache-Control: no-store`:

| Route | Behaviour |
| --- | --- |
| `GET /api/job-matches/metadata` | Vocabulary and model setup status; file presence is checked, with hashes verified on first model load. |
| `GET /api/job-matches` | Latest 30 comparison summaries for the current candidate. |
| `POST /api/job-matches` | Exact fields: `submission_id`, `title`, `description`, `source_url`, `mode`. Mode is `keyword` or `semantic`; source_url can be empty. Returns 201, or 200 for an identical retry. |
| `GET /api/job-matches/<id>` | Full saved comparison, including the frozen candidate snapshot; otherwise 404. |

Unavailable semantic inference returns 503. It is never silently relabelled as a
semantic result backed only by keywords. The user may explicitly select keyword mode.
Normal reauthentication resumes the pending action. Validation errors preserve form
text; a lost creation response can be retried with the same submission key. Navigating
away from edited input asks before discarding it. No draft autosave is provided.

## Verification and remaining limits

On 28 September 2026, all **62 backend tests** passed in the development environment,
including two checks against the downloaded model: normalized/padding-invariant
embeddings and the example SQL/REST paraphrases. Other new tests cover owner isolation,
snapshot immutability, retry behaviour, unknown skills, negation, optional wording,
explicit model failure and unchanged assessments/roadmaps.

The automated Chromium check uses real inference against an isolated SQLite server.
It covers example input, keyword/semantic modes, saved history, snapshot preservation,
source URL validation, injected session expiry, a deliberately lost save response,
escaped pasted HTML, missing-model UI, and links into existing SQL results/roadmaps.
Desktop and 390-pixel mobile layouts are checked for overflow and visually reviewed.
This does not validate Windows/PostgreSQL behaviour; perform the local smoke check.

These are software and demonstration checks. They are not a labelled benchmark,
participant study, proof of novelty or evidence of improved hiring outcomes. Ranking
metrics, threshold calibration, evidence-quality review, live-job ingestion and broader
skill/assessment coverage remain separate milestones.

## Commit after the local smoke check

Confirm that a semantic comparison saves, keyword mode differs as expected, a saved
comparison survives sign-out/sign-in, and the linked SQL result/roadmap remains intact.
Then commit the sixteen source/documentation files:

```powershell
git add .gitignore backend/app.py backend/models/job_comparison.py backend/requirements-semantic.txt
git add backend/routes/job_matches.py backend/scripts/setup_semantic_model.py
git add backend/services/job_matching.py backend/services/semantic_encoder.py backend/services/skill_catalog.py
git add backend/static/matching.js backend/static/workspace.js backend/static/workspace.css backend/templates/workspace.html
git add backend/tests/test_job_matching.py docs/SEMANTIC_MATCHING.md docs/ASSESSMENT_UI.md
git --no-pager diff --cached --stat
git commit -m "Add semantic job comparisons with saved evidence snapshots"
git push -u origin prajwal/semantic-matching
git --no-pager status
```

The downloaded patch, model weights and private `.env` are not part of this commit.
