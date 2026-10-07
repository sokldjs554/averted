from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from averted.api import main as api
from averted.api.store import Store


@pytest.fixture(scope="session")
def client(toy_artifacts):
    api.store = Store(toy_artifacts)
    return TestClient(api.app)


def test_health_and_version(client):
    assert client.get("/health").json() == {"ok": True}
    v = client.get("/version").json()
    assert v["scenarios"] == ["toy"]


def test_scenario_endpoints(client):
    s = client.get("/v1/scenarios").json()["scenarios"]
    assert s[0]["id"] == "toy" and s[0]["verdict"]["level"] in {"green", "yellow", "red"}
    d = client.get("/v1/scenarios/toy").json()
    assert {"audit", "policy", "cate", "profile", "plans"} <= set(d)
    assert client.get("/v1/scenarios/nope").status_code == 404
    p = client.get("/v1/scenarios/toy/policy?k=4").json()
    assert "responsiveness" in p["values"]
    assert client.get("/v1/scenarios/toy/policy?k=5").status_code == 400


def test_plan_endpoint_slices_to_k(client):
    d = client.get("/v1/scenarios/toy").json()
    first = d["plans"][0]
    r = client.get(
        "/v1/scenarios/toy/plan", params={"site": first["site"], "week": first["week"], "k": 3}
    ).json()
    assert len(r["by_effect"]) <= 3 and len(r["by_risk"]) <= 3
    assert client.get("/v1/scenarios/toy/plan", params={"site": 99, "week": 1}).status_code == 404


def test_pilot_plan(client):
    r = client.post(
        "/v1/pilot/plan", json={"base_rate": 0.14, "averted_pp": 3.0, "n_assets": 400, "weeks": 26}
    ).json()
    assert 0 < r["plan"]["power"] < 1
    assert client.post("/v1/pilot/plan", json={"base_rate": 2.0}).status_code == 422


def test_audit_upload_and_errors(client):
    csv = client.get("/v1/sample.csv", params={"rows": 6000}).content
    r = client.post(
        "/v1/audit",
        files={"file": ("log.csv", io.BytesIO(csv), "text/csv")},
        params={"folds": 2, "sensitivity": "false"},
    )
    assert r.status_code == 200
    rep = r.json()
    assert rep["verdict"]["level"] in {"green", "yellow", "red"} and "aipw" in rep["estimates"]
    bad = client.post("/v1/audit", files={"file": ("x.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")})
    assert bad.status_code == 422 and "필요한 열" in bad.json()["detail"]
    garbage = client.post("/v1/audit", files={"file": ("x.csv", io.BytesIO(b"\x00\x01"), "text/csv")})
    assert garbage.status_code in (400, 422)


def test_schema_and_metrics(client):
    assert any(c["column"] == "treated" for c in client.get("/v1/schema").json()["columns"])
    assert "averted_requests" in client.get("/metrics").text
