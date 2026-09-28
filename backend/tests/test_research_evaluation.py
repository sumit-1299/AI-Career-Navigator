"""Independent test vectors for annotation integrity and paired extraction metrics."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.research_evaluation import (KEYS, REVIEW_SCHEMA, digest, make_live_dataset,
    metrics, paired_bootstrap, reconcile, run_evaluation, seal_dataset, text_digest,
    validate_dataset, validate_review, write_new_json, markdown_report)


def packet():
    cases = [{'id': f'case-{i}', 'group_id': f'group-{i}', 'title': f'Test job {i}',
              'description': f'Python backend job number {i}. SQL required.',
              'text_sha256': text_digest(f'Python backend job number {i}. SQL required.'),
              'split': 'development' if i < 2 else 'test', 'source': {'type': 'test'}} for i in range(4)]
    return seal_dataset(cases, {'method': 'unit-test fixture'})


def review(data, reviewer='R1', **changes):
    return {'schema_version': REVIEW_SCHEMA, 'dataset_id': data['dataset_id'],
            'dataset_fingerprint': data['fingerprint'], 'reviewer_id': reviewer,
            'kind': 'independent', 'complete': True, 'without_model_predictions': True,
            'annotations': [{'case_id': case['id'], 'labels': {key: 'present' if key in {'python', 'sql'} else 'absent' for key in KEYS},
                             'notes': 'Python: "Python backend"; SQL: "SQL required".', 'reviewed': True} for case in data['cases']], **changes}


def fake_post(i, **changes):
    return {'listed': True, 'provider': 'greenhouse', 'board': 'canonical' if i % 2 else 'razorpaysoftwareprivatelimited',
            'employer': 'Canonical' if i % 2 else 'Razorpay', 'provider_id': str(i),
            'title': f'Software engineer team {i}', 'description': f'Python role with SQL for product {i}.',
            'source_url': f'https://example.com/jobs/{i}', 'location': 'India', 'version': 1,
            'content_hash': str(i), 'last_seen_at': '2026-09-28T00:00:00+00:00', 'provider_updated_at': None, 'stale': False, **changes}


class DatasetAndReviewTests(unittest.TestCase):
    def test_fingerprint_detects_text_split_and_metadata_changes(self):
        data = packet()
        validate_dataset(data)
        for field, value in [('description', 'Replaced job'), ('split', 'test'), ('title', 'New title')]:
            modified = deepcopy(data)
            modified['cases'][0][field] = value
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                validate_dataset(modified)

    def test_same_text_and_duplicate_groups_are_rejected_even_with_new_fingerprint(self):
        data = packet()
        for field in ('group_id', 'description'):
            modified = deepcopy(data)
            modified['cases'][1][field] = modified['cases'][0][field]
            if field == 'description':
                modified['cases'][1]['text_sha256'] = modified['cases'][0]['text_sha256']
            modified['fingerprint'] = digest({key: value for key, value in modified.items() if key != 'fingerprint'})
            with self.assertRaises(ValueError):
                validate_dataset(modified)

    def test_selection_is_deterministic_balanced_and_has_disjoint_groups(self):
        rows = [fake_post(i) for i in range(12)]
        a, b = make_live_dataset(rows, 8), make_live_dataset(list(reversed(rows)), 8)
        self.assertEqual(a['cases'], b['cases'])
        self.assertEqual(a['selection']['employer_counts'], {'Canonical': 4, 'Razorpay': 4})
        dev = {case['group_id'] for case in a['cases'] if case['split'] == 'development'}
        test = {case['group_id'] for case in a['cases'] if case['split'] == 'test'}
        self.assertFalse(dev & test)
        self.assertEqual((len(dev), len(test)), (4, 4))

    def test_transitive_duplicate_groups_are_not_split(self):
        rows = [fake_post(i) for i in range(8)]
        rows[1]['title'] = rows[3]['title']  # same employer/title
        rows[3]['description'] = rows[4]['description']  # bridges another employer by exact text
        data = make_live_dataset(rows, 4)
        self.assertEqual(data['selection']['distinct_groups'], 6)
        selected_ids = {case['source']['provider_id'] for case in data['cases']}
        self.assertLessEqual(len(selected_ids & {'1', '3', '4'}), 1)

    def test_not_enough_jobs_does_not_silently_change_the_sample_size(self):
        with self.assertRaisesRegex(ValueError, 'requested 24'):
            make_live_dataset([fake_post(i) for i in range(6)], 24)

    def test_drafts_missing_labels_and_missing_attestation_are_rejected(self):
        data = packet()
        for change in ({'complete': False}, {'without_model_predictions': False}, {'reviewer_id': 'Real Name Here'}):
            with self.assertRaises(ValueError):
                validate_review(data, review(data, **change))
        bad = review(data)
        bad['annotations'][0]['labels'].pop('java')
        with self.assertRaises(ValueError):
            validate_review(data, bad)
        bad = review(data)
        bad['annotations'].pop()
        with self.assertRaises(ValueError):
            validate_review(data, bad)

    def test_uncertainty_and_positive_labels_need_notes(self):
        data = packet()
        bad = review(data)
        bad['annotations'][0]['notes'] = ''
        with self.assertRaisesRegex(ValueError, 'supporting quotes'):
            validate_review(data, bad)

    def test_reviews_cannot_be_reused_on_another_packet(self):
        a, b = packet(), packet()
        with self.assertRaisesRegex(ValueError, 'different dataset'):
            validate_review(b, review(a))

    def test_same_reviewer_cannot_supply_both_independent_files(self):
        data = packet()
        with self.assertRaisesRegex(ValueError, 'two different'):
            reconcile(data, review(data), review(data))

    def test_agreement_and_disagreement_detection_use_three_label_categories(self):
        data = packet(); a, b = review(data), review(data, 'R2')
        b['annotations'][0]['labels']['sql'] = 'uncertain'
        _, conflicts, agreement = reconcile(data, a, b)
        self.assertEqual(conflicts[0]['skills'], ['sql'])
        self.assertEqual(agreement['disputed_cells'], 1)
        self.assertEqual(agreement['raw_agreement'], 39 / 40)
        self.assertTrue(0 < agreement['cohen_kappa'] < 1)

    def test_adjudication_requires_third_reviewer_exact_parent_files_and_locked_agreements(self):
        data = packet(); a, b = review(data), review(data, 'R2')
        b['annotations'][0]['labels']['sql'] = 'uncertain'
        final = review(data, 'R3', kind='adjudication', parent_review_hashes=[digest(a), digest(b)])
        final['annotations'] = final['annotations'][:1]
        gold, conflicts, _ = reconcile(data, a, b, final)
        self.assertEqual(conflicts, [])
        self.assertEqual(gold['case-0']['sql'], 'present')
        for change in ({'reviewer_id': 'R1'}, {'parent_review_hashes': ['wrong', 'hash']}):
            with self.assertRaises(ValueError):
                reconcile(data, a, b, {**final, **change})
        final['annotations'][0]['labels']['java'] = 'present'
        with self.assertRaisesRegex(ValueError, 'agreed label'):
            reconcile(data, a, b, final)

    def test_frozen_output_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'packet.json'
            write_new_json(path, packet())
            original = path.read_bytes()
            with self.assertRaises(FileExistsError):
                write_new_json(path, packet())
            self.assertEqual(path.read_bytes(), original)


class EvaluationMetricTests(unittest.TestCase):
    def test_hand_calculated_micro_metrics_and_uncertain_mask(self):
        cases = [{'id': 'a'}, {'id': 'b'}]
        gold = {name: {key: 'absent' for key in KEYS} for name in ('a', 'b')}
        gold['a'].update(python='present', sql='present')
        gold['b'].update(python='present', java='uncertain')
        predictions = {'a': ['python', 'docker'], 'b': ['python', 'java']}
        result = metrics(cases, gold, predictions)
        self.assertEqual((result['micro']['tp'], result['micro']['fp'], result['micro']['fn']), (2, 1, 1))
        self.assertEqual(result['micro']['known'], 19)
        self.assertAlmostEqual(result['micro']['f1'], 2 / 3)
        self.assertEqual(result['scored_cell_fraction'], .95)
        self.assertEqual(result['fully_labelled_cases'], 1)
        self.assertEqual(result['exact_set_accuracy'], 0)
        self.assertEqual(result['per_skill']['java']['fp'], 0)
        self.assertEqual(result['per_skill']['java']['uncertain'], 1)

    def test_zero_division_and_empty_positive_support_are_explicit(self):
        labels = {'a': {key: 'absent' for key in KEYS}}
        result = metrics([{'id': 'a'}], labels, {'a': []})
        self.assertEqual(result['micro']['f1'], 0)
        self.assertEqual(result['micro']['support'], 0)
        self.assertEqual(result['exact_set_accuracy'], 1)
        self.assertEqual(result['zero_division'], 0)

    def test_bootstrap_identical_predictions_have_zero_paired_difference(self):
        data = packet(); gold, _, _ = reconcile(data, review(data), review(data, 'R2'))
        predictions = {case['id']: ['python', 'sql'] for case in data['cases']}
        result = paired_bootstrap(data['cases'], gold, predictions, predictions, repeats=100)
        self.assertEqual(result['delta_micro_f1'], 0)
        self.assertEqual(result['interval_95'], [0, 0])

    def test_both_methods_use_identical_text_and_errors_are_auditable(self):
        data = packet(); gold, _, _ = reconcile(data, review(data), review(data, 'R2'))
        calls = []
        def runner(text, mode):
            calls.append((text, mode))
            skills = ['python'] if mode == 'keyword' else ['python', 'sql', 'docker']
            return {'skills': [{'skill_key': key, 'job_sources': [{'text': text}]} for key in skills], 'manual_review': []}
        result = run_evaluation(data, gold, 'development', runner=runner)
        self.assertEqual(len(calls), 4)
        self.assertEqual(calls[0][0], calls[1][0])
        self.assertEqual(result['methods']['keyword']['micro']['fn'], 2)
        self.assertEqual(result['methods']['semantic']['micro']['fp'], 2)
        self.assertEqual(result['methods']['semantic']['label'], 'Keywords + semantic suggestions')
        self.assertEqual(result['provenance']['candidate_context'], 'empty for every case; extraction only')
        self.assertTrue(any(row['error'] == 'false_negative' for row in result['errors']))

    def test_failed_inference_does_not_produce_partial_success_metrics(self):
        data = packet(); gold, _, _ = reconcile(data, review(data), review(data, 'R2'))
        def fail(text, mode):
            raise RuntimeError('Model unavailable')
        with self.assertRaisesRegex(ValueError, 'no partial metrics'):
            run_evaluation(data, gold, 'test', runner=fail)

    def test_all_uncertain_split_is_rejected(self):
        data = packet(); gold = {case['id']: {key: 'uncertain' for key in KEYS} for case in data['cases']}
        with self.assertRaisesRegex(ValueError, 'No resolved labels'):
            run_evaluation(data, gold, 'development', runner=lambda *_: {})

    def test_smoke_report_cannot_be_mistaken_for_research_output(self):
        data = packet(); data['kind'] = 'synthetic_smoke'
        data['fingerprint'] = digest({key: value for key, value in data.items() if key != 'fingerprint'})
        gold, _, _ = reconcile(data, review(data), review(data, 'R2'))
        result = run_evaluation(data, gold, 'test', runner=lambda *_: {'skills': [], 'manual_review': []}, reference_status='AI-authored synthetic smoke references')
        text = markdown_report(result)
        self.assertIn('SMOKE TEST — NOT RESEARCH RESULTS', text)
        self.assertIn('AI-authored', text)


if __name__ == '__main__':
    unittest.main()
