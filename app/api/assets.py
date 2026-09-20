from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import (
    create_asset,
    delete_asset,
    get_asset_or_404,
    get_versions_for_asset,
    list_assets,
    mark_asset_uploaded,
    update_asset,
)
from app.database import SessionLocal
from app.schemas import AssetCreate, AssetCreateResponse, AssetRead, AssetUpdate, AssetVersionRead
from app.services.s3_client import generate_presigned_upload_url

router = APIRouter(prefix="/assets", tags=["assets"])


def get_db():
    """Provide a database session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AssetCreateResponse)
def create_asset_route(payload: AssetCreate, db: Session = Depends(get_db)):
    """Create an asset and return a presigned upload URL for the client."""
    asset = create_asset(
        db,
        filename=payload.filename,
        content_type=payload.content_type,
        metadata=payload.metadata,
    )

    upload_url = generate_presigned_upload_url(
        object_key=f"{asset.id}/{asset.filename}",
        content_type=asset.content_type,
    )

    return {
        "asset_id": asset.id,
        "filename": asset.filename,
        "content_type": asset.content_type,
        "metadata": asset.asset_metadata,
        "status": asset.status,
        "version": asset.version,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
        "upload_url": upload_url,
    }


@router.get("", response_model=list[AssetRead])
def list_assets_route(db: Session = Depends(get_db)):
    """Return all active assets."""
    assets = list_assets(db)
    return [
        {
            "asset_id": asset.id,
            "filename": asset.filename,
            "content_type": asset.content_type,
            "metadata": asset.asset_metadata,
            "status": asset.status,
            "version": asset.version,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
        }
        for asset in assets
    ]


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset_route(asset_id: str, db: Session = Depends(get_db)):
    """Get a single asset by its identifier."""
    try:
        asset = get_asset_or_404(db, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc
    return {
        "asset_id": asset.id,
        "filename": asset.filename,
        "content_type": asset.content_type,
        "metadata": asset.asset_metadata,
        "status": asset.status,
        "version": asset.version,
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
    }


@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset_route(asset_id: str, payload: AssetUpdate, db: Session = Depends(get_db)):
    """Update asset data and keep a new version record."""
    try:
        get_asset_or_404(db, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc

    updated = update_asset(
        db,
        asset_id,
        filename=payload.filename,
        content_type=payload.content_type,
        metadata=payload.metadata,
        status=payload.status,
    )
    return {
        "asset_id": updated.id,
        "filename": updated.filename,
        "content_type": updated.content_type,
        "metadata": updated.asset_metadata,
        "status": updated.status,
        "version": updated.version,
        "created_at": updated.created_at,
        "updated_at": updated.updated_at,
    }


@router.patch("/{asset_id}/status", response_model=AssetRead)
def mark_asset_uploaded_route(asset_id: str, db: Session = Depends(get_db)):
    """Mark the asset as uploaded after the S3 upload completes."""
    try:
        get_asset_or_404(db, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc

    updated = mark_asset_uploaded(db, asset_id)
    return {
        "asset_id": updated.id,
        "filename": updated.filename,
        "content_type": updated.content_type,
        "metadata": updated.asset_metadata,
        "status": updated.status,
        "version": updated.version,
        "created_at": updated.created_at,
        "updated_at": updated.updated_at,
    }


@router.get("/{asset_id}/versions", response_model=list[AssetVersionRead])
def get_versions_route(asset_id: str, db: Session = Depends(get_db)):
    """Return the version history for an asset."""
    try:
        get_asset_or_404(db, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc

    versions = get_versions_for_asset(db, asset_id)
    return [
        {
            "version": version.version,
            "filename": version.filename,
            "content_type": version.content_type,
            "metadata": version.asset_metadata,
            "status": version.status,
            "created_at": version.created_at,
        }
        for version in versions
    ]


@router.delete("/{asset_id}", status_code=status.HTTP_200_OK)
def delete_asset_route(asset_id: str, db: Session = Depends(get_db)):
    """Delete an asset from the active list."""
    try:
        get_asset_or_404(db, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc

    delete_asset(db, asset_id)
    return {"deleted": True}
