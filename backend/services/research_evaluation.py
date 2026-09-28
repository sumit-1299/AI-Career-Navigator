"""Frozen job-skill extraction evaluation. No candidate records or database writes."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import platform
import random
import re
import subprocess
from uuid import uuid4

from services.job_matching import build_comparison, SIMILARITY_THRESHOLD, MARGIN_THRESHOLD
from services.semantic_encoder import MODEL_ID, MODEL_REVISION, get_encoder
from services.skill_catalog import CATALOG_VERSION, SKILLS

SCHEMA = 'career-skill-dataset-v1'
REVIEW_SCHEMA = 'career-skill-review-v1'
POLICY = 'job-relevant-skills-v1'
KEYS = [item['key'] for item in SKILLS]
LABELS = {'present', 'absent', 'uncertain'}
METHODS = {'keyword': 'Keyword baseline', 'semantic': 'Keywords + semantic suggestions'}
ROOT = Path(__file__).resolve().parents[2]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def text_digest(text):
    return sha256(text.encode()).hexdigest()


def load_json(path):
    path = Path(path)
    if path.stat().st_size > 20 * 1024 * 1024:
        raise ValueError('Input file exceeds 20 MiB.')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_new_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Frozen packets and run artifacts must never be overwritten by accident.
    with path.open('x', encoding='utf-8', newline='\n') as output:
        json.dump(data, output, indent=2, ensure_ascii=False, allow_nan=False)
        output.write('\n')


def seal_dataset(cases, selection, kind='live_job_pilot'):
    data = {'schema_version': SCHEMA, 'dataset_id': str(uuid4()), 'created_at': now_iso(),
            'kind': kind, 'catalog_version': CATALOG_VERSION, 'annotation_policy': POLICY,
            'skills': [{'key': item['key'], 'label': item['label']} for item in SKILLS],
            'selection': selection, 'cases': cases}
    data['fingerprint'] = digest(data)
    validate_dataset(data)
    return data


def validate_dataset(data):
    if not isinstance(data, dict) or data.get('schema_version') != SCHEMA:
        raise ValueError('Choose a supported frozen dataset JSON file.')
    expected = digest({key: value for key, value in data.items() if key != 'fingerprint'})
    if data.get('fingerprint') != expected:
        raise ValueError('Dataset fingerprint mismatch. Use the original frozen export; do not edit its text or split.')
    if data.get('catalog_version') != CATALOG_VERSION or data.get('annotation_policy') != POLICY:
        raise ValueError('Dataset vocabulary or annotation policy differs from this evaluator.')
    if data.get('skills') != [{'key': item['key'], 'label': item['label']} for item in SKILLS]:
        raise ValueError('Dataset skill list differs from the fixed vocabulary.')
    if data.get('kind') not in {'live_job_pilot', 'synthetic_smoke'}:
        raise ValueError('Unknown dataset kind.')
    cases = data.get('cases')
    if not isinstance(cases, list) or not 2 <= len(cases) <= 200:
        raise ValueError('A dataset must contain 2–200 cases.')
    ids, groups, texts = set(), set(), set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get('id'), str) or not re.fullmatch(r'[-A-Za-z0-9_]{1,100}', case['id']) or case['id'] in ids:
            raise ValueError('Missing or duplicate case identifier.')
        if not isinstance(case.get('group_id'), str) or not case['group_id'] or case['group_id'] in groups:
            raise ValueError('Each sampled case must represent a distinct source group.')
        if case.get('split') not in {'development', 'test'}:
            raise ValueError('Cases must have a development or test split.')
        description = case.get('description')
        if not isinstance(description, str) or not description.strip() or len(description) > 60000:
            raise ValueError('Missing or oversized case description.')
        if case.get('text_sha256') != text_digest(description):
            raise ValueError('A case text fingerprint does not match.')
        normalized = ' '.join(description.casefold().split())
        if normalized in texts:
            raise ValueError('Duplicate job text would leak across evaluation cases.')
        if not isinstance(case.get('title'), str) or not isinstance(case.get('source'), dict):
            raise ValueError('Missing title or source metadata.')
        ids.add(case['id']); groups.add(case['group_id']); texts.add(normalized)
    if {case['split'] for case in cases} != {'development', 'test'}:
        raise ValueError('Both development and test cases are required.')
    return data


def make_live_dataset(records, size=24, seed='career-pilot-2026-09-v1'):
    """Select without model predictions. Group exact text or employer/title duplicates."""
    if type(size) is not int or not 4 <= size <= 100:
        raise ValueError('Choose a sample size from 4 to 100.')
    role_words = re.compile(r'\b(engineer|engineering|developer|software|backend|python)\b', re.I)
    eligible = [row for row in records if row['listed'] and role_words.search(row['title'])]
    eligible.sort(key=lambda row: (row['board'], row['provider_id']))
    # Connected components ensure a shared title OR duplicate text joins the same group,
    # including transitive duplicate relationships. One representative per group is used.
    parents = list(range(len(eligible)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    seen = {}
    for i, row in enumerate(eligible):
        title = ' '.join(re.sub(r'[^\w]+', ' ', row['title'].casefold()).split())
        markers = [('title', row['board'], title), ('text', ' '.join(row['description'].casefold().split()))]
        for marker in markers:
            if marker in seen:
                parents[find(i)] = find(seen[marker])
            else:
                seen[marker] = i
    components = defaultdict(list)
    for i, row in enumerate(eligible):
        components[find(i)].append(row)
    representatives = []
    for rows in components.values():
        group_id = digest(sorted(f"{row['board']}:{row['provider_id']}" for row in rows))
        row = min(rows, key=lambda item: digest([seed, item['board'], item['provider_id']]))
        representatives.append((group_id, row))
    if len(representatives) < size:
        raise ValueError(f'Only {len(representatives)} distinct engineering-related groups are cached; requested {size}. Refresh both boards or explicitly choose a smaller pilot size.')
    buckets = defaultdict(list)
    for group_id, row in representatives:
        buckets[row['board']].append((group_id, row))
    for bucket in buckets.values():
        bucket.sort(key=lambda pair: digest([seed, pair[0]]))
    chosen = []
    while len(chosen) < size:
        for board in sorted(buckets):
            if buckets[board] and len(chosen) < size:
                chosen.append(buckets[board].pop(0))
    chosen.sort(key=lambda pair: digest([seed, 'split', pair[0]]))
    cases = []
    for index, (group_id, row) in enumerate(chosen):
        cases.append({'id': f'job-{index + 1:03}', 'group_id': group_id,
                      'split': 'development' if index < size // 2 else 'test',
                      'title': row['title'], 'description': row['description'],
                      'text_sha256': text_digest(row['description']),
                      'source': {key: row[key] for key in ('provider', 'board', 'employer', 'provider_id', 'source_url',
                                  'location', 'version', 'content_hash', 'last_seen_at', 'provider_updated_at', 'stale')}})
    return seal_dataset(cases, {'method': 'deterministic employer round-robin, grouped before split',
        'seed': seed, 'requested_size': size, 'cached_listed_count': sum(row['listed'] for row in records),
        'eligible_postings': len(eligible), 'distinct_groups': len(representatives),
        'title_filter': role_words.pattern, 'employer_counts': dict(Counter(case['source']['employer'] for case in cases)),
        'stale_case_count': sum(case['source']['stale'] for case in cases),
        'near_duplicate_review_required': True})


def validate_review(dataset, review, kind='independent', required_ids=None):
    if not isinstance(review, dict) or review.get('schema_version') != REVIEW_SCHEMA:
        raise ValueError('Choose a supported review JSON file.')
    if review.get('dataset_id') != dataset['dataset_id'] or review.get('dataset_fingerprint') != dataset['fingerprint']:
        raise ValueError('Review belongs to a different dataset or dataset version.')
    if review.get('kind') != kind or review.get('complete') is not True or review.get('without_model_predictions') is not True:
        raise ValueError('Use a completed review with the independent-from-model-predictions attestation.')
    reviewer = review.get('reviewer_id')
    if not isinstance(reviewer, str) or not re.fullmatch(r'[A-Za-z0-9_-]{2,40}', reviewer):
        raise ValueError('Use an anonymous reviewer ID of 2–40 letters, digits, underscores or hyphens.')
    required = set(required_ids if required_ids is not None else [case['id'] for case in dataset['cases']])
    rows = review.get('annotations')
    if not isinstance(rows, list):
        raise ValueError('Review annotations are missing.')
    result = {}
    for row in rows:
        if not isinstance(row, dict) or row.get('case_id') not in required or row['case_id'] in result:
            raise ValueError('Review contains an unknown or duplicate case.')
        labels = row.get('labels')
        if not isinstance(labels, dict) or set(labels) != set(KEYS) or any(value not in LABELS for value in labels.values() if isinstance(value, str)) or any(not isinstance(value, str) for value in labels.values()):
            raise ValueError('Explicitly label all ten concepts present, absent or uncertain.')
        if row.get('reviewed') is not True or not isinstance(row.get('notes'), str) or len(row['notes']) > 5000:
            raise ValueError('Confirm every case as reviewed and keep notes under 5,000 characters.')
        if any(value in {'present', 'uncertain'} for value in labels.values()) and not row['notes'].strip():
            raise ValueError('Add supporting quotes for present skills and explain uncertain labels in the case notes.')
        result[row['case_id']] = row
    if set(result) != required:
        raise ValueError(f'Review is incomplete: {len(required - set(result))} cases are missing.')
    return result


def reconcile(dataset, review_a, review_b, adjudication=None):
    validate_dataset(dataset)
    a = validate_review(dataset, review_a)
    b = validate_review(dataset, review_b)
    if review_a['reviewer_id'] == review_b['reviewer_id']:
        raise ValueError('Use two different independent reviewer IDs.')
    disagreements = []
    flat_a, flat_b = [], []
    resolved = {}
    for case in dataset['cases']:
        case_id = case['id']
        la, lb = a[case_id]['labels'], b[case_id]['labels']
        differing = [key for key in KEYS if la[key] != lb[key]]
        flat_a.extend(la[key] for key in KEYS); flat_b.extend(lb[key] for key in KEYS)
        resolved[case_id] = dict(la)
        if differing:
            disagreements.append({'case_id': case_id, 'skills': differing,
                                  'review_a': a[case_id], 'review_b': b[case_id]})
    total = len(flat_a)
    observed = sum(x == y for x, y in zip(flat_a, flat_b)) / total
    ca, cb = Counter(flat_a), Counter(flat_b)
    chance = sum(ca[label] * cb[label] for label in LABELS) / total ** 2
    agreement = {'cells': total, 'raw_agreement': observed,
                 'cohen_kappa': (observed - chance) / (1 - chance) if chance < 1 else None,
                 'disputed_cells': sum(len(row['skills']) for row in disagreements),
                 'disputed_cases': len(disagreements), 'labels': sorted(LABELS)}
    if adjudication is not None:
        ids = [row['case_id'] for row in disagreements]
        final = validate_review(dataset, adjudication, kind='adjudication', required_ids=ids)
        if adjudication['reviewer_id'] in {review_a['reviewer_id'], review_b['reviewer_id']}:
            raise ValueError('Use a third reviewer ID for adjudication.')
        if adjudication.get('parent_review_hashes') != [digest(review_a), digest(review_b)]:
            raise ValueError('Adjudication does not match these two original review files in this order.')
        for conflict in disagreements:
            case_id = conflict['case_id']
            labels = final[case_id]['labels']
            for key in KEYS:
                if key not in conflict['skills'] and labels[key] != resolved[case_id][key]:
                    raise ValueError('Adjudication changed an agreed label; repeat the independent review explicitly.')
            resolved[case_id] = dict(labels)
        disagreements = []
    return resolved, disagreements, agreement


def metrics(cases, gold, predictions):
    totals = Counter(tp=0, fp=0, fn=0, tn=0, known=0, uncertain=0)
    per_skill = {key: Counter(tp=0, fp=0, fn=0, tn=0, known=0, uncertain=0) for key in KEYS}
    exact = complete = 0
    for case in cases:
        labels, predicted = gold[case['id']], set(predictions[case['id']])
        if not predicted <= set(KEYS):
            raise ValueError('Predictions contain a concept outside the fixed vocabulary.')
        if all(value != 'uncertain' for value in labels.values()):
            complete += 1
            exact += predicted == {key for key, value in labels.items() if value == 'present'}
        for key in KEYS:
            label = labels[key]
            if label == 'uncertain':
                totals['uncertain'] += 1; per_skill[key]['uncertain'] += 1
                continue
            outcome = 'tp' if key in predicted and label == 'present' else 'fp' if key in predicted else 'fn' if label == 'present' else 'tn'
            totals[outcome] += 1; per_skill[key][outcome] += 1
            totals['known'] += 1; per_skill[key]['known'] += 1
    def summarize(counts):
        tp, fp, fn = (counts[key] for key in ('tp', 'fp', 'fn'))
        return {**counts, 'support': tp + fn, 'predicted_positive': tp + fp,
                'precision': tp / (tp + fp) if tp + fp else 0.0,
                'recall': tp / (tp + fn) if tp + fn else 0.0,
                'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}
    scores = {key: summarize(value) for key, value in per_skill.items()}
    return {'micro': summarize(totals), 'per_skill': scores,
            'macro_f1_all_10': sum(row['f1'] for row in scores.values()) / len(KEYS),
            'scored_cell_fraction': totals['known'] / (len(cases) * len(KEYS)),
            'exact_set_accuracy': exact / complete if complete else None,
            'fully_labelled_cases': complete, 'exact_cases': exact,
            'zero_division': 0, 'uncertain_policy': 'excluded per job-skill cell, with coverage reported'}


def paired_bootstrap(cases, gold, keyword, semantic, repeats=2000, seed=1299):
    # Resample whole jobs (one representative per source group), never individual skill cells.
    rng = random.Random(seed)
    counts = {}
    for case in cases:
        counts[case['id']] = [metrics([case], gold, pred)['micro'] for pred in (keyword, semantic)]
    def f1(rows, method):
        tp = sum(counts[row['id']][method]['tp'] for row in rows)
        fp = sum(counts[row['id']][method]['fp'] for row in rows)
        fn = sum(counts[row['id']][method]['fn'] for row in rows)
        return 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    samples = sorted(f1(batch, 1) - f1(batch, 0) for batch in
                     ([rng.choice(cases) for _ in cases] for _ in range(repeats)))
    def percentile(p):
        at = (len(samples) - 1) * p
        low = int(at); high = min(low + 1, len(samples) - 1)
        return samples[low] + (samples[high] - samples[low]) * (at - low)
    return {'method': 'paired percentile bootstrap by job/source group', 'repeats': repeats, 'seed': seed,
            'delta_micro_f1': f1(cases, 1) - f1(cases, 0), 'interval_95': [percentile(.025), percentile(.975)],
            'caution': 'Small convenience sample; descriptive uncertainty, not proof of generalization or novelty.'}


def provenance():
    paths = ['backend/services/job_matching.py', 'backend/services/skill_catalog.py',
             'backend/services/semantic_encoder.py', 'backend/services/research_evaluation.py',
             'backend/scripts/research_evaluation.py']
    files = {path: sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    versions = {}
    for name in ('onnxruntime', 'tokenizers', 'numpy'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {'git_commit': commit, 'source_file_sha256': files, 'python': platform.python_version(),
            'dependencies': versions, 'model': {'id': MODEL_ID, 'revision': MODEL_REVISION},
            'minimum_cosine': SIMILARITY_THRESHOLD, 'minimum_margin': MARGIN_THRESHOLD,
            'catalog_version': CATALOG_VERSION, 'fragment_limit': 300,
            'candidate_context': 'empty for every case; extraction only'}


def run_evaluation(dataset, gold, split, agreement=None, review_hashes=None, runner=None, reference_status='two_self_attested_independent_reviews'):
    validate_dataset(dataset)
    if split not in {'development', 'test'}:
        raise ValueError('Select development or test explicitly.')
    cases = [case for case in dataset['cases'] if case['split'] == split]
    if not any(value != 'uncertain' for case in cases for value in gold[case['id']].values()):
        raise ValueError('No resolved labels are available in this split.')
    if runner is None:
        encoder = get_encoder()  # No fallback or partial keyword-only report on model failure.
        def runner(description, mode):
            return build_comparison(description, {'skills': [], 'evidence': [], 'sql_assessment': None},
                                    mode, encoder=encoder, max_fragments=300)
    predictions = {mode: {} for mode in METHODS}
    errors = []
    for case in cases:
        for mode in METHODS:
            try:
                result = runner(case['description'], mode)
            except Exception as exc:
                raise ValueError(f'Case {case["id"]} failed in {METHODS[mode]}; no partial metrics were written. {exc}') from exc
            predicted = [row['skill_key'] for row in result['skills']]
            predictions[mode][case['id']] = predicted
            for key in KEYS:
                label = gold[case['id']][key]
                if label == 'uncertain' or (key in predicted) == (label == 'present'):
                    continue
                row = next((row for row in result['skills'] if row['skill_key'] == key), None)
                errors.append({'case_id': case['id'], 'method': mode, 'skill': key,
                               'error': 'false_positive' if key in predicted else 'false_negative',
                               'gold': label, 'mapped_passages': row['job_sources'] if row else [],
                               'manual_review_passages': result['manual_review']})
    report = {'schema_version': 'career-skill-evaluation-v1', 'run_id': str(uuid4()), 'created_at': now_iso(),
              'dataset_id': dataset['dataset_id'], 'dataset_fingerprint': dataset['fingerprint'],
              'dataset_kind': dataset['kind'], 'split': split, 'case_count': len(cases),
              'reference_status': reference_status, 'review_hashes': review_hashes or [],
              'selection': dataset['selection'], 'provenance': provenance(), 'agreement': agreement,
              'methods': {mode: {'label': label, **metrics(cases, gold, predictions[mode])} for mode, label in METHODS.items()},
              'paired_difference': paired_bootstrap(cases, gold, predictions['keyword'], predictions['semantic']),
              'predictions': predictions, 'gold': {case['id']: gold[case['id']] for case in cases}, 'errors': errors,
              'interpretation': 'Measures job-skill extraction within ten concepts. Does not measure hiring, proficiency, job ranking, roadmap benefit, or research novelty.'}
    return report


def markdown_report(report):
    smoke = report['dataset_kind'] == 'synthetic_smoke'
    lines = ['# ' + ('SMOKE TEST — NOT RESEARCH RESULTS' if smoke else 'Job-skill extraction pilot'), '',
             report['interpretation'], '', f"Dataset: `{report['dataset_id']}` · Split: **{report['split']}** · Jobs: **{report['case_count']}**", '',
             f"Reference status: `{report['reference_status']}`. Reviewer declarations are self-attested, not independently authenticated.", '',
             '| Method | Micro precision | Micro recall | Micro F1 | Macro F1 (10 skills) | Scored cells |',
             '| --- | ---: | ---: | ---: | ---: | ---: |']
    for result in report['methods'].values():
        lines.append(f"| {result['label']} | {result['micro']['precision']:.4f} | {result['micro']['recall']:.4f} | {result['micro']['f1']:.4f} | {result['macro_f1_all_10']:.4f} | {result['scored_cell_fraction']:.1%} |")
    diff = report['paired_difference']
    lines += ['', 'Precision/recall/F1 use zero for a zero denominator. Uncertain labels are excluded cell by cell; review coverage and per-skill support in results.json.', '',
              f"Paired micro-F1 difference (hybrid minus keyword): {diff['delta_micro_f1']:.4f}. Descriptive 95% bootstrap interval: [{diff['interval_95'][0]:.4f}, {diff['interval_95'][1]:.4f}] ({diff['repeats']} resamples of whole jobs).", '', diff['caution'], '']
    if report['agreement']:
        a = report['agreement']
        kappa = 'undefined (single-label marginals)' if a['cohen_kappa'] is None else f"{a['cohen_kappa']:.4f}"
        lines += [f"Pre-adjudication agreement across the entire packet: {a['raw_agreement']:.1%}; Cohen's kappa: {kappa}; disputed cells: {a['disputed_cells']}. These pooled three-label statistics can be dominated by absent labels.", '']
    lines += ['## Reproducibility and limits', '',
              f"Dataset fingerprint: `{report['dataset_fingerprint']}`. See results.json for source hashes, model revision, review hashes, predictions, errors and selection metadata.", '',
              'The semantic method is keywords plus semantic suggestions, not a semantic-only ablation. No thresholds are tuned by this command. No model is trained. Candidate context is empty for this experiment.', '',
              'Use development cases for changes. Treat test results as exploratory if test cases, labels or errors influenced implementation. Do not call this a novel, validated or market-wide result. A separate human study is needed to test evidence-aware guidance.', '']
    if smoke:
        lines += ['The texts and reference labels in this run are AI-authored synthetic checks. They are not human ground truth, independently held out, or evidence of real-world quality.', '']
    return '\n'.join(lines)
