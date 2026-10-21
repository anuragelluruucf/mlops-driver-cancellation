"""Promotion gate: candidate becomes champion only if PR-AUC beats the champion by >= MIN_DELTA.
PR-AUC (average precision) is used because the positive class is rare (~1%)."""
import argparse
import json
import os
import sys

from src import registry

METRIC = "pr_auc"


def evaluate(candidate, min_delta):
    cm = json.loads((registry.models_dir() / candidate / "metrics.json").read_text())
    champ = registry.champion()
    if champ is None:
        return True, cm, None, "no champion yet"
    delta = cm[METRIC] - champ["metrics"][METRIC]
    ok = delta >= min_delta
    return ok, cm, champ, f"{METRIC} {cm[METRIC]} vs champion {champ['version']} {champ['metrics'][METRIC]} (delta {delta:+.4f}, need >= {min_delta})"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", help="version, default = latest")
    ap.add_argument("--min-delta", type=float, default=0.005)
    ap.add_argument("--fail-on-reject", action="store_true")
    a = ap.parse_args()
    cand = a.candidate or max((p.name for p in registry.models_dir().glob("v*")), key=lambda v: int(v[1:]))
    ok, cm, champ, why = evaluate(cand, a.min_delta)
    if ok:
        registry.set_champion(cand, cm)
        synced = registry.sync_to_gcs(cand)
    print(json.dumps({"candidate": cand, "promoted": ok, "reason": why}))
    if gh := os.getenv("GITHUB_OUTPUT"):
        with open(gh, "a") as f:
            f.write(f"promoted={'true' if ok else 'false'}\nversion={cand}\n")
    sys.exit(1 if (a.fail_on_reject and not ok) else 0)
