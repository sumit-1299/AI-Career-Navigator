# Research evaluation: frozen job-skill extraction pilot

## What this milestone measures

**RQ1:** On a fixed set of engineering-related job descriptions, how does adding
semantic suggestions affect extraction of the ten supported skill concepts,
compared with the existing keyword/alias baseline?

The two executable methods are:

1. **Keyword baseline:** existing curated names/aliases and negation handling.
2. **Keywords + semantic suggestions:** the shipped hybrid method, using the same
   keyword rules plus the pinned MiniLM model and existing heuristic thresholds.

The second method is not a semantic-only ablation. This experiment uses an empty
candidate profile for both methods because candidate records do not affect the
current extracted job-skill set. It therefore does not test candidate proficiency,
hiring success, overall job ranking, the benefit of evidence-aware guidance,
roadmap outcomes, or research novelty. These distinctions must remain in the paper.

**RQ2, still untested:** Does adding independent assessment evidence and explicit
unknown/unverified states help reviewers make better skill-gap decisions than
self-reported profiles alone? That requires a separate evaluation with independently
reviewed candidate-task evidence and a predefined outcome. Do not claim that RQ1
answers RQ2. The SQL, Python and REST/HTTP six-question diagnostics remain draft content.
The separate [recommendation pilot protocol](research/PILOT_PROTOCOL.md) defines
RQ2 controls, practical-task references, outcome rubrics and collection forms.

## Team workflow

Use two reviewers with enough knowledge to interpret the ten skill concepts. They
should label independently, without model predictions or each other's labels. A
third reviewer resolves disagreements. Reviewer IDs such as R1/R2/R3 are enough;
keep identities/qualifications in your team's private study notes if needed.
Review declarations are self-attested, not technically authenticated human identity.
The system cannot guarantee blindness, independence, or expertise.

| Role | Work |
| --- | --- |
| Coordinator | Freeze the packet, retain identical copies, record the design and run commands |
| R1 | Label every case independently with supporting quotes |
| R2 | Label the same cases independently without viewing R1's file |
| R3 | Resolve disputed labels with both reviewers' notes and the frozen text |

One person can coordinate and also review if they have not inspected model outputs
for these cases. A person must not pretend to be two independent reviewers. No
participant recruitment or messages are sent by these tools.

## Step 1 — verify the tools

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe .\backend\scripts\research_evaluation.py smoke --out .\data\research\smoke-v1
```

This exercises both methods on the first six **AI-authored synthetic development
checks** and creates `report.md`, `results.json`, and `practice-packet.json` in the
output directory. The packet includes twelve practice cases. Its nominal split is
for exercising the tool, not an independently held-out research set. These labels
are software-check references, not human ground truth; never copy their metrics
into the paper as model quality. Research evaluation rejects synthetic packets.

No new packages are required if semantic matching already works. Smoke/evaluation
commands use the local model and do not contact employers or require a running
Flask server. The semantic model must be installed; there is no silent fallback.
If a run folder already exists, use a new name such as `smoke-v2` to preserve it.

## Step 2 — freeze real cached jobs

In the application, refresh both employer boards first. Then run:

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\research_evaluation.py export --size 24 --out .\data\research\pilot-v1.json
```

This reads only the shared live-job tables. It does not read candidate accounts,
projects, certificates, skill ratings or assessment results. It never modifies
tables and never fetches additional jobs. PostgreSQL must be available and your
existing private `backend/.env` must be configured.

The default pilot has **24 jobs: 12 development and 12 test**. This is a small
convenience sample suitable for checking feasibility before the expert review,
not a statistically representative market benchmark or enough labelled data to
justify fine-tuning a model.

Selection is fixed before predictions:

- Keep currently cached/listed postings whose titles contain engineer, engineering,
  developer, software, backend or Python. Seniority is not filtered; do not describe
  this as an exclusively junior-role dataset.
