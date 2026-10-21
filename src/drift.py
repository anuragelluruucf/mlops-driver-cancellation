"""Input drift check: Population Stability Index (PSI) per feature vs training deciles."""
import argparse
import json

import numpy as np
import pandas as pd

from src.features import add_derived

THRESHOLDS = {"none": 0.1, "moderate": 0.25}   # common PSI rule of thumb


def psi(ref, values):
    """ref = {"edges": inner bin edges, "expected": training bin fractions}."""
    edges, exp = np.asarray(ref["edges"], float), np.asarray(ref["expected"], float)
    values = np.asarray(values, float)
    act = np.bincount(np.searchsorted(edges, values, side="right"), minlength=len(exp)) / max(len(values), 1)
    exp, act = np.clip(exp, 1e-4, None), np.clip(act, 1e-4, None)
    return float(np.sum((act - exp) * np.log(act / exp)))


def report(reference, X):
    out = {}
    for c, ref in reference.items():
        v = psi(ref, X[c].values)
        out[c] = {"psi": round(v, 4),
                  "status": "ok" if v < THRESHOLDS["none"] else "moderate" if v < THRESHOLDS["moderate"] else "drift"}
    return {"features": out, "drift_detected": any(f["status"] == "drift" for f in out.values())}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reference", required=True)
    ap.add_argument("--data", required=True)
    a = ap.parse_args()
    ref = json.load(open(a.reference))
    print(json.dumps(report(ref, add_derived(pd.read_csv(a.data))), indent=2))
