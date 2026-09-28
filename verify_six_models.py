"""Verify the seven newly published first-answer groups without invoking a model."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def verify():
    catalog = read('data/catalog.json')
    audit = read('results/six-models-answer-audit-20260928.json')
    summary = read('results/six-models-low-xhigh-20260928.json')
    cases = catalog['cases']
    require(len(cases) == audit['caseCount'] == summary['questionsPerCombination'] == 614, 'Question count')
    require(catalog['revision'] == audit['sourceRevision'] == summary['sourceRevision'], 'Source revision')
    require(len(audit['groups']) == 7 and summary['verifiedFirstAnswers'] == 7368, 'Group count')
    results = {}
    for group in audit['groups']:
        path = (ROOT / group['answerFile']).resolve()
        require(path.is_relative_to((ROOT / 'answers').resolve()), 'Invalid answer path')
        raw = path.read_bytes()
        require(sha(raw) == group['answerFileSha256'], f'File hash: {path.name}')
        rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
        require(len(rows) == group['count'] == 614, f'Row count: {path.name}')
        passed = errors = 0
        for ordinal, (case, row) in enumerate(zip(cases, rows), 1):
            tag = f'{path.name}:{ordinal}'
            require(row['ordinal'] == ordinal and row['caseKey'] == case['key'] and row['caseId'] == case['id'], f'Case: {tag}')
            require(row['model'] == group['model'] and row['effort'] == group['effort'], f'Combination: {tag}')
            require(row['sourceRun'] == group['sourceRun'] and row['attempt'] == 1, f'Attempt: {tag}')
            require(row['revision'] == catalog['revision'] and row['promptHash'] == case['promptHash'] and row['rulesHash'] == case['rulesHash'], f'Protocol: {tag}')
            require(sha(row['firstAnswer'].encode('utf-8')) == row['answerHash'], f'Answer hash: {tag}')
            require(type(row['passed']) is bool and isinstance(row['checks'], list), f'Grade: {tag}')
            if row['status'] == 'graded':
                require(bool(row['checks']) and row['passed'] == all(c['passed'] for c in row['checks']), f'Checks: {tag}')
                require(all(c['layer'] in (0, 3) and type(c['passed']) is bool for c in row['checks']), f'Layer: {tag}')
            else:
                require(row['status'] == 'answer_format_error' and not row['passed'] and not row['checks'], f'Format error: {tag}')
                errors += 1
            require('threadId' not in row and 'runtimeWarnings' not in row, f'Private metadata: {tag}')
            passed += row['passed']
        require(passed == group['passed'] and errors == group['formatErrorsCountedZero'], f'Score: {path.name}')
        results[(group['model'], group['effort'])] = passed
    require(sum(g['count'] for g in audit['groups']) == 4298, 'New first-answer count')
    require(sum(g['formatErrorsCountedZero'] for g in audit['groups']) == 1, 'Format error count')
    for model in summary['models']:
        for effort in ('low', 'xhigh'):
            key = (model['model'], effort)
            if key in results:
                require(model[effort]['passed'] == results[key], f'Summary mismatch: {key}')
    partial = read('results/partial-terra-low-20260928.json')
    partial_file = (ROOT / partial['answerFile']).resolve()
    require(partial_file.is_relative_to((ROOT / 'answers').resolve()), 'Partial answer path')
    require(sha(partial_file.read_bytes()) == partial['answerFileSha256'], 'Partial file hash')
    partial_rows = [json.loads(line) for line in partial_file.read_text(encoding='utf-8').splitlines()]
    require(len(partial_rows) == partial['firstAnswers'] == 127, 'Partial count')
    require(sum(row['passed'] for row in partial_rows) == partial['passed'] == 99, 'Partial pass count')
    seen = set()
    for row in partial_rows:
        case = cases[row['ordinal'] - 1]
        require(row['caseKey'] == case['key'] and row['caseKey'] not in seen, 'Partial case')
        seen.add(row['caseKey'])
        require(row['attempt'] == 1 and sha(row['firstAnswer'].encode('utf-8')) == row['answerHash'], 'Partial answer')
        require(row['passed'] == all(c['passed'] for c in row['checks']) and bool(row['checks']), 'Partial grade')
    return {'ok': True, 'questions': 614, 'newFirstAnswers': 4298, 'groups': 7,
            'partialTerraFirstAnswers': 127, 'formatErrorsCountedZero': 1, 'modelCalls': 0}

if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
