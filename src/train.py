"""Train a Random Forest candidate (same hyper-params as the research repo) and register it."""
import argparse
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from src import registry
from src.features import FEATURES, LABEL, add_derived

PROFILES = {
    # research-repo settings
    "research": dict(n_estimators=100, max_depth=8, min_samples_split=50, min_samples_leaf=20),
    # deliberately weak baseline, used to demo the promotion gate
    "baseline": dict(n_estimators=10, max_depth=2, min_samples_split=50, min_samples_leaf=20),
}


def main(data, profile, seed):
    df = pd.read_csv(data).sort_values("order_seq")
    X, y = add_derived(df), df[LABEL].astype(int)
    split = int(len(df) * 0.7)                       # temporal split, as in the research code
    Xtr, Xte, ytr, yte = X[:split], X[split:], y[:split], y[split:]
    t0 = time.time()
    model = RandomForestClassifier(**PROFILES[profile], class_weight="balanced",
                                   random_state=seed, n_jobs=-1).fit(Xtr, ytr)
    p = model.predict_proba(Xte)[:, 1]
    metrics = {"pr_auc": round(float(average_precision_score(yte, p)), 4),
               "roc_auc": round(float(roc_auc_score(yte, p)), 4),
               "test_positive_rate": round(float(yte.mean()), 4),
               "n_train": int(len(Xtr)), "n_test": int(len(Xte)),
               "train_seconds": round(time.time() - t0, 2),
               "profile": profile, "data": data, "synthetic_data": "synthetic" in data}
    version = registry.next_version()
    out = registry.models_dir() / version
    out.mkdir()
    joblib.dump(model, out / "model.joblib")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    # reference distribution (training deciles) for drift checks
    ref = {}
    for c in FEATURES:
        edges = np.unique(np.quantile(Xtr[c], np.linspace(0, 1, 11)))[1:-1]
        counts = np.bincount(np.searchsorted(edges, Xtr[c].values, side="right"), minlength=len(edges) + 1)
        ref[c] = {"edges": edges.tolist(), "expected": (counts / counts.sum()).tolist()}
    (out / "reference.json").write_text(json.dumps(ref))
    print(json.dumps({"candidate": version, **metrics}))
    return version


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/synthetic_orders.csv")
    ap.add_argument("--profile", default="research", choices=PROFILES)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    main(a.data, a.profile, a.seed)
