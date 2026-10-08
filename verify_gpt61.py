"""Verify the GPT-6.1 Sol archives without a model call; --regrade uses frozen rules."""
from pathlib import Path
from collections import Counter, defaultdict
import argparse, hashlib, json, math, statistics
ROOT=Path(__file__).resolve().parent
SUMMARY='results/gpt-6.1-sol-low-xhigh-20261008.json'
FIELDS=set('round sourceRun model effort ordinal caseKey caseId attempt firstAnswer answerHash promptHash rulesHash revision status passed checks started finished secondsIncludingGrading tokens'.split())
TOKENS=('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens')
def sha(value): return hashlib.sha256(value.encode('utf-8') if isinstance(value,str) else value).hexdigest()
def need(ok,message):
    if not ok: raise ValueError(message)
def load(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
def verify(regrade=False):
    summary=load(SUMMARY); catalog=load('data/catalog.json'); cases=catalog['cases']
    need(summary['sourceRevision']==catalog['revision'] and len(cases)==614, 'Frozen dataset')
    need(summary['catalogSha256']==sha((ROOT/'data/catalog.json').read_bytes()), 'Catalog hash')
    need(summary['verifiedFirstAnswers']==1228 and summary['freshUniqueSessions']==1228 and summary['integrityErrors']==0, 'Integrity audit')
    protocol=summary['protocol']
    need(protocol['attemptsPerModelEffortCase']==1 and all(protocol[k] is False for k in ('historicalAnswersImported','automaticQuestionRetries','feedbackToCandidate','toolsAllowed','ultraCollaborationAuthorized')), 'Protocol')
    need(sha(protocol['candidateInstructions'])==protocol['candidateInstructionsHash'], 'Instruction hash')
    need([g['effort'] for g in summary['groups']]==['low','xhigh'], 'Combinations')
    records={}; count=0
    if regrade:
        import bench
    for group in summary['groups']:
        path=(ROOT/group['answerFile']).resolve()
        need(path.is_relative_to((ROOT/'answers').resolve()), 'Archive path')
        data=path.read_bytes(); need(sha(data)==group['answerFileSha256'], 'Archive file hash')
        rows=[json.loads(line) for line in data.decode('utf-8').splitlines()]
        need(len(rows)==group['count']==614, 'Archive row count')
        passed=errors=0; tokens=Counter(); grouped={field:defaultdict(list) for field in ('sdk','category','difficulty')}
        for ordinal,(row,case) in enumerate(zip(rows,cases),1):
            tag=f'{path.name}:{ordinal}'
            need(set(row)==FIELDS, 'Unexpected metadata: '+tag)
            need(row['ordinal']==ordinal and row['caseKey']==case['key'] and row['caseId']==case['id'], 'Question order: '+tag)
            need(row['model']==group['model']==summary['model']=='gpt-6.1-sol' and row['effort']==group['effort'], 'Model: '+tag)
            need(row['sourceRun']==summary['sourceRun'] and row['attempt']==1, 'First attempt: '+tag)
            need(row['revision']==catalog['revision'] and row['promptHash']==case['promptHash'] and row['rulesHash']==case['rulesHash'], 'Frozen hashes: '+tag)
            need(row['answerHash']==sha(row['firstAnswer']) and row['firstAnswer'].strip(), 'First answer hash: '+tag)
            need(type(row['passed']) is bool and type(row['secondsIncludingGrading']) in (int,float), 'Grade types: '+tag)
            if row['status']=='graded':
                need(row['checks'] and row['passed']==all(c['passed'] for c in row['checks']), 'Checks: '+tag)
                need(all(c['layer'] in (0,3) and type(c['passed']) is bool for c in row['checks']), 'Layers: '+tag)
                if regrade:
                    need(bench.rule_hash(bench.UPSTREAM/case['caseDir'])==case['rulesHash'], 'Checker changed: '+tag)
                    grade=bench.run_checks(bench.UPSTREAM/case['caseDir'],bench.extract_code(row['firstAnswer']))
                    checks=[{'layer':layer['layer'],'name':d['check_name'],'passed':d['passed'],'expected':d['expected'],'actual':d['actual']} for layer in grade['layers'] for d in layer['details']]
                    need(grade['passed']==row['passed'] and checks==row['checks'], 'Regrade differs: '+tag)
            else:
                need(row['status']=='answer_format_error' and row['passed'] is False and row['checks']==[], 'Format error: '+tag)
                errors+=1
            need(set(row['tokens'])==set(TOKENS), 'Token fields: '+tag); tokens.update(row['tokens']); passed+=row['passed']; count+=1
            for field in grouped: grouped[field][case[field]].append(row['passed'])
        need(passed==group['passed'] and group['score']==round(passed/614*100,2) and errors==group['formatErrorsCountedZero'], 'Totals')
        need(dict(tokens)==group['tokens'], 'Token totals')
        seconds=[row['secondsIncludingGrading'] for row in rows]
        need(round(statistics.mean(seconds),2)==group['meanSecondsIncludingGrading'] and round(statistics.median(seconds),2)==group['medianSecondsIncludingGrading'] and sorted(seconds)[math.ceil(.95*614)-1]==group['p95SecondsIncludingGrading'], 'Timing totals')
        for field,key in (('sdk','bySdk'),('category','byCategory'),('difficulty','byDifficulty')):
            expected=[{'name':name,'total':len(values),'passed':sum(values),'score':round(100*sum(values)/len(values),2)} for name,values in sorted(grouped[field].items())]
            need(expected==group[key], 'Group totals: '+key)
        records[group['effort']]=rows
    transition=Counter(('passed' if l['passed'] else 'failed')+'To'+('Passed' if h['passed'] else 'Failed') for l,h in zip(records['low'],records['xhigh']))
    need(dict(transition)==summary['lowToXhigh'], 'Transition counts')
    need(summary['changePoints']==round(summary['groups'][1]['score']-summary['groups'][0]['score'],2), 'Score change')
    baseline=load('results/low-614.json')
    expected_comparison=[{'model':row['model'],'baselineFile':'results/low-614.json','baselinePassed':row['passed'],'baselineScore':row['score'],'newPassedMinusBaseline':summary['groups'][0]['passed']-row['passed'],'newScoreMinusBaselinePoints':round(summary['groups'][0]['score']-row['score'],2)} for row in baseline['rows'] if row['total']==row['graded']==614]
    need(expected_comparison==summary['publishedLowComparison'], 'Published comparison')
    return {'ok':True,'questions':614,'firstAnswers':count,'groups':2,'regraded':regrade,'modelCalls':0}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--regrade',action='store_true'); args=parser.parse_args()
    print(json.dumps(verify(args.regrade),ensure_ascii=False,indent=2))