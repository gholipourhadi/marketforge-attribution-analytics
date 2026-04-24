from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_quality_and_funnel():
    assert client.get("/api/v1/quality").status_code == 200
    assert client.get("/api/v1/funnel").json()["conversions"] > 0


def test_attribution_endpoint():
    response = client.post("/api/v1/attribution", json={"model": "position_based"})
    assert response.status_code == 200
    assert sum(row["attributed_revenue_eur"] for row in response.json()) > 0


def test_invalid_attribution_model():
    assert client.post("/api/v1/attribution", json={"model": "unknown"}).status_code == 422


def test_channel_markov_and_cohort_endpoints():
    assert len(client.get("/api/v1/channels").json()) >= 5
    assert len(client.get("/api/v1/markov").json()) >= 5
    assert len(client.get("/api/v1/cohorts").json()) > 0


def test_experiment_endpoint():
    response = client.post(
        "/api/v1/experiments/evaluate",
        json={
            "control_conversions": 100,
            "control_visitors": 2000,
            "treatment_conversions": 160,
            "treatment_visitors": 2000,
        },
    )
    assert response.status_code == 200
    assert response.json()["statistically_significant"] is True


def test_small_experiment_returns_422():
    payload = {"control_conversions": 1, "control_visitors": 20, "treatment_conversions": 2, "treatment_visitors": 20}
    assert client.post("/api/v1/experiments/evaluate", json=payload).status_code == 422


def test_budget_endpoint():
    response = client.post("/api/v1/budget/scenario", json={"total_budget_eur": 50_000})
    assert response.status_code == 200
    assert response.json()["current_budget_eur"] == 50_000


def test_budget_validation():
    assert client.post("/api/v1/budget/scenario", json={"total_budget_eur": 0}).status_code == 422
