"""FastAPI service: serves the current champion model from the registry.
MODEL_GCS_URI (gs://bucket) -> downloads champion at startup; otherwise uses REGISTRY_DIR locally."""
import json
import os
import pathlib
from contextlib import asynccontextmanager

import joblib
import numpy as np
import pandas as pd
import shap
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src import drift
from src.features import FEATURES, add_derived

STATE = {}


def _download_from_gcs(uri, dest):
    from google.cloud import storage  # only needed in the cloud
    b = storage.Client().bucket(uri.removeprefix("gs://"))
    champ = json.loads(b.blob("champion.json").download_as_text())
    d = dest / "models" / champ["version"]
    d.mkdir(parents=True, exist_ok=True)
    for name in ("model.joblib", "metrics.json", "reference.json"):
        b.blob(f"models/{champ['version']}/{name}").download_to_filename(d / name)
    (dest / "champion.json").write_text(json.dumps(champ))


def load():
    root = pathlib.Path(os.getenv("REGISTRY_DIR", "registry"))
    if uri := os.getenv("MODEL_GCS_URI"):
        root = pathlib.Path("/tmp/registry")
        _download_from_gcs(uri, root)
    champ = json.loads((root / "champion.json").read_text())
    d = root / "models" / champ["version"]
    model = joblib.load(d / "model.joblib")
    STATE.update(version=champ["version"], metrics=champ["metrics"], model=model,
                 explainer=shap.TreeExplainer(model),
                 reference=json.loads((d / "reference.json").read_text()))


@asynccontextmanager
async def lifespan(_):
    load()
    yield


app = FastAPI(title="driver-cancellation-risk", lifespan=lifespan)


class Order(BaseModel):
    lifetime_order_count: float = Field(ge=0)
    bike_issue_rate: float = Field(ge=0, le=1)
    post_pickup_rate: float = Field(ge=0, le=1)
    total_distance: float = Field(ge=0)
    first_mile_distance: float = Field(ge=0)
    last_mile_distance: float = Field(ge=0)
    session_time: float = Field(ge=0)
    hour: int = Field(ge=0, le=23)
    time_to_accept: float = Field(ge=0)
    time_to_pickup: float = Field(ge=0)


def _frame(orders):
    return add_derived(pd.DataFrame([o.model_dump() for o in orders]))


def _tier(p):  # risk tiers from the research's policy simulation
    return "high" if p >= 0.7 else "medium" if p >= 0.4 else "low"


@app.get("/health")
def health():
    return {"status": "ok", "model_version": STATE.get("version"), "app_version": os.getenv("APP_VERSION", "dev")}


@app.post("/predict")
def predict(order: Order):
    p = float(STATE["model"].predict_proba(_frame([order]))[0, 1])
    return {"risk_score": round(p, 4), "risk_tier": _tier(p), "model_version": STATE["version"]}


@app.post("/explain")
def explain(order: Order, top_k: int = 5):
    X = _frame([order])
    sv = STATE["explainer"].shap_values(X)
    vals = np.asarray(sv)
    vals = vals[0, :, 1] if vals.ndim == 3 else (sv[1][0] if isinstance(sv, list) else vals[0])
    order_idx = np.argsort(-np.abs(vals))[:top_k]
    return {"model_version": STATE["version"],
            "top_features": [{"feature": FEATURES[i], "value": float(X.iloc[0, i]),
                              "shap": round(float(vals[i]), 4)} for i in order_idx]}


@app.post("/drift")
def drift_check(orders: list[Order]):
    if len(orders) < 50:
        raise HTTPException(422, "send at least 50 orders for a meaningful PSI estimate")
    return drift.report(STATE["reference"], _frame(orders))
