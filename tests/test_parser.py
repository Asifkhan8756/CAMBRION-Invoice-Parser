import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    # Test that the server is running.
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_reject_invalid_file():
    # Test that unsupported file types are rejected.
    response = client.post(
        "/parse-invoice",
        files={"file": ("test.txt", b"fake image data", "text/plain")},
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_reject_empty_file():
    # Test that empty files are rejected.
    response = client.post(
        "/parse-invoice",
        files={"file": ("test.png", b"", "image/png")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_parse_invoice():
    # Test full pipeline with a real invoice. Requires OpenAI API key.
    with open("samples/AB2.png", "rb") as f:
        response = client.post(
            "/parse-invoice",
            files={"file": ("AB2.png", f, "image/png")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["invoice_number"] not in ("", "N/A", "None")
    assert data["date"] not in ("", "N/A", "None")
    assert data["vendor_name"] not in ("", "N/A", "None")
    assert data["total_amount"] > 0
    assert data["currency"] not in ("", "N/A", "None")