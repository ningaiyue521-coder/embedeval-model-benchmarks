"""Verify published Max rounds and Cursor samples. No candidate model calls."""
from pathlib import Path
import hashlib
import json
import statistics

ROOT = Path(__file__).resolve().parent

def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def sha(value):
    return hashlib.sha256(value.encode('utf-8') if isinstance(value,str) else value).hexdigest()

def require(ok, message):
    if not ok:
        raise ValueError(message)

def verify():
    catalog_raw = (ROOT/'data/catalog.json').read_bytes()
    catalog = json.loads(catalog_raw)
    cases = catalog['cases']
    total = 0
    for name, expected in (('max-614-20261009.json',1842), ('cursor-samples-20260928.json',36)):
        summary = read('results/'+name)
        require(summary['catalogSha256'] == sha(catalog_raw), 'Catalog hash')
        require(summary['sourceRevision'] == catalog['revision'], 'Revision')
        require(summary['modelCallsDuringExport'] == 0, 'Export called models')
        count = 0
        seen = set()
        for group in summary['groups']:
            path = (ROOT/group['answerFile']).resolve()
            require(path.is_relative_to((ROOT/'answers').resolve()), 'Answer path')
            raw = path.read_bytes()
            require(sha(raw) == group['answerFileSha256'], f'File hash: {path.name}')
            rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
            require(len(rows) == group['count'], 'Count')
            for row in rows:
                case = cases[row['ordinal']-1]
                key = (row['model'], row['effort'], row['caseKey'])
                require(key not in seen, 'Duplicate first answer'); seen.add(key)
                require(row['model'] == group['model'] and row['sourceRun'] == group['sourceRun'], 'Identity')
                require(row['attempt'] == 1 and row['caseKey'] == case['key'] and row['caseId'] == case['id'], 'Case')
                require(sha(case['prompt']) == row['promptHash'] == case['promptHash'], 'Prompt')
                require(row['rulesHash'] == case['rulesHash'] and row['revision'] == catalog['revision'], 'Rules')
                require(sha(row['firstAnswer']) == row['answerHash'], 'Answer hash')
                cs = row['checks']
                require(cs and type(row['passed']) is bool and row['passed'] == all(c['passed'] for c in cs), 'Checks')
                require(all(c['layer'] in (0,3) and type(c['passed']) is bool for c in cs), 'Layers')
                require(not any(k in row for k in ('threadId','session_id','events','command','apiKey')), 'Private metadata')
            passed = sum(r['passed'] for r in rows)
            require(passed == group['passed'], 'Pass count')
            if name.startswith('max-'):
                require(len(rows) == 614 and [r['ordinal'] for r in rows] == list(range(1,615)), 'Full question order')
                require(round(100*passed/614,2) == group['score'], 'Score')
                require(round(statistics.mean(r['secondsIncludingGrading'] for r in rows),2) == group['meanSecondsIncludingGrading'], 'Mean seconds')
                require(round(statistics.median(r['secondsIncludingGrading'] for r in rows),2) == group['medianSecondsIncludingGrading'], 'Median seconds')
                for k,value in group['tokens'].items():
                    require(sum(r['tokens'][k] for r in rows) == value, 'Token sum')
            else:
                require([r['ordinal'] for r in rows] == group['sampleOrdinals'], 'Sample order')
                require(group['full614Score'] is None and round(100*passed/len(rows),2) == group['sampleScore'], 'Sample score')
            count += len(rows)
        require(count == summary['verifiedFirstAnswers'] == expected, 'Summary count')
        total += count
    return {'ok':True,'maxFirstAnswers':1842,'cursorSampleFirstAnswers':36,'firstAnswers':total,'modelCalls':0}

if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
