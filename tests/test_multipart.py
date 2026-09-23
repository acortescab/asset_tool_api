from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_assets.db"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_initiate_multipart_session():
    payload = {
        "filename": "large.bin",
        "content_type": "application/octet-stream",
        "metadata": {"owner": "big@example.com"},
        "upload_mode": "multipart",
    }

    resp = client.post("/assets", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["upload_mode"] == "multipart"
    assert data["upload_id"] is not None

