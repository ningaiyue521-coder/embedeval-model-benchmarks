"""Single-attempt model matrix through the authenticated local Codex CLI.

Prompts go to fresh ephemeral sessions. No candidate receives the checker,
reference solution, prior answers, or grading feedback. The registry commits
an attempt BEFORE invocation, so restarting this script never repeats it.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid

import bench

RUN = bench.ROOT / '.runs' / 'unconfigured'
REGISTRY = RUN / 'attempts.sqlite3'
ORDER = ['gpt-5.5', 'gpt-5.6-luna', 'gpt-5.6-terra', 'gpt-5.6-sol',
         'gpt-6-luna', 'gpt-6-sol', 'gpt-6-astra']
EFFORTS = ['low', 'medium', 'high', 'xhigh', 'max', 'ultra']
LOCK = threading.RLock()
GRADE_LOCK = threading.RLock()
STOP = threading.Event()
TIMEOUT = 1800
DISABLE = ['shell_tool', 'unified_exec', 'apps', 'plugins', 'memories',
           'browser_use', 'browser_use_external', 'in_app_browser',
           'computer_use', 'code_mode', 'code_mode_host', 'image_generation',
           'hooks', 'workspace_dependencies', 'view_image', 'goals',
           'sleep_tool', 'unbounded_connection_retries', 'skill_search']
INSTRUCTIONS = '''You are completing a single-attempt code repair benchmark.
Solve only the problem provided in the user message. Output only the complete
corrected source file. Do not use the filesystem, execute code, browse, consult
external resources, or invoke tools. You do not have access to reference answers
or grader feedback. Do not request clarification or a second attempt.
'''
ULTRA_INSTRUCTIONS = '''You are completing a single-attempt code repair benchmark.
Solve only the problem provided in the user message. Output only the complete
corrected source file as one final answer. Native Ultra collaboration is permitted:
you may use the built-in subagent collaboration tools to reason about this problem.
Do not use the filesystem, execute code, browse, consult external resources, or
invoke other tools. Apply these restrictions to any subagents as well. You do not
have access to reference answers or grader feedback. Do not request clarification
or a second attempt. Do not return intermediate candidate answers to the user.
'''


def timestamp():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # Windows readers and concurrent writers can briefly deny replacement.
    # Retry only this local file operation, never a model request.
    for attempt in range(40):
        try:
            temp.replace(path)
            return
        except PermissionError:
            if attempt == 39:
                raise
            time.sleep(min(0.01 * (attempt + 1), 0.1))


def connect(registry=None):
    db = sqlite3.connect(registry or REGISTRY, timeout=60)
    db.row_factory = sqlite3.Row
    return db


def configs(effort, run_directory=None):
    ultra = effort == 'ultra'
    run_directory = run_directory or RUN
    instruction_name = 'candidate-instructions-ultra.txt' if ultra else 'candidate-instructions.txt'
    pairs = [
        'model_reasoning_effort=' + json.dumps(effort),
        'model_reasoning_summary="none"', 'approval_policy="never"',
        'web_search="disabled"', 'project_doc_max_bytes=0',
        'model_instructions_file=' + json.dumps((run_directory / instruction_name).as_posix()),
        'features.skip_host_skill_discovery=true',
        'features.multi_agent=' + ('true' if ultra else 'false'), 'features.multi_agent_v2=false',
    ]
    for feature in DISABLE:
        pairs.append('features.' + feature + '=false')
    return [part for pair in pairs for part in ['-c', pair]]


def label(model, effort):
    return f'{model} / {effort} / Codex 单次 / 2026-09-24'


def report(*args, **kwargs):
    raise RuntimeError("Use batch_runner.py with an explicit run context")


def run_one(combo, case, matrix, cases, manifest, executable, *, context=None):
    context = context or {}
    run_directory = context.get('directory', RUN)
    registry = context.get('registry', REGISTRY)
    score_database = context.get('scoreDatabase', bench.ROOT / 'answers.sqlite3')
    submission_label = context.get('label', label)
    publish_report = context.get('report', report)
    stop_file = context.get('stopFile')
    if STOP.is_set():
        return
    if stop_file and stop_file.exists():
        STOP.set()
        return
    model, effort = combo['model'], combo['effort']
    ordinal = case['starterNumber']
    directory = run_directory / 'answers' / model / effort / f'{ordinal:02d}-{case["key"]}'
    directory.mkdir(parents=True, exist_ok=True)
    db = connect(registry)
    try:
        db.execute('BEGIN IMMEDIATE')
        old = db.execute('SELECT status FROM attempts WHERE model=? AND effort=? AND case_key=?',
                         (model, effort, case['key'])).fetchone()
        if old:
            return
        db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?,?,?,?,?)',
                   (model, effort, case['key'], ordinal, 'running', timestamp(), None, None, None, None))
        db.commit()
    finally:
        db.close()
    started = time.monotonic()
    prompt_path = directory / 'prompt.md'
    prompt_path.write_text(case['prompt'], encoding='utf-8')
    output_path = directory / 'first-answer.txt'
    command = [executable, 'exec', '--ignore-user-config', '--strict-config', '--ephemeral',
               '--skip-git-repo-check', '--sandbox', 'read-only', '--color', 'never',
               '--json', '--model', model, '-C', str(context.get('emptyWorkspace', run_directory / 'empty-workspace')),
               '-o', str(output_path), *configs(effort, run_directory), '-']
    dump(directory / 'invocation.json', {'command': command, 'model': model, 'effort': effort,
                                        'promptHash': bench.digest(case['prompt']),
                                        'started': timestamp(), 'attempt': 1})
    print(f'START {model} {effort} Q{ordinal:02}', flush=True)
    try:
        publish_report(matrix, cases)
    except OSError as exc:
        print(f'WARN progress display: {type(exc).__name__}: {exc}', flush=True)
    status, points, detail = 'generation_error', None, {}
    try:
        with (directory / 'events.jsonl').open('wb') as out, (directory / 'stderr.log').open('wb') as err:
            process = subprocess.run(command, input=case['prompt'].encode('utf-8'), stdout=out, stderr=err,
                                     timeout=TIMEOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        events = []
        for line in (directory / 'events.jsonl').read_text(encoding='utf-8', errors='replace').splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
        detail['returnCode'] = process.returncode
        detail['usage'] = next((e.get('usage') for e in reversed(events) if e.get('type') == 'turn.completed'), None)
        detail['threadId'] = next((e.get('thread_id') for e in events if e.get('type') == 'thread.started'), None)
        tool_items = [e.get('item', {}) for e in events if e.get('type') in ['item.started', 'item.completed']
                      and e.get('item', {}).get('type') not in ['agent_message', 'reasoning', 'error']]
        detail['runtimeWarnings'] = [e['item'].get('message', '') for e in events
                                     if e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'error']
        detail['toolItemTypes'] = [item.get('type') for item in tool_items]
        raw = output_path.read_text(encoding='utf-8') if output_path.exists() else ''
        if process.returncode != 0 or not raw.strip() or sum(e.get('type') == 'turn.completed' for e in events) != 1 or sum(e.get('type') == 'thread.started' for e in events) != 1:
            error_events = [e for e in events if e.get('type') in ['error', 'turn.failed']]
            detail['error'] = error_events or (directory / 'stderr.log').read_text(encoding='utf-8', errors='replace')[-2500:]
            if any(term in json.dumps(detail).lower() for term in ['usage limit', 'rate limit', 'rate_limit', 'quota', '429']):
                STOP.set()
        elif any(not (effort == 'ultra' and str(item.get('type', '')).lower().startswith('collab')) for item in tool_items):
            status = 'invalid_tool_use'
            detail['error'] = 'Candidate used tools outside the selected mode policy.'
        else:
            detail['answerHash'] = bench.digest(raw)
            status = 'grading_error'
            try:
                # Model calls remain concurrent; serialize local score transactions.
                with GRADE_LOCK:
                    store = bench.Store(score_database, manifest)
                    graded, created = store.submit(submission_label(model, effort), case['key'], raw)
                dump(directory / 'grade.json', graded)
                status = graded['status']
                points = 10 if graded['passed'] else (0 if graded['passed'] is False else None)
                detail['failedChecks'] = [d['check_name'] for layer in graded.get('layers', [])
                                          for d in layer['details'] if not d['passed']]
            except ValueError as exc:
                status = 'answer_format_error'
                detail['error'] = str(exc)
    except Exception as exc:
        detail['error'] = type(exc).__name__ + ': ' + str(exc)
    seconds = round(time.monotonic() - started, 2)
    db = connect(registry)
    try:
        db.execute('UPDATE attempts SET status=?,finished=?,seconds=?,points=?,detail=? WHERE model=? AND effort=? AND case_key=?',
                   (status, timestamp(), seconds, points, json.dumps(detail, ensure_ascii=False), model, effort, case['key']))
        db.commit()
    finally:
        db.close()
    dump(directory / 'outcome.json', {'status': status, 'points': points, 'seconds': seconds, **detail})
    try:
        progress = publish_report(matrix, cases, 'stopped_on_limit' if STOP.is_set() else 'running')
    except OSError as exc:
        print(f'WARN progress display: {type(exc).__name__}: {exc}', flush=True)
        progress = {'graded': 'saved'}
    print(f'DONE {model} {effort} Q{ordinal:02} {status} points={points} time={seconds}s total={progress["graded"]}', flush=True)
