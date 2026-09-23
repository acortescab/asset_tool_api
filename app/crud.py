from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Asset, AssetUploadSession, AssetVersion


def get_asset_or_404(db: Session, asset_id: str) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.deleted.is_(False)).first()
    if asset is None:
        raise ValueError("Asset not found")
    return asset


def list_assets(db: Session):
    return db.query(Asset).filter(Asset.deleted.is_(False)).order_by(Asset.created_at.desc()).all()


def get_next_asset_version(db: Session, asset_id: str) -> int:
    last_version = db.query(func.max(AssetVersion.version)).filter(AssetVersion.asset_id == asset_id).scalar()
    return (last_version or 0) + 1


def create_asset(db: Session, *, filename: str, content_type: str, metadata: dict) -> Asset:
    asset_id = uuid4().hex
    now = datetime.utcnow()

    asset = Asset(
        id=asset_id,
        filename=filename,
        content_type=content_type,
        owner=metadata.get("owner") if isinstance(metadata, dict) else None,
        asset_metadata=metadata or {},
        status="uploading",
        created_at=now,
        updated_at=now,
    )
    db.add(asset)
    db.flush()

    version_record = AssetVersion(
        asset_id=asset.id,
        version=1,
        filename=asset.filename,
        content_type=asset.content_type,
        asset_metadata=asset.asset_metadata,
        status=asset.status,
        created_at=now,
    )
    db.add(version_record)
    db.commit()
    db.refresh(asset)
    return asset


def create_upload_session(
    db: Session, asset_id: str, upload_id: str, idempotency_key: str | None = None
) -> AssetUploadSession:
    """Create an AssetUploadSession record using an `upload_id` provided by the S3 service."""
    session = AssetUploadSession(
        asset_id=asset_id,
        upload_id=upload_id,
        parts=[],
        status="in_progress",
        # idempotency_key column may not exist; store if present on model
    )
    # attach idempotency_key if model has attribute
    if idempotency_key is not None and hasattr(session, "idempotency_key"):
        setattr(session, "idempotency_key", idempotency_key)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_versions_for_asset(db: Session, asset_id: str):
    return db.query(AssetVersion).filter(AssetVersion.asset_id == asset_id).order_by(AssetVersion.version.asc()).all()


def get_upload_session(db: Session, upload_id: str) -> AssetUploadSession | None:
    return (
        db.query(AssetUploadSession)
        .filter(AssetUploadSession.upload_id == upload_id)
        .first()
    )

def update_asset(
    db: Session,
    asset_id: str,
    *,
    filename: str | None,
    content_type: str | None,
    metadata: dict | None,
    status: str | None,
) -> Asset:
    asset = get_asset_or_404(db, asset_id)

    if filename is not None:
        asset.filename = filename
    if content_type is not None:
        asset.content_type = content_type
    if metadata is not None:
        asset.asset_metadata = {**(asset.asset_metadata or {}), **metadata}
    if status is not None:
        asset.status = status

    next_version = get_next_asset_version(db, asset.id)
    asset.updated_at = datetime.utcnow()

    version_record = AssetVersion(
        asset_id=asset.id,
        version=next_version,
        filename=asset.filename,
        content_type=asset.content_type,
        asset_metadata=asset.asset_metadata,
        status=asset.status,
        created_at=asset.updated_at,
    )
    db.add(version_record)
    db.commit()
    db.refresh(asset)
    return asset


def mark_asset_uploaded(db: Session, asset_id: str) -> Asset:
    return update_asset(
        db,
        asset_id,
        filename=None,
        content_type=None,
        metadata=None,
        status="uploaded",
    )


def delete_asset(db: Session, asset_id: str) -> None:
    asset = get_asset_or_404(db, asset_id)
    asset.deleted = True
    asset.updated_at = datetime.utcnow()
    db.commit()
