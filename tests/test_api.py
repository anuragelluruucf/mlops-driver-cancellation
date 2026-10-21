import pytest
from fastapi.testclient import TestClient

from app.main import app

ORDER = {"lifetime_order_count": 40, "bike_issue_rate": 0.6, "post_pickup_rate": 0.8,
         "total_distance": 9.5, "first_mile_distance": 2.5, "last_mile_distance": 7.0,
         "session_time": 300, "hour": 19, "time_to_accept": 1.0, "time_to_pickup": 10}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:   # requires a trained champion in ./registry (make train gate)
        yield c


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_predict(client):
    r = client.post("/predict", json=ORDER).json()
    assert 0 <= r["risk_score"] <= 1 and r["risk_tier"] in {"low", "medium", "high"}


def test_explain(client):
    r = client.post("/explain?top_k=3", json=ORDER).json()
    assert len(r["top_features"]) == 3


def test_validation(client):
    assert client.post("/predict", json={**ORDER, "bike_issue_rate": 2}).status_code == 422


def test_drift_requires_batch(client):
    assert client.post("/drift", json=[ORDER]).status_code == 422
    assert "drift_detected" in client.post("/drift", json=[ORDER] * 60).json()
