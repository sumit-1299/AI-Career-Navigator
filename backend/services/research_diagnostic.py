"""Development-only comparison against declared AI draft labels, not human truth."""
from collections import Counter
from hashlib import sha256

from services.research_evaluation import (KEYS, LABELS, METHODS, REVIEW_SCHEMA, ROOT,
    digest, is_ai_assisted_review, run_evaluation, validate_dataset)

REFERENCE_STATUS = 'ai_assisted_draft_unvalidated'


def validate_ai_draft(dataset, draft):
    if not isinstance(draft, dict) or draft.get('schema_version') != REVIEW_SCHEMA:
        raise ValueError('Choose the AI-assisted saved review JSON, not the original dataset or a report.')
    if draft.get('dataset_id') != dataset['dataset_id'] or draft.get('dataset_fingerprint') != dataset['fingerprint']:
        raise ValueError('AI draft belongs to a different dataset or dataset version.')
    if not is_ai_assisted_review(draft):
        raise ValueError('This diagnostic requires explicitly declared AI-assisted provenance.')
    if draft.get('kind') != 'independent' or draft.get('complete') is not False or draft.get('without_model_predictions') is not False:
        raise ValueError('Use the saved AI draft with complete=false and without_model_predictions=false; leave the human-review declaration unchecked.')
    required = {case['id'] for case in dataset['cases']}
    rows = draft.get('annotations')
    if not isinstance(rows, list):
        raise ValueError('AI draft annotations are missing.')
    references = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('case_id'), str) or row['case_id'] not in required or row['case_id'] in references:
            raise ValueError('AI draft contains an unknown or duplicate case.')
        labels = row.get('labels')
        if not isinstance(labels, dict) or set(labels) != set(KEYS) or any(not isinstance(value, str) or value not in LABELS for value in labels.values()):
            raise ValueError('The AI draft must label all ten concepts present, absent or uncertain for every case.')
        notes = row.get('notes')
        if not isinstance(notes, str) or len(notes) > 5000:
            raise ValueError('AI draft notes must be text under 5,000 characters.')
        if any(value in {'present', 'uncertain'} for value in labels.values()) and not notes.strip():
            raise ValueError('Keep supporting notes for present and uncertain AI draft labels.')
        references[row['case_id']] = dict(labels)
    if set(references) != required:
        raise ValueError('The AI draft is missing cases from the original packet.')
    return references


def run_diagnostic(dataset, draft, runner=None):
    validate_dataset(dataset)
    if dataset['kind'] != 'live_job_pilot':
        raise ValueError('Use smoke for synthetic checks; diagnose requires frozen live-job text.')
    references = validate_ai_draft(dataset, draft)
    # No split option: this path must not inspect test predictions during development.
    report = run_evaluation(dataset, references, 'development', runner=runner,
                            reference_status=REFERENCE_STATUS)
    report['schema_version'] = 'career-skill-ai-diagnostic-v1'
    report['independent_human_validation'] = False
    report['draft_sha256'] = digest(draft)
    report.pop('review_hashes')
    report.pop('agreement')
    report['reference_labels'] = report.pop('gold')
    # A sampling interval cannot quantify error or bias in the AI labels. Keep the
    # descriptive difference only; do not publish a bootstrap interval for this mode.
    diff = report.pop('paired_difference')
    report['comparison'] = {'hybrid_minus_keyword_micro_f1': diff['delta_micro_f1'],
        'meaning': 'Difference in agreement with unvalidated AI labels; not a model-quality or significance claim.'}
    notes = {row['case_id']: row['notes'] for row in draft['annotations']}
    disagreements = []
    for row in report.pop('errors'):
        row['reference_label'] = row.pop('gold')
        row['difference'] = 'method_only' if row.pop('error') == 'false_positive' else 'draft_only'
        row['draft_notes'] = notes[row['case_id']]
        disagreements.append(row)
    report['disagreements_with_ai'] = disagreements
    selected = [case for case in dataset['cases'] if case['split'] == 'development']
    report['development_case_ids'] = [case['id'] for case in selected]
    report['test_cases_not_scored'] = sum(case['split'] == 'test' for case in dataset['cases'])
    report['development_employer_counts'] = dict(Counter(case['source'].get('employer', 'unknown') for case in selected))
    report['draft_label_counts'] = dict(Counter(value for case in selected for value in references[case['id']].values()))
    report['skills_without_positive_draft_labels'] = [key for key in KEYS if not any(references[case['id']][key] == 'present' for case in selected)]
    report['interpretation'] = ('PRELIMINARY AI-ASSISTED DEVELOPMENT DIAGNOSTIC. '
        'Scores describe agreement with an unvalidated AI draft, not accuracy against independent human reference labels. '
        'A disagreement can be a matcher error, a draft-label error, or an ambiguous policy. '
        'No model is trained, thresholds tuned, or test predictions generated. '
        'This does not validate candidate proficiency, job ranking, roadmap benefit, or research novelty.')
    path = 'backend/services/research_diagnostic.py'
    # Use bytes so the recorded hash has the same cross-platform convention as the evaluator.
    report['provenance']['source_file_sha256'][path] = sha256((ROOT / path).read_bytes()).hexdigest()
    return report


