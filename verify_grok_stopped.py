"""Verify the stopped Grok archive without model calls or score changes."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parent
def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(x): return hashlib.sha256(x.encode('utf-8') if isinstance(x,str) else x).hexdigest()
def need(ok,message):
    if not ok: raise ValueError(message)
def verify():
    summary=read('results/grok-4.7-high-stopped-20261014.json')
    raw=(ROOT/'data/catalog.json').read_bytes(); catalog=json.loads(raw)
    need(sha(raw)==summary['catalogSha256'],'Catalog hash')
    path=(ROOT/summary['answerFile']).resolve(); need(path.is_relative_to((ROOT/'answers').resolve()),'Archive path')
    raw=path.read_bytes(); need(sha(raw)==summary['answerFileSha256'],'Archive hash')
    rows=[json.loads(s) for s in raw.decode('utf-8').splitlines()]
    need(len(rows)==summary['lockedAttempts']==614,'Attempt count')
    answered=passed=0; missing=[]
    for ordinal,(r,c) in enumerate(zip(rows,catalog['cases']),1):
        need(r['ordinal']==ordinal and r['caseKey']==c['key'] and r['caseId']==c['id'],'Case order')
        need(r['attempt']==1 and r['model']==summary['model']=='grok-4.7-high' and r['effort']=='high','Identity')
        need(r['revision']==catalog['revision']==summary['sourceRevision'],'Revision')
        need(r['promptHash']==c['promptHash']==sha(c['prompt']) and r['rulesHash']==c['rulesHash'],'Question hashes')
        if r['status']=='graded':
            need(r['firstAnswer'] and sha(r['firstAnswer'])==r['answerHash'],'Answer hash')
            need(r['checks'] and type(r['passed']) is bool and all(x['passed'] for x in r['checks'])==r['passed'],'Checks')
            need(all(x['layer'] in (0,3) for x in r['checks']),'Layers')
            need(' '.join(r['actualModelDisplay'].split()).lower() in ('grok 4.7 high','grok 4.7 256k high'),'Display')
            answered+=1; passed+=r['passed']
        else:
            expected={310:('generation_error','CURSOR_CONFIG_RENAME_EPERM'),506:('generation_error','CURSOR_TLS_CONNECTION_ABORTED'),525:('cancelled_by_user','USER_STOPPED_PROLONGED_REQUEST')}
            need(ordinal in expected and (r['status'],r['errorCode'])==expected[ordinal],'Missing answer reason')
            need(r['firstAnswer'] is None and r['answerHash'] is None and r['passed'] is None and r['checks']==[],'Missing answer treated as graded')
            need(r['finalAnswerAvailable'] is False and r['retryIssued'] is False,'Retry/final answer')
            missing.append({'ordinal':ordinal,'status':r['status'],'errorCode':r['errorCode']})
        need(not any(k in r for k in ('session_id','threadId','command','apiKey','events')),'Private metadata')
    need(answered==summary['gradedFirstAnswers']==611 and passed==summary['passed']==540,'Grade totals')
    need(round(100*passed/answered,2)==summary['answeredOnlyScore']==88.38,'Answered-only score')
    need(round(100*passed/614,2)==summary['full614Score']==87.95,'Full denominator score')
    need(summary['scoreDenominator']==614 and summary['missingFinalAnswersCountedZero']==len(missing)==3,'Missing answer scoring')
    need(summary['includedInComparison'] is True and missing==summary['missingFinalAnswers'],'Comparison inclusion')
    prior=[json.loads(s) for s in (ROOT/'answers/20260928-grok-4.7-high-sample.jsonl').read_text(encoding='utf-8').splitlines()]
    need(len(prior)==6,'Historical sample')
    need(all(a['caseKey']==b['caseKey'] and a['firstAnswer']==b['firstAnswer'] and a['answerHash']==b['answerHash'] for a,b in zip(prior,rows[:6])),'Historical answer changed')
    return {'ok':True,'attempts':614,'gradedFirstAnswers':answered,'passed':passed,'score':summary['full614Score'],'missingFinalAnswersCountedZero':3,'modelCalls':0}
if __name__=='__main__': print(json.dumps(verify(),ensure_ascii=False,indent=2))
