# Context and REST wording correction

This change follows the AI-assisted development diagnostic. It corrects two
observed disagreements without training or fine-tuning MiniLM, changing embedding
thresholds, or running predictions on the packet's test jobs.

## Behaviour

- `HTTP/REST`, including case and spacing variants such as `HTTP / REST`, is a
  curated REST API alias. Generic HTTP, JSON, APIs or the everyday word "rest"
  do not become keyword matches. Semantic suggestions remain a separate channel.
- Recognized company-background and benefits sections, explicit company
  statements and narrow project-portfolio wording are routed to manual review
  when no direct candidate-work cue is present. No employer name or case ID is
  hard-coded in the rule.
- Candidate references, imperative duties, qualifications and recognized role
  headings preserve role-specific evidence. An explicit candidate clause can be
  separated from a company statement in the same sentence.
- Excluded text remains visible with a reason. It is filtered before both keyword
  matching and semantic encoding so embeddings do not silently restore it.
- Existing negation handling remains conservative. General mixed negation is not
  solved by this change. Unknown headings, mixed subjects, broad team/technology
  descriptions and implicit duties can still require human interpretation.

These rules recognize some wording patterns; they do not fully understand who
uses every technology. In particular, "we use Python" outside a recognized
background section is not automatically suppressed because it can describe the
candidate team's work. Review the preserved source text.

## Versions and saved comparisons

New results include `extraction_version: skill-extraction-context-v2`.
Pasted comparisons use `pasted-job-comparison-v2`. Live comparisons retain their
`live-job-comparison-v1` source/input policy and carry the new extraction version
separately. Both versions are visible in the source/method details.

The ten concept IDs, labels and annotation definitions are unchanged, so the
frozen `backend-skills-2026-09-27-v1` vocabulary remains compatible. The additional
alias is recorded by the new extraction version and source-file fingerprints.
No dataset fingerprint or reference label was edited to accommodate the change.

Previously saved comparisons keep their original result snapshots. Create a new
comparison to use the new rules; reopening an old result does not rerun it. The
UI supports snapshots without the new extraction-version or reason fields.

## Development observations

The exact same frozen dataset and AI draft were used before and after the change.
Only the 12 development jobs were scored: 10 Canonical and 2 Razorpay postings.
There were 120 possible job-skill cells, including 3 uncertain AI labels excluded
for both methods. The remaining 117 cells contained 11 positive draft labels.

| Method | Before F1 vs AI draft | After F1 vs AI draft | Before method-only / draft-only cells | After method-only / draft-only cells |
| --- | ---: | ---: | ---: | ---: |
| Keyword baseline | 0.9091 | 1.0000 | 1 / 1 | 0 / 0 |
| Keywords + semantic suggestions | 0.9091 | 1.0000 | 1 / 1 | 0 / 0 |

- `job-003`: the optional networking phrase `HTTP/REST` now supports REST APIs.
- `job-011`: the company-wide Python project statement is retained for manual
  review instead of being counted as a candidate requirement for the Rust role.

**These are development results against unvalidated AI draft labels.** The same
disagreements guided the rule changes. Perfect agreement here is not independent
validation or evidence of generalization. Both methods still produce identical
skill sets, so this run does not demonstrate a semantic advantage. SQL, Django,
Flask, Git and JavaScript have no positive resolved draft labels in this subset.
A broader independent human-labelled set is needed to evaluate those concepts.

Dataset fingerprint:
`33ea2f1ed0540a91a449c24de2b4692a9ae7e8f0314cb4733e0b2189ef9a4d04`

AI draft hash:
`bf87e10b290bb1a724034b2c9a64c276bb7fcf01cb54c3d52c9d27f1c8cee9f8`

## Local check and reproduction

After applying the patch, run the existing backend suite. Tests use isolated
SQLite rather than your PostgreSQL application data:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -q
```

Development verification passed **122 tests**, including actual local MiniLM
inference. The new regression checks cover alias boundaries, section changes,
candidate/team counterexamples, mixed company/candidate clauses, long-fragment
context, exclusion before semantic encoding, API persistence and version metadata.
Browser checks cover visible review reasons, escaped text, legacy-shaped saved
results and desktop/mobile overflow. These are software checks, not research
validation.

Keep the earlier run. Generate a distinctly named new development diagnostic:

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\research_evaluation.py diagnose --dataset .\data\research\pilot-v1.json --draft .\data\research\pilot_v1_AI_DRAFT.json --out .\data\research\ai-diagnostic-context-v2
```

Open the new `report.md` and retain `results.json`, which records the extraction
version and source/model fingerprints. A different or edited AI draft can produce
different scores; do not edit labels to match the numbers above. The command
refuses to overwrite existing output folders.

Restart Flask and hard-refresh the candidate workspace. In **Compare a job**,
use this fictional description with either method:

```text
About us:
Our company develops Python products.
Responsibilities:
Build services using HTTP/REST and Git.
Preferred skills:
Docker.
```

Expected named skill cards: **REST APIs, Git, Docker**. The Python company
statement appears under **Read these passages manually**, with its context reason.
The original SQL assessment and candidate evidence still supply their own records;
the matcher does not create or change proficiency scores.