- Group exact normalized descriptions or identical normalized employer/title pairs.
  Connected components also join transitive duplicate relationships. Retain one
  deterministic representative per group before choosing the split.
- Use a declared seed, deterministic ordering and employer round-robin selection.
  If one board has fewer eligible groups, fill remaining slots from the other.
  Record actual employer counts and the complete selection rule.
- Put half the selected groups into development and half into test using a seeded
  hash ordering. A group appears in one split only. No model outputs influence
  selection or splitting.
- Retain source URL, posting version, source-update/fetch timestamps and content
  hashes. Export includes full plain text without silently truncating it.
- A full-dataset fingerprint binds text, source, split and selection metadata.
  Later provider refreshes do not change this file. Do not hand-edit sealed packets.
- The exporter reports stale cases. If stale sources are unsuitable, refresh and
  export a new version before anyone begins labelling. Do not replace cases after
  seeing model results just because they are hard.

Exact/title grouping does not detect all near-duplicate descriptions or shared
employer templates. Inspect the sample before labelling, record this limitation,
and do not claim an independent test set if near-duplicates or prior developer
exposure compromise it. If fewer than 24 groups exist, the exporter stops with a
count; refresh or deliberately choose a smaller size and report that change.

## Step 3 — label in the browser

```powershell
Start-Process .\research\review.html
```

This local page is separate from the candidate app. No Flask route or login is
needed. It sends no requests and does not upload files. It is tested in Chromium;
use Chrome or Edge on Windows. Keep `review.html`, `review.js`, and `review.css`
together in the repository. It uses the browser's Web Crypto API to check the
packet fingerprint; if opening local files is restricted by your browser, use a
local static server from the project root:

```powershell
.\.venv\Scripts\python.exe -m http.server 8001 --bind 127.0.0.1
```

Then open http://127.0.0.1:8001/research/review.html and stop the server afterwards.
Do not bind this project-root server to a public interface; it serves local files.

R1 loads `pilot-v1.json`, enters `R1`, and labels the cases. R2 independently loads
an identical copy and enters `R2`. The page shows frozen text and source information,
not model predictions, anchors, scores or development/test assignments. The split
is still present in the JSON and not technically secret.

For each job and each concept:

| Label | Definition |
| --- | --- |
| Present | A skill the candidate is expected or preferred to use, explicitly or by an unambiguous paraphrase |
| Absent | The role does not support that skill, the mention is only company background, or it is explicitly not required |
| Uncertain | Ambiguous wording prevents a defensible decision; explain the ambiguity |

Required and preferred skills both count as present for this binary extraction
task. This does not measure correct importance/severity classification. A job that
expects a technology in the responsibilities section can support a present label
without using the word "required". Do not treat corporate background or benefits as
candidate requirements. Read clauses separately, including mixed negation.

Use this vocabulary consistently:

| Concept | Review distinction |
| --- | --- |
| Python | Do not infer solely from Django/Flask; explicit Python work supports it |
| SQL | Clear relational query work may support it; a database product name alone does not |
| REST APIs | Named REST or sufficiently explicit REST architecture supports it; generic HTTP/JSON alone can be uncertain |
| Django / Flask | Distinct frameworks; do not interchange them or add implied parent-language labels |
| PostgreSQL | PostgreSQL/Postgres; generic databases do not uniquely establish it |
| Git | Git or sufficiently distinctive distributed version-control work; generic collaboration is not enough |
| Docker | Docker-specific work; generic containers may use other tools |
| JavaScript / Java | Distinct concepts; Java inside JavaScript is not a match |

Use uncertain when a technology-specific mapping would require an unjustified
assumption. Unknown/out-of-vocabulary technologies are not automatically mapped
to one of these ten skills. No label describes a candidate's ability.

Add brief supporting quotes with skill names for present labels and explanations
for uncertain ones. After reading a case, **Mark remaining blank labels absent**
can save clicks. This is an explicit reviewer action, never an automatic default.
Click **Confirm this case reviewed**. Editing a label or note reopens the case.