def diagnostic_markdown(report):
    lines = ['# PRELIMINARY AI-ASSISTED DIAGNOSTIC — NOT HUMAN-VALIDATED RESULTS', '',
        report['interpretation'], '',
        f"Development jobs: **{report['case_count']}**. Test jobs not scored: **{report['test_cases_not_scored']}**.", '',
        f"Development employer counts: `{report['development_employer_counts']}`. Draft labels: `{report['draft_label_counts']}`.", '',
        '## Agreement with the AI draft', '',
        'All precision/recall/F1 counts below use the AI draft as a provisional reference. They are not independently validated accuracy figures.', '',
        '| Method | Precision vs draft | Recall vs draft | F1 vs draft | Method-only cells | Draft-only cells | Scored cells |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for result in report['methods'].values():
        counts = result['micro']
        lines.append(f"| {result['label']} | {counts['precision']:.4f} | {counts['recall']:.4f} | {counts['f1']:.4f} | {counts['fp']} | {counts['fn']} | {counts['known']} / {report['case_count'] * len(KEYS)} |")
    lines += ['', 'Uncertain draft cells are excluded for both methods. Undefined precision/recall/F1 use zero. Counts named TP/FP/FN/TN in results.json are relative to the draft only.', '',
        f"Hybrid-minus-keyword micro-F1 versus the draft: **{report['comparison']['hybrid_minus_keyword_micro_f1']:.4f}**. No significance or sampling-interval claim is made.", '',
        '## Skills represented in this development sample', '',
        '| Skill | Positive draft labels | Uncertain draft labels |', '| --- | ---: | ---: |']
    for key in KEYS:
        counts = report['methods']['keyword']['per_skill'][key]
        lines.append(f"| {key} | {counts['support']} | {counts['uncertain']} |")
    lines += ['', 'Skills with no positive draft labels cannot have their extraction sensitivity established by this sample.', '',
        '## Disagreements to inspect', '',
        'Method-only means the matcher selected a skill the AI draft marked absent. Draft-only means the AI draft marked present but the matcher did not select it. Neither direction proves which side is right.', '',
        '| Case | Skill | Method | Difference |', '| --- | --- | --- | --- |']
    for row in report['disagreements_with_ai']:
        lines.append(f"| {row['case_id']} | {row['skill']} | {METHODS[row['method']]} | {row['difference']} |")
    if not report['disagreements_with_ai']:
        lines += ['| — | — | Both | No disagreement on resolved draft cells |']
    lines += ['', 'Mapped passages, manual-review passages and draft notes for each disagreement are retained in results.json.', '',
        '## Reproducibility and next action', '',
        f"Dataset: `{report['dataset_id']}`. Fingerprint: `{report['dataset_fingerprint']}`.", '',
        f"AI draft hash: `{report['draft_sha256']}`. Reference status: `{report['reference_status']}`.", '',
        'Both methods use the same frozen text and empty candidate context. The semantic method includes the keyword baseline plus MiniLM suggestions. Model revision, settings, dependencies and source hashes are recorded in results.json.', '',
        'Inspect disagreements against the original descriptions before changing extraction logic. Keep a record of any development change. The diagnose command neither edits the draft nor trains the model.', '',
        'Obtain genuinely independent human reviews for the evaluate workflow. Anyone who consulted these AI suggestions must disclose that assistance; duplicating or renaming this draft does not create independent reviewers.', '',
        'The packet is a small employer-concentrated convenience sample. If test examples or labels guide implementation, create a fresh untouched evaluation set. This diagnostic cannot establish a research gap or a validated research contribution.', '']
    return '\n'.join(lines)
