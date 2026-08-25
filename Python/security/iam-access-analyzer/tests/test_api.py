from fastapi.testclient import TestClient

from iam_analyzer.api import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_analyze_access_allows_alice():
    response = client.post(
        "/analyze-access",
        json={
            "principal": {
                "id": "user:alice@example.com",
                "type": "user",
            },
            "resource": {
                "id": "bucket:prod-data",
                "type": "storage_bucket",
            },
            "action": {
                "name": "storage.objects.get",
            },
            "context": {},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "effect": "allow",
        "reason": "Matching allow policy found",
        "risk_score": 10,
    }

def test_analyze_access_denies_bob():
    response = client.post(
        "/analyze-access",
        json={
            "principal": {
                "id": "user:bob@example.com",
                "type": "user",
            },
            "resource": {
                "id": "bucket:prod-data",
                "type": "storage_bucket",
            },
            "action": {
                "name": "storage.objects.get",
            },
            "context": {},
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "effect": "deny",
        "reason": "No matching policy found",
        "risk_score": 10,
    }

def test_analyze_access_rejects_missing_principal():
    response = client.post(
        "/analyze-access",
        json={
            "resource": {
                "id": "bucket:prod-data",
                "type": "storage_bucket",
            },
            "action": {
                "name": "storage.objects.get",
            },
            "context": {},
        },
    )

    assert response.status_code == 422

def test_analyze_access_returns_risk_score():
    payload = {
        "principal": {
            "id": "user:alice@example.com",
            "type": "user",
        },
        "resource": {
            "id": "bucket:prod-data",
            "type": "storage_bucket",
        },
        "action": {
            "name": "storage.objects.delete",
        },
        "context": {},
    }

    response = client.post(
        "/analyze-access",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["effect"] == "allow"
    assert data["risk_score"] == 70