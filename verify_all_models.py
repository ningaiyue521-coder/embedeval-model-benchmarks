"""Verify the combined seven-model leaderboard from saved first answers. No model calls."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_MODELS = {'gpt-6-astra', 'gpt-6.1-sol', 'gpt-6-sol', 'gpt-5.5',
                   'gpt-5.6-sol', 'gpt-6-luna', 'gpt-5.6-luna'}

def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def verify():
    summary = read('results/seven-models-low-xhigh-20261008.json')
    catalog_raw = (ROOT / 'data/catalog.json').read_bytes()
    catalog = json.loads(catalog_raw)
    cases = catalog['cases']
    require(sha(catalog_raw) == summary['catalogSha256'], 'Catalog hash')
    require(catalog['revision'] == summary['sourceRevision'], 'Source revision')
    require(len(cases) == summary['questionsPerCombination'] == 614, 'Question count')
    require(len({c['key'] for c in cases}) == 614, 'Unique questions')
    for case in cases:
        require(sha(case['prompt'].encode('utf-8')) == case['promptHash'], 'Prompt content hash')
    for source in summary['sourceSummaries']:
        require(sha((ROOT / source['path']).read_bytes()) == source['sha256'], 'Source summary hash')
    require(len(summary['models']) == 7 and {m['model'] for m in summary['models']} == EXPECTED_MODELS, 'Model set')
    cache, computed, seen = {}, {}, set()
    total = errors = 0
    for model in summary['models']:
        for effort in ('low', 'xhigh'):
            group = model[effort]
            name = group['answerFile']
            path = (ROOT / name).resolve()
            require(path.is_relative_to((ROOT / 'answers').resolve()), 'Invalid answer path')
            if name not in cache:
                raw = path.read_bytes()
                cache[name] = (sha(raw), [json.loads(line) for line in raw.decode('utf-8').splitlines()])
            digest, all_rows = cache[name]
            require(digest == group['answerFileSha256'], f'Archive hash: {name}')
            require(group['model'] == model['model'] and group['effort'] == effort, 'Group identity')
            rows = sorted((r for r in all_rows if r['model'] == model['model'] and r['effort'] == effort), key=lambda r:r['ordinal'])
            require(len(rows) == group['count'] == 614, 'Complete group')
            passed = format_errors = 0
            for ordinal, (case, row) in enumerate(zip(cases, rows), 1):
                tag = f'{model["model"]}/{effort}/{ordinal}'
                key = (model['model'], effort, row['caseKey'])
                require(key not in seen, f'Duplicate first answer: {tag}')
                seen.add(key)
                require(row['ordinal'] == ordinal and row['caseKey'] == case['key'] and row['caseId'] == case['id'], f'Case order: {tag}')
                require(row['round'] == group['round'] and row.get('sourceRun') == group['sourceRun'], f'Source round: {tag}')
                require(row['attempt'] == 1, f'Attempt: {tag}')
                require(row['revision'] == catalog['revision'] and row['promptHash'] == case['promptHash'] and row['rulesHash'] == case['rulesHash'], f'Protocol: {tag}')
                require(sha(row['firstAnswer'].encode('utf-8')) == row['answerHash'], f'Answer hash: {tag}')
                require(type(row['passed']) is bool and isinstance(row['checks'], list), f'Grade: {tag}')
                if row.get('status', 'graded') == 'graded':
                    require(bool(row['checks']) and row['passed'] == all(c['passed'] for c in row['checks']), f'Checks: {tag}')
                    require(all(c['layer'] in (0, 3) and type(c['passed']) is bool for c in row['checks']), f'Layers: {tag}')
                    if row['passed']:
                        require({c['layer'] for c in row['checks']} == {0, 3}, f'Passing layers: {tag}')
                else:
                    require(row['status'] == 'answer_format_error' and not row['passed'] and not row['checks'], f'Format error: {tag}')
                    format_errors += 1
                require('threadId' not in row and 'runtimeWarnings' not in row, f'Private metadata: {tag}')
                passed += row['passed']
            require(passed == group['passed'] and round(100*passed/614, 2) == group['score'], 'Group score')
            require(format_errors == group['formatErrorsCountedZero'], 'Format error count')
            computed[(model['model'], effort)] = passed
            total += len(rows)
            errors += format_errors
        combined = model['low']['passed'] + model['xhigh']['passed']
        require(round(100*combined/1228, 2) == model['averageScore'], 'Average uses unrounded counts')
        require(round(100*(model['xhigh']['passed']-model['low']['passed'])/614, 2) == model['changePoints'], 'Effort change')
    require(total == len(seen) == summary['verifiedFirstAnswers'] == 8596, 'Total first answers')
    require(summary['combinations'] == len(computed) == 14 and errors == summary['formatErrorsCountedZero'] == 1, 'Summary counts')
    expected = sorted(summary['models'], key=lambda r:(r['low']['passed']+r['xhigh']['passed'], r['xhigh']['passed']), reverse=True)
    require(summary['models'] == expected and [r['rank'] for r in expected] == list(range(1,8)), 'Ranking')
    for row in read('results/low-614.json')['rows']:
        require(row['passed'] == computed[(row['model'], 'low')], 'Historical Low summary')
    for row in read('results/six-models-low-xhigh-20260928.json')['models']:
        for effort in ('low', 'xhigh'):
            require(row[effort]['passed'] == computed[(row['model'], effort)], 'Historical six-model summary')
    for row in read('results/gpt-6.1-sol-low-xhigh-20261008.json')['groups']:
        require(row['passed'] == computed[(row['model'], row['effort'])], 'New GPT-6.1 summary')
    return dict(ok=True, questions=614, models=7, combinations=14, firstAnswers=total,
                formatErrorsCountedZero=errors, modelCalls=0)

if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
