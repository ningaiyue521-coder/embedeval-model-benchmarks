"""Verify the published Terra first-answer archives without model calls."""
from pathlib import Path
import hashlib
import json
import argparse

ROOT = Path(__file__).resolve().parent
def sha(v): return hashlib.sha256(v.encode('utf-8') if isinstance(v,str) else v).hexdigest()
def verify(regrade=False):
    if regrade:
        import bench
        verified_rules = {}
    raw = (ROOT/'data/catalog.json').read_bytes()
    catalog = json.loads(raw)
    summary = json.loads((ROOT/'results/gpt-6.1-terra-four-efforts-20261027.json').read_text(encoding='utf-8'))
    assert summary['catalogSha256'] == sha(raw) and summary['sourceRevision'] == catalog['revision']
    assert len(catalog['cases']) == 614 and summary['verifiedFirstAnswers'] == 2456
    assert {g['effort'] for g in summary['groups']} == {'low','high','xhigh','max'}
    seen = set()
    for group in summary['groups']:
        path = (ROOT/group['answerFile']).resolve()
        assert path.is_relative_to((ROOT/'answers').resolve())
        raw = path.read_bytes(); assert sha(raw) == group['answerFileSha256']
        rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
        assert len(rows) == group['count'] == 614
        for ordinal, (case, row) in enumerate(zip(catalog['cases'], rows),1):
            key = row['model'],row['effort'],row['caseKey']
            assert key not in seen; seen.add(key)
            assert row['model'] == group['model'] == 'gpt-6.1-terra' and row['effort'] == group['effort']
            assert row['ordinal'] == ordinal and row['caseKey'] == case['key'] and row['caseId'] == case['id'] and row['attempt'] == 1
            assert sha(case['prompt']) == row['promptHash'] == case['promptHash'] and row['rulesHash'] == case['rulesHash']
            assert row['revision'] == catalog['revision'] and sha(row['firstAnswer']) == row['answerHash']
            assert row['checks'] and row['passed'] == all(c['passed'] for c in row['checks'])
            assert all(c['layer'] in (0,3) and type(c['passed']) is bool for c in row['checks'])
            assert not any(k in row for k in ('threadId','session_id','events','command','apiKey'))
            if regrade:
                case_dir = bench.UPSTREAM/case['caseDir']
                if case['caseDir'] not in verified_rules: verified_rules[case['caseDir']] = bench.rule_hash(case_dir)
                assert verified_rules[case['caseDir']] == case['rulesHash']
                result = bench.run_checks(case_dir, bench.extract_code(row['firstAnswer']))
                checks = [{'layer':l['layer'],'name':c['check_name'],'passed':c['passed'],'expected':c['expected'],'actual':c['actual']} for l in result['layers'] for c in l['details']]
                assert result['passed'] == row['passed'] and checks == row['checks']
        assert sum(r['passed'] for r in rows) == group['passed'] and round(100*group['passed']/614,2) == group['score']
        assert sum(r['transportRetryWarning'] for r in rows) == group['transportRetryWarningCases']
        for k,value in group['tokens'].items(): assert sum(r['tokens'][k] for r in rows) == value
    combined = json.loads((ROOT/'results/all-models-summary-20261027.json').read_text(encoding='utf-8'))
    old = json.loads((ROOT/'results/all-models-summary-20261014.json').read_text(encoding='utf-8'))
    assert combined['modelsCount'] == 9 and combined['combinations'] == 22 and combined['scoredAttempts'] == 13508
    assert [m for m in combined['models'] if m['model'] != 'gpt-6.1-terra'] == old['models']
    assert combined['models'] == sorted(combined['models'],key=lambda m:-m['best']['passed'])
    model = next(m for m in combined['models'] if m['model']=='gpt-6.1-terra')
    for group in summary['groups']:
        g = model['groups'][group['effort']]
        assert g == {'effort':group['effort'],'passed':group['passed'],'score':group['score'],'denominator':614}
    assert model['best'] == max(model['groups'].values(),key=lambda g:g['passed'])
    for source in combined['sourceSummaries']:
        assert sha((ROOT/source['path']).read_bytes()) == source['sha256']
    return {'ok':True,'questions':614,'combinations':4,'firstAnswers':len(seen),'regraded':regrade,'modelCalls':0}
if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--regrade',action='store_true')
    print(json.dumps(verify(parser.parse_args().regrade),ensure_ascii=False,indent=2))
