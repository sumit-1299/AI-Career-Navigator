"""Checks for development-only AI reference handling and honest report provenance."""
from argparse import Namespace
from contextlib import redirect_stderr
from copy import deepcopy
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import research_evaluation as cli
from services.research_diagnostic import diagnostic_markdown, run_diagnostic, validate_ai_draft
from services.research_evaluation import digest, validate_review
from test_research_evaluation import packet, review


def ai_draft(data):
    result = review(data, 'AI_DRAFT', complete=False, without_model_predictions=False,
                    annotation_origin='ai_assisted')
    for row in result['annotations']:
        row.update(reviewed=False, annotation_origin='ai_assisted')
    return result


class AIDiagnosticTests(unittest.TestCase):
    def test_plain_and_ui_reexported_drafts_validate_but_never_as_independent_reviews(self):
        data = packet()
        draft = ai_draft(data)
        for remove_top_marker in (False, True):
            candidate = deepcopy(draft)
            if remove_top_marker:
                candidate.pop('annotation_origin')
            self.assertEqual(len(validate_ai_draft(data, candidate)), 4)
            # Setting completion/declarations must not erase explicit row provenance.
            candidate.update(complete=True, without_model_predictions=True)
            for row in candidate['annotations']:
                row['reviewed'] = True
            with self.assertRaisesRegex(ValueError, 'AI-assisted labels'):
                validate_review(data, candidate)
        self.assertEqual(len(validate_review(data, review(data))), 4)

    def test_draft_binding_provenance_and_explicit_nonhuman_declaration(self):
        data = packet()
        original = ai_draft(data)
        variants = [dict(original, dataset_id='wrong'), dict(original, dataset_fingerprint='wrong'),
                    dict(original, complete=True), dict(original, without_model_predictions=True),
                    dict(original, kind='adjudication'), dict(original, schema_version='unsupported')]
        missing_origin = deepcopy(original)
        missing_origin.pop('annotation_origin')
        for row in missing_origin['annotations']:
            row.pop('annotation_origin')
        variants.append(missing_origin)
        for bad in variants:
            with self.subTest(fields={key:bad[key] for key in bad if key != 'annotations'}):
                with self.assertRaises(ValueError):
                    validate_ai_draft(data, bad)

    def test_missing_duplicate_invalid_labels_and_absent_notes_fail(self):
        data = packet()
        mutations = [lambda x: x['annotations'].pop(),
                     lambda x: x['annotations'].append(deepcopy(x['annotations'][0])),
                     lambda x: x['annotations'][0]['labels'].pop('java'),
                     lambda x: x['annotations'][0]['labels'].update(python=''),
                     lambda x: x['annotations'][0]['labels'].update(python=[]),
                     lambda x: x['annotations'][0].update(notes=''),
                     lambda x: x['annotations'][0].update(notes='x' * 5001),
                     lambda x: x['annotations'].__setitem__(0, None)]
        for mutate in mutations:
            bad = ai_draft(data)
            mutate(bad)
            with self.assertRaises(ValueError):
                validate_ai_draft(data, bad)

    def test_only_development_text_is_run_and_reference_metrics_are_hand_checked(self):
        data = packet()
        draft = ai_draft(data)
        draft['annotations'][0]['labels']['sql'] = 'uncertain'
        original_data, original_draft = deepcopy(data), deepcopy(draft)
        calls = []
        def runner(text, mode):
            calls.append((text, mode))
            skills = ['python', 'sql'] if mode == 'keyword' else ['sql', 'rest_api']
            return {'skills': [{'skill_key': key, 'job_sources': [{'text': text}]} for key in skills],
                    'manual_review': []}
        result = run_diagnostic(data, draft, runner=runner)
        self.assertEqual(len(calls), 4)
        self.assertEqual({text for text, _ in calls}, {case['description'] for case in data['cases'][:2]})
        self.assertEqual(result['test_cases_not_scored'], 2)
        self.assertEqual(result['development_case_ids'], ['case-0', 'case-1'])
        self.assertEqual(result['methods']['keyword']['micro']['known'], 19)
        self.assertEqual(result['methods']['keyword']['micro']['f1'], 1)
        self.assertAlmostEqual(result['methods']['semantic']['micro']['f1'], 1 / 3)
        self.assertAlmostEqual(result['comparison']['hybrid_minus_keyword_micro_f1'], -2 / 3)
        self.assertEqual(result['draft_sha256'], digest(draft))
        self.assertEqual(result['schema_version'], 'career-skill-ai-diagnostic-v1')
        self.assertFalse(result['independent_human_validation'])
        self.assertNotIn('agreement', result)
        self.assertNotIn('gold', result)
        self.assertNotIn('paired_difference', result)
        self.assertEqual({row['difference'] for row in result['disagreements_with_ai']}, {'method_only', 'draft_only'})
        self.assertTrue(all('draft_notes' in row and 'gold' not in row for row in result['disagreements_with_ai']))
        self.assertEqual((data, draft), (original_data, original_draft))
        rendered = diagnostic_markdown(result)
        self.assertIn('NOT HUMAN-VALIDATED RESULTS', rendered)
        self.assertIn('F1 vs draft', rendered)
        self.assertIn('cannot have their extraction sensitivity established', rendered)
        self.assertNotIn("Cohen's kappa", rendered)
        self.assertNotIn('bootstrap interval', rendered)

    def test_tampered_packet_and_synthetic_packet_rejected_before_inference(self):
        data = packet()
        draft = ai_draft(data)
        data['cases'][0]['description'] = 'Changed text'
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            run_diagnostic(data, draft, runner=lambda *_: self.fail('Must not run'))
        data = packet()
        data['kind'] = 'synthetic_smoke'
        data['fingerprint'] = digest({key:value for key,value in data.items() if key != 'fingerprint'})
        with self.assertRaisesRegex(ValueError, 'Use smoke'):
            run_diagnostic(data, ai_draft(data), runner=lambda *_: self.fail('Must not run'))

    def test_all_uncertain_development_and_failed_model_do_not_yield_success(self):
        data = packet()
        draft = ai_draft(data)
        for row in draft['annotations'][:2]:
            row['labels'] = dict.fromkeys(row['labels'], 'uncertain')
        with self.assertRaisesRegex(ValueError, 'No resolved labels'):
            run_diagnostic(data, draft, runner=lambda *_: self.fail('Must not run'))
        def broken_model(*_):
            raise RuntimeError('Unavailable model')
        with self.assertRaisesRegex(ValueError, 'no partial metrics'):
            run_diagnostic(data, ai_draft(data), runner=broken_model)

    def test_cli_rejects_test_split_and_preserves_existing_or_failed_run_output(self):
        with patch.object(sys, 'argv', ['research_evaluation.py', 'diagnose', '--dataset', 'd.json',
                    '--draft', 'a.json', '--out', 'output', '--split', 'test']), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                cli.main()
            self.assertEqual(caught.exception.code, 2)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'run'
            args = Namespace(dataset='unused', draft='unused', out=output)
            with patch.object(cli, 'load_json', return_value={}), patch.object(cli, 'run_diagnostic', side_effect=ValueError('Inference failed')):
                with self.assertRaisesRegex(ValueError, 'Inference failed'):
                    cli.diagnose(args)
            self.assertFalse(output.exists())
            output.mkdir()
            marker = output / 'keep.txt'
            marker.write_text('Earlier run')
            with self.assertRaisesRegex(ValueError, 'already exists'):
                cli.diagnose(args)
            self.assertEqual(marker.read_text(), 'Earlier run')


if __name__ == '__main__':
    unittest.main()
