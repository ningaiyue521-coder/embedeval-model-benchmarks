"""Audit published first answers. Optional regrade never invokes a model."""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOKEN_KEYS = ("input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens")

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def digest(value):
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def verify(regrade=False):
    manifest = read("data/catalog.json")
    cases = {c["key"]: c for c in manifest["cases"]}
    require(len(cases) == 614, "Expected 614 unique questions")
    for item in cases.values():
        require(digest(item["prompt"]) == item["promptHash"], f'Prompt hash: {item["key"]}')
    protocols = {p["round"]: p for p in read("data/protocols.json")}
    audit = read("results/export-audit.json")
    groups, seen, counts = defaultdict(list), set(), {}
    if regrade:
        import bench
        verified_rules = {}
    for source in audit["rounds"]:
        path = ROOT / source["answerFile"]
        require(path.resolve().is_relative_to((ROOT/"answers").resolve()), "Invalid answer path")
        require(digest(path.read_bytes()) == source["answerFileSha256"], f"File hash: {path.name}")
        count = 0
        warnings = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            key = tuple(row[k] for k in ("round", "model", "effort", "caseKey"))
            require(key not in seen, f"Duplicate first answer: {key}")
            seen.add(key)
            item = cases[row["caseKey"]]
            protocol = protocols[row["round"]]
            require(row["round"] == source["round"], f"Wrong round: {key}")
            require({"model":row["model"], "effort":row["effort"]} in protocol["matrix"], f"Wrong model/effort: {key}")
            require(protocol["questionKeys"][row["ordinal"]-1] == row["caseKey"], f"Question order: {key}")
            require(row["attempt"] == 1, f"Not a first attempt: {key}")
            require(digest(row["firstAnswer"]) == row["answerHash"], f"Answer hash: {key}")
            require(row["caseId"] == item["id"], f"Case ID: {key}")
            for field in ("promptHash", "rulesHash"):
                require(row[field] == item[field], f"{field}: {key}")
            require(row["revision"] == manifest["revision"] == protocol["sourceRevision"], f"Revision: {key}")
            require(row["checks"] and all(type(c["passed"]) is bool for c in row["checks"]), f"Invalid checks: {key}")
            require(all(c["passed"] for c in row["checks"]) == row["passed"], f"Pass mismatch: {key}")
            require(type(row["passed"]) is bool, f"Invalid pass flag: {key}")
            require(set(c["layer"] for c in row["checks"]).issubset({0,3}), f"Unexpected check layer: {key}")
            if row["passed"]:
                require(set(c["layer"] for c in row["checks"]) == {0,3}, f"Missing pass layer: {key}")
            for token in TOKEN_KEYS:
                require(type(row["tokens"][token]) is int and row["tokens"][token] >= 0, f"Token count: {key}")
            require(row["tokens"]["cached_input_tokens"] <= row["tokens"]["input_tokens"], f"Cached tokens: {key}")
            require(row["tokens"]["reasoning_output_tokens"] <= row["tokens"]["output_tokens"], f"Reasoning tokens: {key}")
            if regrade:
                case_dir = bench.UPSTREAM / item["caseDir"]
                if item["caseDir"] not in verified_rules:
                    verified_rules[item["caseDir"]] = bench.rule_hash(case_dir)
                require(verified_rules[item["caseDir"]] == item["rulesHash"], f"Changed upstream rules: {key}")
                result = bench.run_checks(case_dir, bench.extract_code(row["firstAnswer"]))
                actual = [{"layer":layer["layer"], "name":c["check_name"], "passed":c["passed"],
                           "expected":c["expected"], "actual":c["actual"]}
                          for layer in result["layers"] for c in layer["details"]]
                require(result["passed"] == row["passed"] and actual == row["checks"], f"Regrade differs: {key}")
            groups[key[:3]].append(row)
            count += 1
            warnings += row["transportWarning"]
        require(count == source["answers"], f"Answer count: {source['round']}")
        require(warnings == source["transportWarningCases"], f"Warning count: {source['round']}")
        counts[source["round"]] = count
    require(len(seen) == audit["totalAnswers"] == 3750, "Expected 3750 unique first answers")
    result_rows = []
    for name in ("low-614", "starter-10", "paused-xhigh"):
        result_rows.extend(read(f"results/{name}.json")["rows"])
    require(len(result_rows) == len(groups) == 45, "Expected 45 published model/effort/round groups")
    summary_keys = set()
    for row in result_rows:
        key = tuple(row[k] for k in ("round", "model", "effort"))
        require(key not in summary_keys, f"Duplicate result row: {key}")
        summary_keys.add(key)
        values = groups[key]
        total = protocols[row["round"]]["caseCount"]
        passed = sum(v["passed"] for v in values)
        complete = len(values) == total
        require(row["graded"] == len(values) and row["total"] == total and row["passed"] == passed, f"Counts: {key}")
        require(row["complete"] == complete, f"Completeness: {key}")
        require(row["score"] == (round(100*passed/total,2) if complete else None), f"Score: {key}")
        require(row["tokens"] == {k:sum(v["tokens"][k] for v in values) for k in TOKEN_KEYS}, f"Token sum: {key}")
        require(row["transportWarningCases"] == sum(v["transportWarning"] for v in values), f"Warnings: {key}")
    paused = read("results/paused-xhigh.json")
    require(paused["automaticResume"] is False and paused["status"] == "paused_by_user", "Paused status changed")
    print(json.dumps({"ok":True, "questions":614, "firstAnswers":len(seen), "groups":len(groups),
                      "rounds":counts, "regraded":len(seen) if regrade else 0, "modelCalls":0}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regrade", action="store_true", help="Re-run pinned local checkers on saved answers")
    verify(parser.parse_args().regrade)
