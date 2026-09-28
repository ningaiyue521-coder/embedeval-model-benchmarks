"""Portable fresh-round runner. prepare/status/doctor never invoke a model."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing, contextmanager
from datetime import datetime
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading

import bench
import runner_core as core

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / '.runs'
REPORT_LOCK = threading.RLock()
EFFORTS = ('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')


def location(run_id):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,79}', run_id):
        raise ValueError('Run ID must use lowercase letters, digits and hyphens, at most 80 characters')
    return RUNS / run_id


@contextmanager
def controller_lock(folder):
    """OS lock: a crash releases the controller but never releases attempts."""
    with (folder / 'runner.lock').open('a+b') as lock:
        if lock.tell() == 0:
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        if os.name == 'nt':
            import msvcrt
            try:
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError('This round already has an active controller') from exc
        else:
            import fcntl
            try:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError('This round already has an active controller') from exc
        try:
            yield
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def prepare(run_id, models, efforts, starter=False, allow_ultra=False):
    """New directory only. Published historical answers are never imported."""
    if not models or not efforts:
        raise ValueError('Explicit models and efforts are required')
    if any(not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}', m) for m in models):
        raise ValueError('Invalid model identifier')
    if any(e not in EFFORTS for e in efforts):
        raise ValueError('Invalid reasoning effort')
    if 'ultra' in efforts and not allow_ultra:
        raise ValueError('Ultra needs explicit user permission for native collaboration and --allow-ultra')
    folder = location(run_id)
    folder.parent.mkdir(parents=True, exist_ok=True)
    # Never reset an existing round or silently turn it into a new experiment.
    folder.mkdir()
    manifest = bench.catalog()
    cases = [c for c in manifest['cases'] if not starter or c['starter']]
    matrix = [{'model':m, 'effort':e} for m,e in itertools.product(dict.fromkeys(models),dict.fromkeys(efforts))]
    core.dump(folder/'manifest.json', manifest)
    for name, instructions in [('candidate-instructions.txt',core.INSTRUCTIONS),
                               ('candidate-instructions-ultra.txt',core.ULTRA_INSTRUCTIONS)]:
        (folder/name).write_text(instructions,encoding='utf-8',newline='\n')
    protocol = {'run':run_id,'created':core.timestamp(),'matrix':matrix,'caseCount':len(cases),
                'questionKeys':[c['key'] for c in cases], 'revision':manifest['revision'],
                'catalogTextHash':bench.digest(bench.MANIFEST.read_text(encoding='utf-8')),
                'ordinaryInstructionsHash':bench.digest(core.INSTRUCTIONS),
                'ultraInstructionsHash':bench.digest(core.ULTRA_INSTRUCTIONS),
                'attemptsPerModelEffortCase':1, 'historicalAnswersImported':False,
                'ultraCollaborationAuthorized':allow_ultra, 'scope':bench.SCOPE,
                'transport':'one fresh codex exec --ephemeral per question'}
    core.dump(folder/'protocol.json',protocol)
    with closing(core.connect(folder/'attempts.sqlite3')) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('''CREATE TABLE attempts (
            model TEXT, effort TEXT, case_key TEXT, ordinal INTEGER,
            status TEXT, started TEXT, finished TEXT, seconds REAL,
            points INTEGER, detail TEXT, PRIMARY KEY(model,effort,case_key))''')
        db.commit()
    bench.Store(folder/'answers.sqlite3',manifest)
    return folder


def load(folder):
    protocol = json.loads((folder/'protocol.json').read_text(encoding='utf-8'))
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if bench.digest(bench.MANIFEST.read_text(encoding='utf-8')) != protocol['catalogTextHash']:
        raise RuntimeError('Published catalog differs from the round snapshot')
    if manifest != bench.catalog() or manifest['revision'] != protocol['revision']:
        raise RuntimeError('Round manifest changed')
    for name,key in [('candidate-instructions.txt','ordinaryInstructionsHash'),
                     ('candidate-instructions-ultra.txt','ultraInstructionsHash')]:
        if bench.digest((folder/name).read_text(encoding='utf-8')) != protocol[key]:
            raise RuntimeError('Candidate instructions changed')
    by_key = {c['key']:c for c in manifest['cases']}
    if len(set(protocol['questionKeys'])) != protocol['caseCount']:
        raise RuntimeError('Question list changed')
    cases = [{**by_key[key], 'starterNumber':i} for i,key in enumerate(protocol['questionKeys'],1)]
    return protocol,cases,manifest


def report(folder):
    with REPORT_LOCK:
        protocol,cases,_ = load(folder)
        with closing(core.connect(folder/'attempts.sqlite3')) as db:
            attempts = [dict(r) for r in db.execute('SELECT * FROM attempts ORDER BY started,ordinal')]
        rows = []
        for combo in protocol['matrix']:
            mine = [a for a in attempts if a['model']==combo['model'] and a['effort']==combo['effort']]
            graded = [a for a in mine if a['status']=='graded']
            passed = sum(a['points']==10 for a in graded)
            complete = len(graded)==len(cases)
            token_keys = ('input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens')
            usage = {k:sum((json.loads(a['detail'] or '{}').get('usage') or {}).get(k,0) or 0 for a in mine) for k in token_keys}
            rows.append({**combo,'total':len(cases),'attempted':len(mine),'graded':len(graded),'passed':passed,
                         'unattempted':len(cases)-len(mine),'errors':sum(a['status'] not in ('graded','running') for a in mine),
                         'runningOrInterrupted':sum(a['status']=='running' for a in mine), 'complete':complete,
                         'score':round(100*passed/len(cases),2) if complete else None,
                         'secondsIncludingGrading':round(sum(a['seconds'] or 0 for a in mine),2),'tokens':usage})
        paused = (folder/'STOP.json').exists()
        value = {'run':protocol['run'],'updated':core.timestamp(),'status':'paused' if paused else
                 ('completed' if all(r['complete'] for r in rows) else 'ready_or_in_progress'),
                 'scope':bench.SCOPE,'graded':sum(r['graded'] for r in rows),'rows':rows,
                 'historicalAnswersImported':False,'automaticQuestionRetries':False}
        core.dump(folder/'progress.json',value)
        lines=['# '+protocol['run'],'',bench.SCOPE,'','| Model | Effort | Graded | Passed | Score / 100 |','|---|---|---:|---:|---:|']
        for r in rows:
            lines.append(f'| {r["model"]} | {r["effort"]} | {r["graded"]}/{r["total"]} | {r["passed"]} | {r["score"] if r["complete"] else "incomplete"} |')
        (folder/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
        return value


def executable(explicit=None):
    if explicit:
        candidate = Path(explicit).expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        return str(candidate)
    found = shutil.which('codex')
    if found and Path(found).suffix.lower() not in ('.cmd','.bat','.ps1'):
        return found
    # Desktop executable discovery only; never inspect or copy credentials.
    if os.name == 'nt' and os.environ.get('LOCALAPPDATA'):
        choices = list((Path(os.environ['LOCALAPPDATA'])/'OpenAI/Codex/bin').glob('*/codex.exe'))
        if choices:
            return str(max(choices,key=lambda p:p.stat().st_mtime))
    raise RuntimeError('Find a Codex executable; pass --codex /path/to/codex (Windows: codex.exe)')


def doctor(explicit=None):
    exe = executable(explicit)
    def call(*args):
        return subprocess.run([exe,*args],capture_output=True,text=True,encoding='utf-8',errors='replace',
                              timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    help_result = call('exec','--help')
    help_text = help_result.stdout+help_result.stderr
    required = ('--ignore-user-config','--strict-config','--ephemeral','--skip-git-repo-check',
                '--sandbox','--json','--output-last-message')
    missing = [flag for flag in required if flag not in help_text]
    login = call('login','status')
    version = call('--version')
    result = {'executable':exe,'version':version.stdout.strip(),'missingRequiredFlags':missing,
              'loggedIn':login.returncode==0,'modelCalls':0,
              'modelAvailability':'Confirm requested model/effort on this account before running; no automatic substitution.'}
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    if missing or help_result.returncode:
        raise RuntimeError('This CLI lacks the isolation flags used by the experiment; update Codex, do not drop the flags')
    if login.returncode:
        raise RuntimeError('Codex CLI is not authenticated in this environment. Run codex login on this computer')
    return exe


def pause(folder,reason,purpose='user_pause'):
    core.dump(folder/'STOP.json',{'at':core.timestamp(),'purpose':purpose,'reason':reason,'automaticResume':False})


def remaining(folder,protocol,cases,max_new=0):
    with closing(core.connect(folder/'attempts.sqlite3')) as db:
        claimed = {(r['model'],r['effort'],r['case_key']) for r in db.execute('SELECT model,effort,case_key FROM attempts')}
    jobs = [(combo,case) for case in cases for combo in protocol['matrix']
            if (combo['model'],combo['effort'],case['key']) not in claimed]
    return jobs[:max_new] if max_new else jobs


def run(folder,workers=4,max_new=0,resume=False,codex=None,timeout=1800):
    if not 1 <= workers <= 64 or max_new < 0 or timeout < 1:
        raise ValueError('workers=1..64; max-new>=0; timeout>=1')
    protocol,cases,manifest = load(folder)
    with controller_lock(folder):
        stop_file = folder/'STOP.json'
        if stop_file.exists():
            saved = json.loads(stop_file.read_text(encoding='utf-8'))
            if not resume or saved.get('purpose') != 'user_pause':
                raise RuntimeError('Paused: '+saved['reason']+'. Only a user pause may use --resume-paused; errors need inspection, never retry.')
        jobs = remaining(folder,protocol,cases,max_new)
        if not jobs:
            print(json.dumps(report(folder),ensure_ascii=False,indent=2))
            return
        # Fail before reserving any question if the environment or frozen rules are invalid.
        exe = doctor(codex)
        checked = {}
        for case in cases:
            path = bench.UPSTREAM/case['caseDir']
            if path not in checked:
                checked[path]=bench.rule_hash(path)
            if checked[path]!=case['rulesHash'] or bench.digest(case['prompt'])!=case['promptHash']:
                raise RuntimeError('Frozen prompt/checker changed: '+case['id'])
        if stop_file.exists():
            stop_file.rename(folder/('pause-acknowledged-'+datetime.now().strftime('%Y%m%d%H%M%S%f')+'.json'))
        core.STOP.clear()
        core.TIMEOUT=timeout
        # Candidate working directory is outside this repository and has no answers/checkers.
        with tempfile.TemporaryDirectory(prefix='embedeval-candidate-') as empty:
            context={'directory':folder,'registry':folder/'attempts.sqlite3','scoreDatabase':folder/'answers.sqlite3',
                     'label':lambda model,effort:f'{model} / {effort} / {protocol["run"]}',
                     'report':lambda *a,**kw:report(folder),'stopFile':stop_file,'emptyWorkspace':Path(empty)}
            core.dump(folder/'execution.json',{'workers':workers,'started':core.timestamp(),'plannedNewAttempts':len(jobs),
                      'cliExecutable':exe,'freshSessionPerQuestion':True,'timeoutSeconds':timeout})
            queue=iter(jobs)
            queue_lock=threading.Lock()
            def worker():
                while not core.STOP.is_set() and not stop_file.exists():
                    with queue_lock:
                        job=next(queue,None)
                    if job is None:
                        return
                    combo,case=job
                    try:
                        core.run_one(combo,case,protocol['matrix'],cases,manifest,exe,context=context)
                        with closing(core.connect(folder/'attempts.sqlite3')) as db:
                            a=db.execute('SELECT status FROM attempts WHERE model=? AND effort=? AND case_key=?',
                                         (combo['model'],combo['effort'],case['key'])).fetchone()
                        if a and a['status']!='graded':
                            raise RuntimeError(f'{combo["model"]}/{combo["effort"]}/{case["key"]}: {a["status"]}; first attempt remains locked')
                    except Exception as exc:
                        core.STOP.set()
                        pause(folder,str(exc),'error')
                        print('STOP: '+str(exc),file=sys.stderr,flush=True)
                        return
            with ThreadPoolExecutor(max_workers=min(workers,len(jobs))) as pool:
                futures=[pool.submit(worker) for _ in range(min(workers,len(jobs)))]
                try:
                    for future in as_completed(futures):
                        future.result()
                except KeyboardInterrupt:
                    core.STOP.set()
                    pause(folder,'Keyboard interruption: stop issuing questions; let in-flight calls finish')
                    print('Pausing. Waiting for already-started answers; none will be repeated.',flush=True)
            print(json.dumps(report(folder),ensure_ascii=False,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    prep=sub.add_parser('prepare',help='Create a completely new round, zero model calls')
    prep.add_argument('--run',required=True)
    prep.add_argument('--models',nargs='+',required=True)
    prep.add_argument('--efforts',nargs='+',choices=EFFORTS,required=True)
    prep.add_argument('--starter',action='store_true')
    prep.add_argument('--allow-ultra',action='store_true')
    for command in ('status','pause'):
        sub.add_parser(command).add_argument('--run',required=True)
    sub.add_parser('doctor').add_argument('--codex')
    execute=sub.add_parser('run',help='This command consumes the logged-in account quota')
    execute.add_argument('--run',required=True)
    execute.add_argument('--workers',type=int,default=4)
    execute.add_argument('--max-new',type=int,default=0)
    execute.add_argument('--timeout',type=int,default=1800)
    execute.add_argument('--resume-paused',action='store_true')
    execute.add_argument('--codex')
    args=parser.parse_args()
    if args.command=='doctor':
        doctor(args.codex)
        return
    folder=location(args.run)
    if args.command=='prepare':
        prepare(args.run,args.models,args.efforts,args.starter,args.allow_ultra)
    elif args.command=='pause':
        load(folder)
        pause(folder,'User requested pause')
    elif args.command=='run':
        run(folder,args.workers,args.max_new,args.resume_paused,args.codex,args.timeout)
        return
    print(json.dumps(report(folder),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