Download drafts whenever you pause: nothing is automatically saved in the browser.
To resume, load the original packet and then the downloaded draft. After all cases
are confirmed, check the human-review declaration and download the completed file.
Keep R1 and R2 files unchanged. Move/rename them to:

```text
data/research/review-R1.json
data/research/review-R2.json
```

The filename may change; do not edit the JSON contents. Generated packets, reviews
and results under `data/research/` are ignored by Git. Store them privately with a
backup; Git is not their backup. Code, protocol and explicitly synthetic fixtures
under `research/` are tracked for portfolio review.

## Optional development diagnostic using an AI-assisted draft

When independent human labels are not available, an explicitly AI-assisted draft
can support preliminary debugging. This is a separate workflow, not a replacement
for Steps 4–5. Use the original `pilot-v1.json` and `pilot_v1_AI_DRAFT.json` supplied
for that exact packet, or a saved draft that preserves its AI-provenance markers.
Leave the human-review declaration unchecked. Do not rename duplicate copies as
R1/R2 or claim that assisted review was blind independent annotation.

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\research_evaluation.py diagnose --dataset .\data\research\pilot-v1.json --draft .\data\research\pilot_v1_AI_DRAFT.json --out .\data\research\ai-diagnostic-v1
```

This command always uses **development cases only** (12 in the default packet).
It has no test-split option. Both matchers receive the same frozen descriptions,
and neither candidate records nor the live database are read. The installed local
MiniLM model and existing semantic dependencies are required; there are no new
packages for this command. An unavailable model fails the run without writing a
partial success report. Existing output directories are never overwritten.

The output folder contains:

- `report.md`: prominently marked AI-assisted diagnostic, method agreement with
  the draft, positive/uncertain skill support, and disagreements to inspect.
- `results.json`: a distinct `career-skill-ai-diagnostic-v1` schema, AI reference
  labels, draft fingerprint, predictions, source/model hashes, mapped passages
  and draft notes. It does not contain human inter-reviewer agreement statistics.

Precision/recall/F1 are relative to the **unvalidated AI draft**. A disagreement
may reflect a matcher error, an AI-label error or an unclear annotation policy.
These figures are not independently validated accuracy, proficiency, suitability
or proof of novelty. No sampling interval can establish validity of the AI labels;
this report therefore does not present one. Uncertain cells are excluded equally
for both methods, and zero-positive skills must not be treated as validated.

Inspect the disagreement passages before modifying extraction logic. Save a new
versioned run after any development change. Nothing in `diagnose` trains or tunes
the model or changes your packet/review files. If test cases or labels influenced
your choices, obtain a fresh untouched test set for final evaluation.

Known AI-provenance markers at the review level or in individual annotations are
rejected by `evaluate` and `prepare-adjudication`, even if completion/declaration
checkboxes are changed. This check preserves declared provenance; it cannot
authenticate a human reviewer or detect undisclosed AI assistance.

## Step 4 — reconcile reviewer disagreements

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\research_evaluation.py prepare-adjudication --dataset .\data\research\pilot-v1.json --review-a .\data\research\review-R1.json --review-b .\data\research\review-R2.json --out .\data\research\adjudication-v1.json
```

If there are no disagreements, no adjudication file is needed. Otherwise R3 opens
`adjudication-v1.json` in the same review page. Only disputed cases appear. Agreed
labels are locked; R3 resolves conflicting labels using the text and both reviewers'
notes. R3 can choose uncertain where evidence remains insufficient. Download the
completed adjudication and move/rename it to `data/research/review-R3.json`.

Adjudication is bound to hashes of the two original review files in their supplied
order. Re-exporting/changing either original review requires a new adjudication
packet. The evaluator rejects incomplete reviews, wrong packets, unresolved
conflicts, reused reviewer IDs or changed agreed labels.

