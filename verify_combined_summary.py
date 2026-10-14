"""Check the eight-model comparison against frozen source summaries. No model calls."""
from pathlib import Path
import hashlib
import json
ROOT=Path(__file__).resolve().parent
def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def need(ok,message):
    if not ok: raise ValueError(message)
def verify():
    combined=read('results/all-models-summary-20261014.json')
    for source in combined['sourceSummaries']:
        need(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()==source['sha256'],'Source hash')
    expected={}
    for m in read('results/seven-models-low-xhigh-20261008.json')['models']:
        expected[m['model']]={e:m[e]['passed'] for e in ('low','xhigh')}
    for g in read('results/max-614-20261009.json')['groups']:
        expected[g['model']]['max']=g['passed']
    grok=read('results/grok-4.7-high-stopped-20261014.json')
    expected[grok['model']]={'high':grok['passed']}
    need(len(combined['models'])==combined['modelsCount']==8 and {m['model'] for m in combined['models']}==set(expected),'Model set')
    groups=0
    for m in combined['models']:
        need(set(m['groups'])==set(expected[m['model']]),'Effort set')
        for effort,g in m['groups'].items():
            need(g['effort']==effort and g['passed']==expected[m['model']][effort],'Pass count')
            need(g['denominator']==614 and round(100*g['passed']/614,2)==g['score'],'Score')
            if m['model']==grok['model']:
                need(g['missingFinalAnswersCountedZero']==3 and g['score']==grok['full614Score']==87.95,'Grok failure handling')
            groups+=1
        best=max(m['groups'].values(),key=lambda g:g['passed'])
        need(m['best']==best,'Best measured effort')
    need(groups==combined['combinations']==18 and combined['scoredAttempts']==18*614==11052,'Totals')
    need(combined['models']==sorted(combined['models'],key=lambda m:-m['best']['passed']),'Order')
    return {'ok':True,'models':8,'combinations':18,'denominator':614,'grokScore':87.95,'modelCalls':0}
if __name__=='__main__': print(json.dumps(verify(),ensure_ascii=False,indent=2))
