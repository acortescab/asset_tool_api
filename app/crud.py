from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Asset, AssetVersion


def get_asset_or_404(db: Session, asset_id: str) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.deleted.is_(False)).first()
    if asset is None:
        raise ValueError("Asset not found")
    return asset


def list_assets(db: Session):
    return db.query(Asset).filter(Asset.deleted.is_(False)).order_by(Asset.created_at.desc()).all()


def create_asset(db: Session, *, filename: str, content_type: str, metadata: dict) -> Asset:
    asset_id = uuid4().hex
    now = datetime.utcnow()

    asset = Asset(
        id=asset_id,
        filename=filename,
        content_type=content_type,
        asset_metadata=metadata or {},
        status="uploading",
        version=1,
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


def get_versions_for_asset(db: Session, asset_id: str):
    return (
        db.query(AssetVersion)
        .filter(AssetVersion.asset_id == asset_id)
        .order_by(AssetVersion.version.asc())
        .all()
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

    asset.version = (asset.version or 0) + 1
    asset.updated_at = datetime.utcnow()

    version_record = AssetVersion(
        asset_id=asset.id,
        version=asset.version,
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