## Step 5 — evaluate development, then freeze and evaluate test

Without adjudication:

```powershell
.\.venv\Scripts\python.exe .\backend\scripts\research_evaluation.py evaluate --dataset .\data\research\pilot-v1.json --review-a .\data\research\review-R1.json --review-b .\data\research\review-R2.json --split development --out .\data\research\development-v1
```

If adjudication was required, add:

```text
--adjudication .\data\research\review-R3.json
```

Use development errors for improvements. Record the final design/settings in Git
before running test. Then use the same evaluation command with `--split test` and
`--out .\data\research\test-v1`. Do not change thresholds, aliases or logic based on
test errors and still call that same test set independently held out. Create a new
untouched test set or label later results exploratory. The tool does not enforce
researcher blindness or prevent repeated test inspection.

Both methods receive the identical frozen description. The evaluator uses the
shipping matcher and fixed 300-fragment live-job limit. An input/model error aborts
the run; it never silently excludes difficult jobs or reports only a surviving
method. Output directories are not overwritten. A successful run creates:

- `report.md`: readable method comparison, coverage and limitations.
- `results.json`: exact predictions, resolved labels, per-skill counts, false
  positives/negatives with mapped passages, manual-review passages, fingerprints,
  model revision, dependency versions and code-file hashes.

The Git commit plus actual source hashes record modifications present at runtime;
file hashes can differ across Windows/Linux line endings. Snapshot the code used
for an experiment. Runs do not automatically train, tune or publish anything.

## Metrics and interpretation

For each job-skill cell with a resolved present/absent label, count true positives,
false positives, false negatives and true negatives. Uncertain cells are excluded
for both methods using the identical mask. Report the fraction of scored cells and
uncertain counts; high F1 on a small resolved subset is not full coverage.

Micro precision/recall/F1 pool counts across resolved cells. Macro F1 averages the
ten per-skill F1 values equally. Undefined precision/recall/F1 use zero, including
skills with no positive support; always inspect per-skill support alongside macro
F1. Exact-set accuracy is reported only for jobs with all ten labels resolved.
There is no headline overall "accuracy" dominated by absent-skill true negatives.

The evaluator reports the hybrid-minus-keyword micro-F1 difference and a descriptive
95% percentile bootstrap interval (2,000 paired resamples of whole jobs/groups,
fixed seed). The 12-job default test sample is small and clustered by employer;
these intervals are unstable and are not a market-level significance claim.

Reviewer agreement is measured before adjudication on the complete packet, using
three categorical labels: present, absent and uncertain. Report raw agreement and
Cohen's kappa with disagreement counts. A single-category degeneracy yields null
kappa. Many absent labels can dominate these pooled values; they do not establish
annotation validity. Disagreement notes and adjudication remain necessary.

Method references (primary documentation):

- Precision, recall, F-score and micro/macro conventions:
  https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_fscore_support.html
- Cohen's kappa:
  https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html
- Data leakage and separation of evaluation data:
  https://scikit-learn.org/stable/common_pitfalls.html

The evaluator implements these simple counts with the standard library; it does
not add scikit-learn as an application dependency.

## What can go in the report and paper

Before human annotation, report only the implemented evaluation method and pending
results. Once reviewed data exists, report sample size, source/seniority mix,
selection dates/rules, annotation instructions, reviewer qualifications, uncertainty
coverage, disagreement handling, exact settings and measured results including
negative findings. Describe the sample as a pilot. Do not replace observed results
with synthetic demo numbers or imply that the pretrained model was trained here.

RQ1 results can support a bounded claim about extraction on this sample. A claim
about evidence-aware guidance needs RQ2 evidence; a novelty claim needs a verified
literature comparison. O*NET/ESCO are reference vocabularies, not labelled
candidate-job training data. A future fine-tuning dataset would require enough
independent reviewed examples and a separate untouched evaluation set.
