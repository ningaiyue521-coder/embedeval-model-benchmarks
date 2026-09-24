"""Offline manual-answer adapter for the pinned EmbedEval checkout.

Uses the upstream bugfix prompt and L0/L3 check functions. Never calls an LLM,
compiles, or executes submitted C code. Local first submissions are immutable.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent
UPSTREAM = Path(os.environ.get("EMBEDEVAL_ROOT", ROOT / ".upstream" / "embedeval")).resolve()
REVISION = "fdbcb9b93476149cce2d395532bf5164811fe053"
sys.path.insert(0, str(UPSTREAM / "src"))
import yaml
from embedeval.evaluator import _execute_check_module
from embedeval.models import CaseMetadata

MANIFEST = ROOT / "data" / "catalog.json"
SCOPE = "仅官方 L0 静态检查 + L3 规则检查；未编译、未仿真、未实机验证"
MODULES: dict[Path, object] = {}
STARTER_PRESET = [
    ("zephyr/isr-concurrency-008:plain_int_indices", "中断与线程共享队列"),
    ("zephyr/dma-001:start_before_config", "DMA 配置与启动顺序"),
    ("zephyr/gpio-basic-006:isr_reads_gpio_directly", "GPIO 按键消抖"),
    ("zephyr/ble-008:cross_platform_api", "BLE 混用不同 SDK 的 API"),
    ("zephyr/ota-001:confirm_without_self_test", "OTA 固件自检与确认"),
    ("zephyr/storage-001:mount_after_write", "NVS 挂载与写入顺序"),
    ("zephyr/watchdog-005:unconditional_feed", "看门狗与线程健康检查"),
    ("zephyr/networking-001:no_protocol_loop", "MQTT 协议处理循环"),
    ("zephyr/timer-001:wrong_timer_period", "周期定时器参数"),
    ("zephyr/security-001:missing_key_destroy", "PSA 密钥资源释放"),
]


def digest(value: str | bytes) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")


def module_at(path: Path):
    path = path.resolve()
    if not path.is_relative_to((UPSTREAM / "cases").resolve()):
        raise ValueError("Invalid check path")
    if path not in MODULES:
        spec = importlib.util.spec_from_file_location("manual_"+digest(str(path))[:16], path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Cannot load {path.name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        MODULES[path] = module
    return MODULES[path]


def rule_hash(case_dir: Path) -> str:
    paths = list((UPSTREAM / "src" / "embedeval").rglob("*.py"))
    paths += list((case_dir / "checks").glob("*.py"))
    paths += [case_dir / "metadata.yaml"]
    h = hashlib.sha256()
    for path in sorted(paths):
        h.update(path.relative_to(UPSTREAM).as_posix().encode())
        h.update(b"\0")
        h.update(path.read_bytes())
    return h.hexdigest()


def run_checks(case_dir: Path, code: str) -> dict:
    """Use unchanged upstream functions, failing closed on check-loader errors."""
    layers = []
    for number, filename, name in [(0, "static.py", "static_analysis"),
                                   (3, "behavior.py", "static_heuristic")]:
        path = case_dir / "checks" / filename
        if not path.is_file():
            raise RuntimeError(f"Missing official checker: {path}")
        module = module_at(path)
        result = _execute_check_module(module, code, layer=number, name=name)
        if result.error:
            raise RuntimeError(f"L{number} checker error: {result.error}")
        if not result.details:
            raise RuntimeError(f"L{number} has no checks")
        layers.append(result.model_dump())
        if not result.passed:
            break  # Preserve the official L0 -> L3 failure gate.
    passed = len(layers) == 2 and all(layer["passed"] for layer in layers)
    not_run = ["L1 编译", "L2 运行/仿真", "L4 判题器变异验证"]
    if len(layers) < 2:
        not_run.insert(2, "L3 规则检查（L0 未通过，按上游流程跳过）")
    return {"passed": passed, "layers": layers,
            "notRun": not_run,
            "scope": SCOPE}


def catalog() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def extract_code(raw: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("请粘贴首次答案或导入文件")
    if len(raw.encode("utf-8")) > 1_000_000:
        raise ValueError("答案超过 1 MB")
    fenced = re.findall(r"^\s*```[^\n]*\n([\s\S]*?)^\s*```\s*$", raw, re.M)
    if len(fenced) > 1:
        raise ValueError("检测到多个代码块：请从保存的首次答案中粘贴完整源码，不要让模型重答")
    code = fenced[0] if fenced else raw
    if not code.strip():
        raise ValueError("代码块为空，请导入首次回答中的完整源码")
    return code.lstrip("\ufeff")


def normalize_model(model: str) -> tuple[str, str]:
    label = unicodedata.normalize("NFKC", model).strip()
    if not label or len(label) > 120:
        raise ValueError("请填写模型名称与版本（1–120 字符）")
    key = " ".join(label.casefold().split())
    return label, key


class Store:
    def __init__(self, path: Path, manifest: dict):
        self.path = path
        self.manifest = manifest
        self.cases = {item["key"]: item for item in manifest["cases"]}
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS submissions (
                model_key TEXT NOT NULL, case_key TEXT NOT NULL, model TEXT NOT NULL,
                created TEXT NOT NULL, answer_hash TEXT NOT NULL, raw_answer TEXT NOT NULL,
                code TEXT NOT NULL, status TEXT NOT NULL, result TEXT,
                PRIMARY KEY(model_key, case_key))""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def submit(self, model: str, case_key: str, raw: str) -> tuple[dict, bool]:
        label, model_key = normalize_model(model)
        if case_key not in self.cases:
            raise ValueError("题目不存在")
        item = self.cases[case_key]
        code = extract_code(raw)
        case_dir = (UPSTREAM / item["caseDir"]).resolve()
        if not case_dir.is_relative_to((UPSTREAM / "cases").resolve()):
            raise RuntimeError("Invalid case directory")
        if rule_hash(case_dir) != item["rulesHash"]:
            raise RuntimeError("官方评分文件发生变化，已停止评分以保护可比性")
        answer_hash = digest(raw)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM submissions WHERE model_key=? AND case_key=?", (model_key, case_key)).fetchone()
            if old:
                if old["answer_hash"] != answer_hash:
                    raise FileExistsError("此模型的本题首次答案已锁定，不能覆盖或提交修改稿")
                if old["result"]:
                    return json.loads(old["result"]), False
                raise FileExistsError("此题首次答案已保存，评分正在处理或中断；请保留原答卷")
            # Persist the raw first answer before any grading. Failure cannot unlock it.
            db.execute("INSERT INTO submissions VALUES (?,?,?,?,?,?,?,?,?)",
                       (model_key, case_key, label, now(), answer_hash, raw, code, "pending", None))
        try:
            graded = run_checks(case_dir, code)
            status = "graded"
        except Exception as exc:
            graded = {"passed": None, "layers": [], "scope": SCOPE, "error": str(exc),
                      "notRun": ["L0/L3 判题未完成", "L1 编译", "L2 运行/仿真", "L4 判题器变异验证"]}
            status = "error"
        result = {**graded, "status": status, "model": label, "caseKey": case_key,
                  "caseId": item["id"], "title": item["title"], "answerHash": answer_hash,
                  "promptHash": item["promptHash"], "rulesHash": item["rulesHash"],
                  "revision": self.manifest["revision"], "recordedAt": now(), "attempt": 1}
        with self.connect() as db:
            db.execute("UPDATE submissions SET status=?,result=? WHERE model_key=? AND case_key=?",
                       (status, json.dumps(result, ensure_ascii=False), model_key, case_key))
        return result, True

    def results(self, model: str | None = None, include_answers: bool = False) -> list[dict]:
        with self.connect() as db:
            if model is not None:
                _, key = normalize_model(model)
                rows = db.execute("SELECT * FROM submissions WHERE model_key=? ORDER BY created", (key,)).fetchall()
            else:
                rows = db.execute("SELECT * FROM submissions ORDER BY created").fetchall()
        results = []
        for r in rows:
            result = json.loads(r["result"]) if r["result"] else {
                "model": r["model"], "caseKey": r["case_key"], "status": r["status"], "passed": None}
            if include_answers:
                result["rawAnswer"] = r["raw_answer"]
            results.append(result)
        return results

    def leaderboard(self) -> list[dict]:
        starter = {x["key"] for x in self.manifest["cases"] if x["starter"]}
        groups = {}
        for r in self.results():
            _, key = normalize_model(r["model"])
            row = groups.setdefault(key, {"model": r["model"], "submitted": 0, "graded": 0,
                                         "passed": 0, "errors": 0, "starterSubmitted": 0,
                                         "starterGraded": 0, "starterPassed": 0})
            row["submitted"] += 1
            row["graded"] += r["status"] == "graded"
            row["passed"] += r.get("passed") is True
            row["errors"] += r["status"] != "graded"
            if r["caseKey"] in starter:
                row["starterSubmitted"] += 1
                row["starterGraded"] += r["status"] == "graded"
                row["starterPassed"] += r.get("passed") is True
        for row in groups.values():
            row["starterTotal"] = len(starter)
            row["starterScore"] = row["starterPassed"] * 100 / len(starter)
            row["complete"] = row["starterGraded"] == len(starter)
        return sorted(groups.values(), key=lambda x: (not x["complete"], -x["starterScore"], x["model"]))
