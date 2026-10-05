# Resume, job alignment and interface — 5 October 2026

This batch extends `c9d104a` without replacing the existing application. It adds
resume review/save and a shared responsive interface to the live-job, diagnostic
and roadmap workflow. Final submission is Thursday 8 October 2026.

## Install on the existing Windows project

Stop the running Flask process with Ctrl+C, then use the existing interpreter:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe .\backend\app.py
```

The new dependency is `pypdf==6.19.0`. Keep existing semantic dependencies, model
weights and private `backend/.env`. Starting the app creates `candidate_resumes`;
existing tables do not require an alteration. Open http://127.0.0.1:5000/app and
press Ctrl+F5. ONNX Runtime telemetry is disabled before runtime initialization
and through its documented API. The model setup download still needs the network;
subsequent inference uses local model files.

## Complete demonstration

1. Sign in and open **Resume & skills**. Upload a PDF, DOCX or TXT, or paste text.
   Read and correct the extracted draft; click **Save resume**. The persistent
   filename/status and saved version confirm success even if the native file
   picker resets to “No file chosen.” Extraction alone does not save a resume.
2. Add honest self-ratings. Add projects/certificates under the separate evidence
   tab and tag relevant skills. These records are explicitly unverified.
3. Open **Live opportunities** and refresh Canonical or Razorpay. Read each
   board's status. Search and open **View & compare** for a relevant posting;
   check employer/location/requirements and the employer source link.
4. Compare with keywords or keywords plus semantic suggestions. The saved
   alignment table separates resume mentions, ratings, project/certificate tags
   and diagnostic answers. Expand source passages and ambiguous context.
5. Assess Python, SQL or REST/HTTP from a matching skill card. Include a skipped
   topic and an incorrect answer in a synthetic demo attempt to show different
   actions. Open the roadmap and a linked course/reference.
6. Return to the original comparison and select the action to compare again with
   updated evidence. Save the new comparison. The original remains unchanged.

Use synthetic demonstration information, separate from research participants.
If a board cannot refresh, the previous cache remains available with its true
timestamp/status. A pasted description is also available under **Job alignment**.
Do not relabel pasted or cached data as a fresh successful live retrieval.

## What alignment means

The job extractor retains its ten concepts, keyword baseline and optional
pretrained MiniLM suggestions. The resume analyser uses only literal curated
names/aliases with word boundaries. Lines indicating learning, aspiration or
negative claims are held for manual review. This conservative rule can withhold
valid mixed statements; candidates can inspect the passage. It is not semantic
resume parsing, verification of work history or a calibrated ATS score.

Four source-coverage counts use explicitly named job concepts, including
preferred concepts. Semantic-only suggestions stay visible but are excluded
from these counts. Counts overlap and must not be summed into a percentage.
With no named concepts the UI shows an em dash. Missing resume mentions mean
only that no supported mention was found. An all-skipped diagnostic is not
counted as answered evidence. None of these counts establishes full job fit,
eligibility, years of experience, credential validity or hiring probability.

Resume text never creates skill ratings or changes diagnostic scores. The
roadmap still uses the existing topic-answer policy. New snapshot format
`candidate-evidence-v3` retains resume text/name/hash/version/time along with
the existing sources; old comparisons without resumes remain readable.
Policies are `resume-mentions-v1` and `source-coverage-v1`. Extraction settings
and research question definitions are unchanged.

## File and record behaviour

- Files are limited to 2 MB; extracted/saved text to 30,000 characters; minimum
  saved text is 40 characters. PDF extraction supports up to ten pages. Scanned
  images and encrypted PDFs require an independently prepared text alternative.
- DOCX reads the main document paragraphs/tables, not headers, images or text
  in every drawing. Always inspect the editable extraction preview.
- An isolated parser process has a ten-second timeout. ZIP/XML sizes are
  bounded; on POSIX the worker also has CPU/address-space limits. Windows uses
  the parent timeout without those POSIX resource limits.
- The original uploaded bytes are not stored. The reviewed plaintext is saved
  privately to the account and copied into that account's saved comparisons.
  This is plaintext database storage, not encryption at rest.
- Saving/removing requires the latest version. A conflict requires reloading
  and reviewing the saved text; stale requests cannot silently replace it.
- Removing the current resume clears its text but preserves a version tombstone
  and previous comparison snapshots. This is not an account-wide erasure tool.
- Unsaved drafts remain in the current tab only. Navigation back to the editor
  retains them; reload/logout warns about loss. A saved resume is loaded from
  the account. Authentication and owner isolation apply to every resume route.

## API

| Method/path | Input | Effect |
| --- | --- | --- |
| GET `/api/resume` | Authenticated account | Current saved text, version, mention analysis and catalogue |
| POST `/api/resume/extract` | Multipart `file` | Extraction preview; no save |
| PUT `/api/resume` | JSON `version`, `text`, `source_name` | Version-checked save |
| DELETE `/api/resume` | JSON `version` | Clear current text; retain old snapshots |
| DELETE `/api/skills/<id>` | Owned rating ID | Remove self-rating; old comparison snapshots remain |

## Technical checks and research status

On 5 October all 140 backend tests passed, including actual MiniLM inference,
resume format/limit handling, account isolation, stale version protection,
claim boundaries and snapshot preservation. The environment used Python 3.12
and SQLite; the user's Windows/PostgreSQL run is a separate local smoke check.
These tests verify software behaviour, not research accuracy or proficiency.

Independent content review, reference labels, practical-task outcomes and
recommendation utility remain pending. See `research/PILOT_PROTOCOL.md`. Keep
resume context constant across research conditions; the proposed pilot does
not isolate the benefit of the new resume parser or visual design.

Preserve private resumes and study records outside public Git commits. Use the
existing ignored `data/research/` folder for local study materials. Keep original
team attribution and commit this batch as a distinct portfolio contribution.
