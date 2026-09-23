from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_assets.db"

from fastapi.testclient import TestClient

from app.main import app
from app.models import Asset, AssetVersion

client = TestClient(app)


def test_app_boots_and_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_asset_returns_presigned_upload_url():
    payload = {
        "filename": "photo.jpg",
        "content_type": "image/jpeg",
        "metadata": {"owner": "demo@example.com", "category": "marketing"},
    }

    response = client.post("/assets", json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["status"] == "uploading"
    assert data["asset_id"]
    assert "upload_url" in data
    assert "https://" in data["upload_url"]


def test_list_and_get_asset():
    create_response = client.post(
        "/assets",
        json={
            "filename": "banner.png",
            "content_type": "image/png",
            "metadata": {"owner": "demo@example.com"},
        },
    )
    asset_id = create_response.json()["asset_id"]

    list_response = client.get("/assets")
    assert list_response.status_code == 200
    assets = list_response.json()
    assert any(item["asset_id"] == asset_id for item in assets)

    detail_response = client.get(f"/assets/{asset_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["asset_id"] == asset_id
    assert detail["filename"] == "banner.png"


def test_update_asset_creates_new_version():
    create_response = client.post(
        "/assets",
        json={
            "filename": "report.pdf",
            "content_type": "application/pdf",
            "metadata": {"owner": "ops@example.com"},
        },
    )
    asset_id = create_response.json()["asset_id"]

    update_response = client.patch(
        f"/assets/{asset_id}",
        json={
            "metadata": {"owner": "ops", "category": "finance"},
            "status": "uploaded",
        },
    )

    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["version"] == 2
    assert updated["metadata"]["category"] == "finance"
    assert updated["status"] == "uploaded"

    history_response = client.get(f"/assets/{asset_id}/versions")
    assert history_response.status_code == 200
    versions = history_response.json()
    assert len(versions) >= 2
    assert versions[0]["version"] == 1


def test_version_is_generated_from_history_not_stored_twice():
    assert "version" not in Asset.__table__.columns
    assert "version" in AssetVersion.__table__.columns


def test_delete_asset_removes_record():
    create_response = client.post(
        "/assets",
        json={
            "filename": "delete-me.txt",
            "content_type": "text/plain",
            "metadata": {"owner": "qa@example.com"},
        },
    )
    asset_id = create_response.json()["asset_id"]

    delete_response = client.delete(f"/assets/{asset_id}")
    assert delete_response.status_code == 200, delete_response.text

    get_response = client.get(f"/assets/{asset_id}")
    assert get_response.status_code == 404


def test_invalid_asset_payload_is_rejected():
    response = client.post(
        "/assets",
        json={
            "content_type": "image/jpeg",
            "metadata": {"owner": "demo"},
        },
    )

    assert response.status_code == 422
