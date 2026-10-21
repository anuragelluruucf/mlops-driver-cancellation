import json

import pandas as pd
import pytest

from src import data, gate, registry, train, drift
from src.features import add_derived


@pytest.fixture()
def reg(tmp_path, monkeypatch):
    monkeypatch.setattr(registry, "ROOT", tmp_path / "registry")
    csv = tmp_path / "synthetic.csv"
    data.generate(8000, n_riders=600, seed=1).to_csv(csv, index=False)
    return csv


def test_schema_and_label_rate():
    df = data.generate(5000, seed=3)
    assert 0 < df.is_strategic_order.mean() < 0.05
    assert list(add_derived(df).columns)[0] == "lifetime_order_count"


def test_gate_promotes_better_and_rejects_equal(reg):
    v1 = train.main(str(reg), "baseline", 42)
    assert gate.evaluate(v1, 0.005)[0] and registry.set_champion(v1, json.loads((registry.models_dir() / v1 / "metrics.json").read_text())) is None
    v2 = train.main(str(reg), "research", 42)
    ok, cm, champ, _ = gate.evaluate(v2, 0.005)
    expected = cm["pr_auc"] - champ["metrics"]["pr_auc"] >= 0.005
    assert ok == expected
    registry.set_champion(v2, cm) if ok else None
    v3 = train.main(str(reg), registry.champion()["metrics"]["profile"], 42)
    assert gate.evaluate(v3, 0.005)[0] is False   # identical retrain must not be promoted


def test_drift_detects_shift(reg):
    v = train.main(str(reg), "research", 42)
    ref = json.loads((registry.models_dir() / v / "reference.json").read_text())
    same = add_derived(data.generate(4000, seed=9))
    shifted = data.generate(4000, seed=9)
    shifted["total_distance"] *= 2
    assert drift.report(ref, same)["drift_detected"] is False
    assert drift.report(ref, add_derived(shifted))["drift_detected"] is True
