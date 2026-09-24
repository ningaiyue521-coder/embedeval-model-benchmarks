"""Integration checks; all submissions use disposable test databases."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import bench
import server


class StoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = bench.catalog()
        cls.starters = [c for c in cls.manifest['cases'] if c['starter']]

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='embedeval-test-')
        self.path = Path(self.temp.name) / 'answers.sqlite3'
        self.store = bench.Store(self.path, self.manifest)
        self.item = self.starters[0]
        self.reference = self.ref(self.item)

    def tearDown(self):
        self.temp.cleanup()

    def ref(self, item):
        return (bench.UPSTREAM / item['caseDir'] / 'reference' / 'main.c').read_text(encoding='utf-8')

    def mutant(self, item):
        module = bench.module_at(bench.UPSTREAM / item['caseDir'] / 'checks' / 'negatives.py')
        negative = next(n for n in module.NEGATIVES if n.get('name') == item['mutation'])
        return negative['mutation'](self.ref(item))

    def test_ten_references_pass_and_seeded_defects_fail(self):
        self.assertEqual(len(self.starters), 10)
        for item in self.starters:
            with self.subTest(case=item['id']):
                reference, _ = self.store.submit('SELFTEST-REFERENCE', item['key'], self.ref(item))
                defective, _ = self.store.submit('SELFTEST-DEFECT', item['key'], self.mutant(item))
                self.assertIs(reference['passed'], True)
                self.assertIs(defective['passed'], False)
                self.assertEqual([r['layer'] for r in reference['layers']], [0, 3])
        board = {r['model']: r for r in self.store.leaderboard()}
        self.assertEqual(board['SELFTEST-REFERENCE']['starterScore'], 100)
        self.assertEqual(board['SELFTEST-DEFECT']['starterScore'], 0)
        self.assertTrue(all(r['complete'] for r in board.values()))

    def test_first_raw_answer_survives_restart_and_cannot_be_replaced(self):
        raw = '首次回答\n```c\n' + self.reference + '\n```\n'
        result, created = self.store.submit('  Ｍodel   A  ', self.item['key'], raw)
        self.assertTrue(created)
        self.assertIs(result['passed'], True)
        reopened = bench.Store(self.path, self.manifest)
        duplicate, created = reopened.submit('model a', self.item['key'], raw)
        self.assertFalse(created)
        self.assertEqual(duplicate, result)
        self.assertEqual(reopened.results('MODEL A', include_answers=True)[0]['rawAnswer'], raw)
        with self.assertRaises(FileExistsError):
            reopened.submit('model a', self.item['key'], self.mutant(self.item))
        self.assertEqual(len(reopened.results()), 1)

    def test_simultaneous_submissions_have_one_winner(self):
        gate = threading.Barrier(2)
        def submit(raw):
            gate.wait(timeout=5)
            try:
                return self.store.submit('race-model', self.item['key'], raw)[1]
            except FileExistsError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(submit, raw) for raw in [self.reference, self.mutant(self.item)]]
            winners = [f.result(timeout=15) for f in futures]
        self.assertEqual(winners.count(True), 1)
        self.assertEqual(len(self.store.results()), 1)

    def test_checker_error_keeps_first_answer_and_never_counts_as_pass(self):
        with patch.object(bench, 'run_checks', side_effect=RuntimeError('test checker unavailable')):
            result, _ = self.store.submit('error-model', self.item['key'], self.reference)
        self.assertEqual(result['status'], 'error')
        self.assertIsNone(result['passed'])
        row = self.store.leaderboard()[0]
        self.assertEqual((row['starterGraded'], row['starterScore'], row['errors']), (0, 0, 1))
        with self.assertRaises(FileExistsError):
            self.store.submit('error-model', self.item['key'], self.mutant(self.item))

    def test_invalid_format_does_not_create_an_attempt(self):
        for raw in ['', '   ', '```c\n\n```', '```c\nint a;\n```\n```c\nint b;\n```']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.store.submit('format-model', self.item['key'], raw)
        self.assertEqual(self.store.results(), [])

    def test_changed_rules_cannot_create_a_new_grade(self):
        with patch.object(bench, 'rule_hash', return_value='different'):
            with self.assertRaisesRegex(RuntimeError, '评分文件发生变化'):
                self.store.submit('changed-rules', self.item['key'], self.reference)
        self.assertEqual(self.store.results(), [])


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='embedeval-http-test-')
        cls.httpd = server.make_server(0, Path(cls.temp.name) / 'answers.sqlite3')
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.httpd.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def request(self, path, data=None, origin=None):
        headers = {'Content-Type': 'application/json'}
        if origin:
            headers['Origin'] = origin
        request = Request(self.url + path, None if data is None else json.dumps(data).encode(), headers)
        try:
            response = urlopen(request, timeout=15)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, json.loads(response.read()), response.headers

    def test_browser_api_first_submission_report_and_overwrite_rejection(self):
        status, health, _ = self.request('/api/health')
        self.assertEqual((status, health['app']), (200, 'embedeval-manual'))
        status, catalog, _ = self.request('/api/catalog')
        self.assertEqual(status, 200)
        self.assertEqual(catalog['bugfixCount'], 614)
        for c in catalog['cases']:
            self.assertFalse({'caseDir', 'referenceHash', 'rulesHash'} & c.keys())
        item = bench.catalog()['cases'][0]
        code = (bench.UPSTREAM / item['caseDir'] / 'reference' / 'main.c').read_text(encoding='utf-8')
        payload = {'model': 'HTTP-自检模型', 'caseKey': item['key'], 'answer': code}
        status, first, _ = self.request('/api/submit', payload, self.url)
        self.assertEqual(status, 201)
        self.assertIs(first['passed'], True)
        status, duplicate, _ = self.request('/api/submit', payload, self.url)
        self.assertEqual((status, duplicate), (200, first))
        status, _, _ = self.request('/api/submit', {**payload, 'answer': 'int main(void) { return 0; }'}, self.url)
        self.assertEqual(status, 409)
        status, report, headers = self.request('/api/report?model=' + quote(payload['model']))
        self.assertEqual(status, 200)
        self.assertEqual(report['summary']['starterScore'], 10)
        self.assertFalse(report['summary']['complete'])
        self.assertEqual(report['results'][0]['rawAnswer'], code)
        self.assertIn('attachment', headers['Content-Disposition'])

    def test_unrelated_websites_cannot_submit_and_source_files_are_not_served(self):
        status, _, _ = self.request('/api/submit', {'model': 'blocked'}, 'https://example.org')
        self.assertEqual(status, 403)
        status, _, _ = self.request('/../EmbedEval/cases/zephyr/timer-001/reference/main.c')
        self.assertEqual(status, 404)


if __name__ == '__main__':
    unittest.main()
