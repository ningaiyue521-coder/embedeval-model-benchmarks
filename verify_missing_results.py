"""Verify the nine added tiers from published first answers, without model calls."""
from pathlib import Path
import argparse
import hashlib
import json
import statistics

ROOT=Path(__file__).resolve().parent
SUMMARY='results/missing-nine-tiers-20261106.json'
EXPECTED={('gpt-5.6-sol','high'),('gpt-5.6-sol','max'),('gpt-6-luna','high'),
          ('gpt-5.6-luna','high'),('gpt-5.6-luna','max'),('gpt-6-astra','high'),
          ('gpt-6-astra','max'),('gpt-6.1-sol','high'),('gpt-6-sol','high')}
FIELDS=set('model effort sourceRun ordinal caseKey caseId attempt firstAnswer answerHash promptHash rulesHash revision passed layers started finished secondsIncludingGrading tokens transportWarning'.split())
def sha(data): return hashlib.sha256(data.encode('utf8') if isinstance(data,str) else data).hexdigest()
def need(ok,message):
    if not ok: raise ValueError(message)
def read(name): return json.loads((ROOT/name).read_text(encoding='utf8'))
def verify(regrade=False):
    summary=read(SUMMARY)
    catalog=read('data/catalog.json')
    need(len(catalog['cases'])==614 and catalog['revision']==summary['sourceRevision'],'Frozen catalog')
    need(sha((ROOT/'data/catalog.json').read_bytes())==summary['catalogSha256'],'Catalog file hash')
    protocol=summary['protocol']
    need(protocol['questionsPerCombination']==614 and protocol['firstFinalAnswersPerQuestion']==1,'Protocol scope')
    need(protocol['freshEphemeralSessionPerRequest'] and protocol['retryOnlyTransportFailuresWithoutAnswer'],'Session policy')
    need(all(protocol[k] is False for k in ('toolsAllowed','feedbackToCandidate','compiled','simulated','hardwareVerified')),'Protocol limits')
    need(protocol['gradingLayers']==[0,3] and sha(protocol['candidateInstructions'])==protocol['candidateInstructionsSha256'],'Instruction hash')
    need(summary['firstAnswersVerified']==summary['uniqueSessions']==5526 and summary['toolCalls']==0,'Local audit')
    need(summary['modelCallsDuringAudit']==0 and summary['regradedWithFrozenL0L3'] is True,'Audit scope')
    need({(g['model'],g['effort']) for g in summary['groups']}==EXPECTED and len(summary['groups'])==9,'Tier scope')
    if regrade: import bench
    seen=set()
    for g in summary['groups']:
        path=(ROOT/g['answerFile']).resolve()
        need(path.is_relative_to((ROOT/'answers').resolve()),'Archive path')
        data=path.read_bytes()
        need(sha(data)==g['answerFileSha256'],'Archive hash')
        rows=[json.loads(line) for line in data.decode('utf8').splitlines()]
        need(len(rows)==g['total']==614,'Archive count')
        for ordinal,(r,c) in enumerate(zip(rows,catalog['cases']),1):
            need(set(r)==FIELDS,'Unexpected archive metadata')
            need(r['ordinal']==ordinal and r['caseKey']==c['key'] and r['caseId']==c['id'],'Question order')
            need((r['model'],r['effort'])==(g['model'],g['effort']) and r['attempt']==1,'First-answer identity')
            key=(r['model'],r['effort'],r['caseKey'])
            need(key not in seen,'Duplicate first answer'); seen.add(key)
            need(r['promptHash']==c['promptHash'] and r['rulesHash']==c['rulesHash'] and r['revision']==catalog['revision'],'Frozen hashes')
            need(r['firstAnswer'].strip() and sha(r['firstAnswer'])==r['answerHash'],'Answer hash')
            need(type(r['passed']) is bool and r['layers'] and all(l['layer'] in (0,3) for l in r['layers']),'Grade scope')
            checks=[d for layer in r['layers'] for d in layer['details']]
            need(checks and r['passed']==(len(r['layers'])==2 and all(d['passed'] for d in checks)),'Rule result')
            if regrade:
                need(bench.rule_hash(bench.UPSTREAM/c['caseDir'])==c['rulesHash'],'Grader hash')
                again=bench.run_checks(bench.UPSTREAM/c['caseDir'],bench.extract_code(r['firstAnswer']))
                need(again['layers']==r['layers'] and again['passed']==r['passed'],'Regrade mismatch')
        passed=sum(r['passed'] for r in rows)
        need(passed==g['passed'] and round(100*passed/614,2)==g['score'],'Score total')
        need({k:sum(r['tokens'][k] for r in rows) for k in g['tokens']}==g['tokens'],'Token totals')
        need(round(statistics.mean(r['secondsIncludingGrading'] for r in rows),2)==g['meanSeconds'],'Mean time')
        need(round(statistics.median(r['secondsIncludingGrading'] for r in rows),2)==g['medianSeconds'],'Median time')
        need(sum(r['transportWarning'] for r in rows)==g['transportWarningCases'],'Warning total')
    need(len(seen)==5526,'First-answer total')
    return {'ok':True,'combinations':9,'firstAnswers':5526,'regraded':regrade,'modelCalls':0}
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--regrade',action='store_true'); args=parser.parse_args()
    print(json.dumps(verify(args.regrade),ensure_ascii=False,indent=2))
