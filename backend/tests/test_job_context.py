"""Synthetic regression and counterexample checks; not independent research labels."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.job_matching import EXTRACTION_VERSION, build_comparison, fragments
from services.skill_catalog import SKILLS, keyword_keys


EMPTY = {'skills': [], 'evidence': [], 'sql_assessment': None}


def compare(text, mode='keyword', encoder=None):
    return build_comparison(text, EMPTY, mode, encoder=encoder)


def keys(result):
    return {row['skill_key'] for row in result['skills']}


class JobContextTests(unittest.TestCase):
    def test_explicit_http_rest_slash_wording_and_boundaries(self):
        for phrase in ('HTTP/REST', 'http/rest', 'HTTP / REST', 'HTTP\t/\tREST'):
            with self.subTest(phrase=phrase):
                self.assertEqual(keyword_keys('Networking knowledge: ' + phrase), ['rest_api'])
        for text in ('Take a rest after work.', 'Build HTTP and JSON endpoints.', 'Maintain APIs.',
                     'HTTP/RESTaurant', 'XHTTP/REST', 'REST is a break in activity.'):
            with self.subTest(text=text):
                self.assertNotIn('rest_api', keyword_keys(text))

    def test_company_portfolio_is_preserved_for_review_not_mapped(self):
        text = 'Northstar has several projects in Python and Java. Build services in Rust.'
        result = compare(text)
        self.assertEqual(keys(result), set())
        self.assertEqual(result['manual_review'][0]['text'], 'Northstar has several projects in Python and Java.')
        self.assertEqual(result['manual_review'][0]['reason_code'], 'company_context')
        self.assertIn('candidate', result['manual_review'][0]['reason'])
        self.assertEqual(result['extraction_version'], EXTRACTION_VERSION)

    def test_background_section_ends_at_role_and_qualification_headings(self):
        for heading in ('Responsibilities', 'The role entails', 'What you will focus on', 'Who you are',
                        'What we are looking for in you', 'Additional skills that you might also bring'):
            with self.subTest(heading=heading):
                result = compare('Company overview:\nPython and Java platforms.\n' + heading + ':\nSQL and Git.')
                self.assertEqual(keys(result), {'sql', 'git'})
                self.assertEqual(result['manual_review'][0]['reason_code'], 'background_section')

    def test_direct_candidate_work_survives_inside_background_section(self):
        for text in ('You will write Python code.', 'Develop Python services.',
                     'Experience with Python.', 'Python knowledge is required.',
                     'This role maintains Python services.'):
            with self.subTest(text=text):
                self.assertEqual(keys(compare('About us:\n' + text)), {'python'})

    def test_candidate_or_team_portfolio_is_not_mistaken_for_company_background(self):
        for text in ('You have several projects in Python.',
                     'The ideal candidate has projects in Python.',
                     'An applicant has products built with Python.',
                     'The team has projects in Python.',
                     'Our team has products using Python.',
                     'We have projects in Python which you will maintain.'):
            with self.subTest(text=text):
                self.assertEqual(keys(compare(text)), {'python'})

    def test_unqualified_team_stack_is_not_silently_filtered(self):
        self.assertEqual(keys(compare('We use Python and Docker to build our services.')), {'python', 'docker'})
        self.assertEqual(keys(compare('Maintain our Python projects.')), {'python'})

    def test_mixed_company_and_candidate_clauses_keep_candidate_skills(self):
        for boundary in (', but ', ', and ', ' while ', '; ', '. '):
            with self.subTest(boundary=boundary):
                result = compare('Our company develops Python products' + boundary + 'you will build Java services.')
                self.assertEqual(keys(result), {'java'})
                self.assertEqual(len(result['manual_review']), 1)

    def test_background_mention_does_not_cancel_separate_role_requirement(self):
        result = compare('Our company uses Python and Java.\nRequirements:\nPython is required.')
        self.assertEqual(keys(result), {'python'})
        self.assertEqual([source['text'] for source in result['skills'][0]['job_sources']], ['Python is required.'])
        self.assertEqual(len(result['manual_review']), 1)

    def test_nice_to_have_variants_remain_optional(self):
        for heading in ('Nice-to-have skills', 'Additional skills that you might also bring'):
            result = compare(heading + ':\nHTTP/REST\nDocker')
            self.assertEqual(keys(result), {'rest_api', 'docker'})
            self.assertTrue(all(source['importance'] == 'optional' for row in result['skills'] for source in row['job_sources']))

    def test_long_background_passage_keeps_context_across_fragment_chunks(self):
        text = 'Orion has many projects in ' + ' '.join(['Rust'] * 70) + ' and Python.'
        result = compare(text)
        self.assertEqual(keys(result), set())
        self.assertEqual(len(result['manual_review']), 2)
        self.assertIn('Python', result['manual_review'][-1]['text'])
        self.assertTrue(all(row['reason_code'] == 'company_context' for row in result['manual_review']))

    def test_semantic_suggestions_cannot_restore_excluded_background(self):
        class PythonEncoder:
            def __init__(self):
                self.inputs = []
            def encode(self, texts):
                self.inputs.extend(texts)
                anchors = [skill['anchor'] for skill in SKILLS]
                return [[float(i == (anchors.index(text) if text in anchors else 0))
                         for i in range(len(SKILLS))] for text in texts]
        encoder = PythonEncoder()
        background = 'Our company develops Python products.'
        result = compare(background, 'semantic', encoder)
        self.assertEqual(keys(result), set())
        self.assertNotIn(background, encoder.inputs)
        self.assertEqual(result['manual_review'][0]['reason_code'], 'company_context')
        # The stub would suggest Python for ordinary text, proving this assertion
        # checks filtering before encoding rather than an encoder returning nothing.
        self.assertEqual(keys(compare('Use an unfamiliar language.', 'semantic', encoder)), {'python'})

    def test_negation_still_requires_review_instead_of_becoming_a_requirement(self):
        result = compare('HTTP/REST is not required. Docker is required.')
        self.assertEqual(keys(result), {'docker'})
        self.assertEqual(result['manual_review'][0]['reason_code'], 'negation')
        self.assertTrue(fragments('No Python required.')[0]['review_needed'])


if __name__ == '__main__':
    unittest.main()
