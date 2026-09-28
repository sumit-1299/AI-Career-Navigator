"""Offline provider fixtures: cache integrity, provenance, ownership and retries."""
from datetime import timedelta
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['JWT_SECRET_KEY'] = 'assessment-tests-only-not-a-deployment-secret-2026'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from extensions import db
from models.assessment_attempt import utc_now
from models.job_comparison import JobComparison
from models.live_job import JobBoardSync, LiveJob
from services.live_jobs import (BOARD_LOCKS, FeedUnavailable, fetch_board,
                                normalize_feed, plain_description)
from services.semantic_encoder import SemanticUnavailable


def posting(number=1, **changes):
    return {'id': number, 'internal_job_id': number + 100, 'title': 'Python backend developer',
            'location': {'name': 'Bengaluru, India'},
            'absolute_url': f'https://job-boards.greenhouse.io/canonical/jobs/{number}',
            'content': '&lt;h2&gt;Requirements&lt;/h2&gt;&lt;p&gt;Python, SQL and REST APIs are required.&lt;/p&gt;',
            'updated_at': '2026-09-20T12:00:00Z', **changes}


def feed(*jobs):
    return {'jobs': list(jobs), 'meta': {'total': len(jobs)}}


class ProviderTests(unittest.TestCase):
    def test_plain_text_decodes_entities_preserves_boundaries_and_drops_scripts(self):
        text = plain_description('&lt;h2&gt;Requirements&lt;/h2&gt;&lt;p&gt;Python &amp;amp; SQL&lt;/p&gt;<script>stolen()</script><style>bad</style><ul><li>Git</li></ul>')
        self.assertEqual(text, 'Requirements\nPython & SQL\nGit')

    def test_incomplete_duplicate_and_malformed_feeds_are_rejected(self):
        for data in ({}, {'jobs': [], 'meta': {'total': 1}}, feed(posting(), posting()),
                     feed(posting(title='')), feed(posting(content='')), feed(posting(updated_at='yesterday')),
                     feed(posting(absolute_url='http://localhost/secret')), feed(posting(location=None))):
            with self.subTest(data=data), self.assertRaises(FeedUnavailable):
                normalize_feed(data)

    def test_general_interest_posts_are_excluded(self):
        jobs, prospects = normalize_feed(feed(posting(), posting(2, internal_job_id=None)))
        self.assertEqual((len(jobs), prospects), (1, 1))

    def test_fetch_only_uses_configured_board_and_a_fixed_https_endpoint(self):
        with patch('services.live_jobs.build_opener') as opener:
            with self.assertRaises(ValueError):
                fetch_board('https://attacker.example')
            opener.assert_not_called()
            response = opener.return_value.open.return_value.__enter__.return_value
            response.status = 200
            response.read.side_effect = [json.dumps(feed(posting())).encode(), b'']
            self.assertEqual(fetch_board('canonical')['meta']['total'], 1)
            args, kwargs = opener.return_value.open.call_args
            self.assertEqual(args[0].full_url, 'https://boards-api.greenhouse.io/v1/boards/canonical/jobs?content=true')
            self.assertEqual(kwargs['timeout'], 8)

    def test_fetch_error_does_not_expose_provider_exception(self):
        with patch('services.live_jobs.build_opener', side_effect=RuntimeError('private proxy details')):
            with self.assertRaises(FeedUnavailable) as caught:
                fetch_board('canonical')
        self.assertNotIn('private', str(caught.exception))


class LiveJobsApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.headers = self.register('jobs-one@example.test')
        self.other = self.register('jobs-two@example.test')

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register(self, email):
        account = {'name': 'Jobs Demo', 'email': email, 'password': 'jobs-test-only-password'}
        self.assertEqual(self.client.post('/api/register', json=account).status_code, 201)
        token = self.client.post('/api/login', json=account).get_json()['access_token']
        return {'Authorization': 'Bearer ' + token}

    def refresh(self, payload=None, board='canonical', failure=None):
        with patch('services.live_jobs.fetch_board', side_effect=failure, return_value=payload if payload is not None else feed(posting())) as fetch:
            response = self.client.post(f'/api/jobs/boards/{board}/refresh', headers=self.headers, json={})
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json(), fetch

    def reset_cooldown(self, board='canonical'):
        with self.app.app_context():
            db.session.get(JobBoardSync, board).last_attempt_at = utc_now() - timedelta(minutes=6)
            db.session.commit()

    def listing(self):
        response = self.client.get('/api/jobs', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        return response.get_json()

    def first_job(self):
        row = self.listing()['jobs'][0]
        return self.client.get('/api/jobs/' + row['id'], headers=self.headers).get_json()['job']

    def body(self, job, **changes):
        return {'submission_id': str(uuid4()), 'job_version': job['version'], 'mode': 'keyword', **changes}

    def compare(self, job, body=None, headers=None):
        return self.client.post(f'/api/jobs/{job["id"]}/compare', headers=headers or self.headers, json=body or self.body(job))

    def test_endpoints_require_authentication_and_sources_cannot_be_injected(self):
        self.assertEqual(self.client.get('/api/jobs').status_code, 401)
        self.assertEqual(self.client.post('/api/jobs/boards/canonical/refresh', json={}).status_code, 401)
        self.assertEqual(self.client.post('/api/jobs/boards/unknown/refresh', headers=self.headers, json={}).status_code, 404)
        self.assertEqual(self.client.post('/api/jobs/boards/canonical/refresh', headers=self.headers, json={'url': 'https://example.com'}).status_code, 400)

    def test_empty_list_never_fetches_automatically(self):
        with patch('services.live_jobs.fetch_board') as fetch:
            data = self.listing()
        fetch.assert_not_called()
        self.assertEqual(data['jobs'], [])
        self.assertTrue(all(row['stale'] and row['can_refresh'] for row in data['boards']))

    def test_successful_refresh_and_shared_cooldown_prevent_repeat_fetch(self):
        result, _ = self.refresh()
        self.assertEqual(result['outcome'], 'refreshed')
        self.assertEqual(result['board']['listed_count'], 1)
        self.assertFalse(result['board']['stale'])
        again, fetch = self.refresh()
        self.assertEqual(again['outcome'], 'cooldown')
        fetch.assert_not_called()
        self.assertEqual(self.listing()['total'], 1)

    def test_changed_text_creates_a_version_but_same_text_does_not(self):
        self.refresh()
        first = self.first_job()
        self.reset_cooldown()
        self.refresh()
        self.assertEqual(self.first_job()['version'], first['version'])
        self.reset_cooldown()
        self.refresh(feed(posting(content='<p>Python and Docker are required for backend services.</p>')))
        changed = self.first_job()
        self.assertEqual(changed['id'], first['id'])
        self.assertEqual(changed['version'], first['version'] + 1)
        self.assertNotEqual(changed['content_hash'], first['content_hash'])

    def test_failed_and_incomplete_refreshes_preserve_cached_records_and_success_time(self):
        first, _ = self.refresh()
        job = self.first_job()
        for data, failure in ((None, FeedUnavailable('Provider unavailable.')), ({'jobs': [], 'meta': {'total': 2}}, None)):
            self.reset_cooldown()
            result, _ = self.refresh(data, failure=failure)
            self.assertEqual(result['outcome'], 'failed')
            self.assertEqual(result['board']['last_success_at'], first['board']['last_success_at'])
            self.assertEqual(self.first_job()['last_seen_at'], job['last_seen_at'])
            self.assertEqual(self.listing()['total'], 1)

    def test_complete_empty_feed_marks_removed_and_reappearance_versions_it(self):
        self.refresh()
        original = self.first_job()
        self.reset_cooldown()
        self.refresh(feed())
        self.assertEqual(self.listing()['total'], 0)
        removed = self.client.get('/api/jobs/' + original['id'], headers=self.headers).get_json()['job']
        self.assertFalse(removed['listed'])
        self.assertEqual(removed['last_seen_at'], original['last_seen_at'])
        self.assertEqual(self.compare(original).status_code, 409)
        self.reset_cooldown()
        self.refresh()
        self.assertEqual(self.first_job()['version'], original['version'] + 2)

    def test_failed_one_board_does_not_hide_other_board_jobs(self):
        self.refresh()
        self.refresh(feed(posting(2)), board='razorpaysoftwareprivatelimited')
        self.reset_cooldown()
        self.refresh(failure=FeedUnavailable('Offline'))
        self.assertEqual(self.listing()['total'], 2)

    def test_literal_search_location_filter_and_stable_pagination(self):
        jobs = [posting(i + 1, title=f'Engineer {i:02}', location={'name': 'Pune' if i % 2 else 'Bengaluru'}) for i in range(23)]
        self.refresh(feed(*jobs))
        self.assertEqual(len(self.listing()['jobs']), 20)
        page2 = self.client.get('/api/jobs?page=2', headers=self.headers).get_json()
        self.assertEqual(len(page2['jobs']), 3)
        pune = self.client.get('/api/jobs?location=pune&q=SQL', headers=self.headers).get_json()
        self.assertEqual(pune['total'], 11)
        literal = self.client.get('/api/jobs?q=%25', headers=self.headers).get_json()
        self.assertEqual(literal['total'], 0)
        for args in ('page=0', 'page=oops', 'board=unknown', 'q=' + 'a' * 101):
            self.assertEqual(self.client.get('/api/jobs?' + args, headers=self.headers).status_code, 400)

    def test_stale_cache_is_labelled_and_frozen_in_comparison(self):
        self.refresh()
        with self.app.app_context():
            row = db.session.query(LiveJob).one()
            row.last_seen_at = utc_now() - timedelta(days=2)
            db.session.get(JobBoardSync, 'canonical').last_success_at = row.last_seen_at
            db.session.commit()
        job = self.first_job()
        self.assertTrue(job['stale'])
        self.assertTrue(self.listing()['boards'][0]['stale'])
        saved = self.compare(job).get_json()['comparison']
        self.assertTrue(saved['job']['stale_at_comparison'])

    def test_comparison_uses_server_text_and_owned_evidence_snapshot(self):
        self.refresh()
        job = self.first_job()
        self.client.post('/api/skills', headers=self.headers, json={'skill_name': 'SQL', 'proficiency': 7})
        self.client.post('/api/skills', headers=self.other, json={'skill_name': 'SQL', 'proficiency': 2})
        response = self.compare(job)
        self.assertEqual(response.status_code, 201)
        saved = response.get_json()['comparison']
        self.assertEqual(saved['job']['source_type'], 'greenhouse')
        self.assertEqual(saved['job']['description'], job['description'])
        self.assertEqual(saved['job']['content_hash'], job['content_hash'])
        self.assertEqual(saved['result']['policy_version'], 'live-job-comparison-v1')
        self.assertEqual(saved['candidate_snapshot']['skills'][0]['proficiency'], 7)
        self.assertEqual(self.client.get('/api/job-matches/' + saved['id'], headers=self.other).status_code, 404)
        self.assertEqual(self.client.get('/api/jobs/' + job['id'], headers=self.other).status_code, 200)
        for change in ({'description': 'Forged text'}, {'source_type': 'greenhouse'}, {'job_version': True}, {'mode': []}):
            self.assertEqual(self.compare(job, self.body(job, **change)).status_code, 400)

    def test_retry_after_job_changes_returns_original_and_conflicting_input_is_rejected(self):
        self.refresh()
        job = self.first_job()
        body = self.body(job)
        first = self.compare(job, body).get_json()['comparison']
        self.reset_cooldown()
        self.refresh(feed())
        retry = self.compare(job, body)
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.get_json()['comparison'], first)
        self.assertEqual(self.compare(job, {**body, 'mode': 'semantic'}).status_code, 409)
        with self.app.app_context():
            self.assertEqual(db.session.query(JobComparison).count(), 1)

    def test_changed_posting_requires_reopening_before_a_new_comparison(self):
        self.refresh()
        job = self.first_job()
        self.reset_cooldown()
        self.refresh(feed(posting(title='Changed title')))
        self.assertEqual(self.compare(job).status_code, 409)
        self.assertEqual(self.compare(self.first_job()).status_code, 201)

    def test_snapshot_survives_refresh_and_current_profile_edits(self):
        self.refresh()
        first = self.compare(self.first_job()).get_json()['comparison']
        self.reset_cooldown()
        self.refresh(feed(posting(content='<p>Docker is the only named skill in this new text.</p>')))
        self.client.post('/api/skills', headers=self.headers, json={'skill_name': 'Docker', 'proficiency': 9})
        reopened = self.client.get('/api/job-matches/' + first['id'], headers=self.headers).get_json()['comparison']
        self.assertEqual(reopened, first)

    def test_long_live_description_is_not_silently_truncated(self):
        self.refresh(feed(posting(content='<p>' + '</p><p>'.join(['Experience with backend services.'] * 75 + ['SQL required.']) + '</p>')))
        saved = self.compare(self.first_job()).get_json()['comparison']
        self.assertEqual(saved['result']['skills'][0]['skill_key'], 'sql')
        self.assertEqual(saved['result']['input_limits'], {'max_fragments': 300, 'truncated': False})
        self.reset_cooldown()
        self.refresh(feed(posting(content='<p>' + '</p><p>'.join(['Python required.'] * 301) + '</p>')))
        self.assertEqual(self.compare(self.first_job()).status_code, 400)

    def test_missing_model_fails_explicitly_and_keyword_still_works(self):
        self.refresh()
        job = self.first_job()
        with patch('services.job_matching.get_encoder', side_effect=SemanticUnavailable('Model setup required.')):
            self.assertEqual(self.compare(job, self.body(job, mode='semantic')).status_code, 503)
        self.assertEqual(self.compare(job).status_code, 201)

    def test_in_progress_refresh_is_rejected(self):
        with BOARD_LOCKS['canonical']:
            response = self.client.post('/api/jobs/boards/canonical/refresh', headers=self.headers, json={})
        self.assertEqual(response.status_code, 409)


if __name__ == '__main__':
    unittest.main()
