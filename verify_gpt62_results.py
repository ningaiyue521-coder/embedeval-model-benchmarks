"""Verify GPT-6.2 first answers and the updated leaderboard without calling models."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import verify_combined_summary

ROOT = Path(__file__).resolve().parent
RESULTS = "results/gpt-6.2-sol-astra-20261118.json"
LEADERBOARD = "results/all-models-summary-20261118.json"
PREVIOUS_LEADERBOARD = "results/all-models-summary-20261106.json"
MODELS = {"gpt-6.2-sol": "GPT-6.2 Sol", "gpt-6.2-astra": "GPT-6.2 Astra"}
EFFORTS = ("low", "high", "xhigh", "max")
PUBLISHED_EFFORTS = {
    "gpt-6.2-sol": EFFORTS,
    "gpt-6.2-astra": ("low", "xhigh"),
}
FIELDS = set(
    "round sourceRun model effort ordinal caseKey caseId attempt firstAnswer answerHash "
    "promptHash rulesHash revision status passed checks started finished secondsIncludingGrading "
    "tokens transportWarning intermediateMessages".split()
)


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def digest(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def verify_group(group, cases, revision, regrade=False):
    path = group["answerFile"]
    label = f'{group["model"]}/{group["effort"]}'
    need(path == f'answers/20261118-{group["model"]}-{group["effort"]}.jsonl', f"Archive path {label}")
    archive = (ROOT / path).read_bytes()
    need(digest(archive) == group["answerFileSha256"], f"Archive hash {label}")
    rows = [json.loads(line) for line in archive.decode("utf-8").split("\n") if line]
    need(len(rows) == group["count"] == len(cases), f"Archive count {label}")

    if regrade:
        import bench

    totals = Counter()
    sdk_passed = Counter()
    format_errors = 0
    for ordinal, (row, case) in enumerate(zip(rows, cases), 1):
        tag = f"{label}/{ordinal}"
        need(set(row) == FIELDS, f"Unexpected archive fields {tag}")
        need((row["model"], row["effort"], row["sourceRun"], row["round"], row["attempt"])
             == (group["model"], group["effort"], group["sourceRun"], group["sourceRun"], 1),
             f"First answer provenance {tag}")
        need((row["ordinal"], row["caseKey"], row["caseId"])
             == (ordinal, case["key"], case["id"]), f"Question order {tag}")
        need((row["promptHash"], row["rulesHash"], row["revision"])
             == (case["promptHash"], case["rulesHash"], revision), f"Frozen question and rules {tag}")
        need(row["firstAnswer"].strip() and digest(row["firstAnswer"]) == row["answerHash"],
             f"First answer hash {tag}")
        checks = row["checks"]
        need(type(row["passed"]) is bool and type(row["transportWarning"]) is bool
             and type(row["intermediateMessages"]) is int and row["intermediateMessages"] >= 0,
             f"Grade fields {tag}")
        if row["status"] == "graded":
            need(checks and {c["layer"] for c in checks} in ({0}, {0, 3})
                 and all(type(c["passed"]) is bool for c in checks)
                 and row["passed"] == ({c["layer"] for c in checks} == {0, 3} and all(c["passed"] for c in checks)),
                 f"Rule outcomes {tag}")
            if regrade:
                case_dir = bench.UPSTREAM / case["caseDir"]
                need(bench.rule_hash(case_dir) == case["rulesHash"], f"Checker hash {tag}")
                grade = bench.run_checks(case_dir, bench.extract_code(row["firstAnswer"]))
                repeated = [
                    {"layer": layer["layer"], "name": c["check_name"], "passed": c["passed"],
                     "expected": c["expected"], "actual": c["actual"]}
                    for layer in grade["layers"] for c in layer["details"]
                ]
                need(grade["passed"] == row["passed"] and repeated == checks, f"Frozen regrade {tag}")
        else:
            need(row["status"] == "answer_format_error" and not checks and not row["passed"],
                 f"Answer format outcome {tag}")
            format_errors += 1
            if regrade:
                try:
                    bench.extract_code(row["firstAnswer"])
                except ValueError:
                    pass
                else:
                    raise ValueError(f"Format error no longer reproduces {tag}")

        need(row["tokens"].keys() == group["tokens"].keys(), f"Token fields {tag}")
        totals.update(row["tokens"])
        sdk_passed[case["sdk"]] += row["passed"]

    passed = sum(sdk_passed.values())
    need(passed == group["passed"] and round(100 * passed / len(cases), 2) == group["score"], f"Score {label}")
    need(format_errors == group["formatErrorsCountedZero"], f"Format error total {label}")
    need(dict(totals) == group["tokens"], f"Token totals {label}")
    need(sum(row["transportWarning"] for row in rows) == group["transportWarningCases"], f"Warning total {label}")
    need(sum(row["intermediateMessages"] for row in rows) == group["intermediateMessages"], f"Message total {label}")
    sdk_totals = Counter(case["sdk"] for case in cases)
    need(group["bySdk"] == {k: {"total": n, "passed": sdk_passed[k]} for k, n in sdk_totals.items()},
         f"SDK totals {label}")


def leaderboard_models(previous_models, groups):
    models = list(previous_models)
    for model, name in MODELS.items():
        scores = {
            g["effort"]: {"effort": g["effort"], "passed": g["passed"], "score": g["score"], "denominator": g["count"]}
            for g in groups if g["model"] == model
        }
        models.append({"model": model, "displayName": name, "groups": scores,
                       "best": max(scores.values(), key=lambda score: score["passed"])})
    return sorted(models, key=lambda model: -model["best"]["passed"])


def verify(regrade=False):
    catalog = read("data/catalog.json")
    new = read(RESULTS)
    cases = catalog["cases"]
    need(len(cases) == new["questionsPerCombination"] == 614 and catalog["revision"] == new["sourceRevision"],
         "Frozen dataset")
    need(digest((ROOT / "data/catalog.json").read_bytes()) == new["catalogSha256"], "Frozen catalog hash")
    expected = [(model, effort) for model, efforts in PUBLISHED_EFFORTS.items() for effort in efforts]
    groups = new["groups"]
    need([(g["model"], g["effort"]) for g in groups] == expected, "GPT-6.2 effort matrix")
    count = len(groups) * len(cases)
    need(new["verifiedFirstAnswers"] == new["uniqueSessions"] == count and new["modelCallsDuringAudit"] == 0
         and new["regradedWithFrozenL0L3"] and new["toolsUsed"] == 0, "Local audit totals")
    instructions = new["protocol"]["candidateInstructions"]
    need(digest(instructions) == new["protocol"]["candidateInstructionsSha256"], "Candidate instruction hash")
    need(new["protocol"]["firstFinalAnswersPerQuestion"] == 1 and new["protocol"]["gradingLayers"] == [0, 3]
         and all(new["protocol"][field] is False for field in
                 ("toolsAllowed", "feedbackToCandidate", "compiled", "simulated", "hardwareVerified")),
         "Test protocol")
    for group in groups:
        need(group["sourceRun"] == new["effortSourceRuns"][group["effort"]], "Run identity")
        verify_group(group, cases, catalog["revision"], regrade)

    verify_combined_summary.verify()
    previous = read(PREVIOUS_LEADERBOARD)
    combined = read(LEADERBOARD)
    need(combined["sourceSummaries"] == [
        *previous["sourceSummaries"], {"path": RESULTS, "sha256": digest((ROOT / RESULTS).read_bytes())}
    ], "Leaderboard source files")
    need(combined["models"] == leaderboard_models(previous["models"], groups), "Leaderboard scores or order")
    need(combined["modelsCount"] == len(combined["models"]) == 11
         and combined["combinations"] == previous["combinations"] + len(groups) == 37
         and combined["denominatorPerCombination"] == len(cases)
         and combined["scoredAttempts"] == combined["combinations"] * len(cases), "Leaderboard totals")
    return {"ok": True, "models": combined["modelsCount"], "combinations": combined["combinations"],
            "scoredAttempts": combined["scoredAttempts"], "gpt62FirstAnswers": count,
            "regraded": regrade, "modelCalls": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regrade", action="store_true")
    print(json.dumps(verify(parser.parse_args().regrade), indent=2))
