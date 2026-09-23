from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    AssetCreate,
    AssetCreateResponse,
    AssetRead,
    AssetUpdate,
    AssetVersionRead,
    MultipartStatusResponse,
    MultipartStatusRequest,
    PresignedPartResponse,
    PresignPartRequest,
    MultipartCompleteRequest,
    AbortMultipartRequest,
)
from app.services.assets_service import (
    create_asset_service,
    delete_asset_service,
    get_asset_service,
    get_versions_service,
    list_assets_service,
    multipart_abort_service,
    multipart_complete_service,
    multipart_status_service,
    presign_part_service,
    update_asset_service,
)

router = APIRouter(prefix="/assets", tags=["assets"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=AssetCreateResponse)
def create_asset_route(payload: AssetCreate):
    """Create an asset and return a presigned upload URL or multipart session for the client."""
    result = create_asset_service(
        filename=payload.filename,
        content_type=payload.content_type,
        metadata=payload.metadata,
        upload_mode=payload.upload_mode,
        file_size=payload.file_size,
    )

    asset = result["asset"]
    return {
        "asset_id": asset["id"],
        "filename": asset["filename"],
        "content_type": asset["content_type"],
        "metadata": asset["asset_metadata"],
        "owner": asset["owner"],
        "status": asset["status"],
        "version": asset["version"],
        "created_at": asset["created_at"],
        "updated_at": asset["updated_at"],
        "upload_url": result.get("upload_url"),
        "upload_mode": result.get("upload_mode"),
        "upload_id": result.get("upload_id"),
    }

@router.post("/{asset_id}/multipart/{part_number}", response_model=PresignedPartResponse)
def presign_part(asset_id: str, part_number: int, payload: PresignPartRequest):
    try:
        url = presign_part_service(asset_id=asset_id, part_number=part_number, upload_id=payload.upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc
    return {"part_number": part_number, "presigned_url": url}


@router.get("/{asset_id}/multipart/status", response_model=MultipartStatusResponse)
def multipart_status(asset_id: str, payload: MultipartStatusRequest):
    try:
        stat = multipart_status_service(asset_id=asset_id, upload_id=payload.upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return stat


@router.post("/{asset_id}/multipart/complete")
def multipart_complete(asset_id: str, payload: MultipartCompleteRequest):
    try:
        parts = [{"ETag": p.etag, "PartNumber": p.part_number} for p in payload.parts]
        resp = multipart_complete_service(asset_id=asset_id, upload_id=payload.upload_id, parts=parts)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return resp


@router.post("/{asset_id}/multipart/abort")
def multipart_abort(asset_id: str, payload: AbortMultipartRequest):
    try:
        multipart_abort_service(asset_id=asset_id, upload_id=payload.upload_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"aborted": True}


@router.get("", response_model=list[AssetRead])
def list_assets_route():
    """Return all active assets."""
    assets = list_assets_service()
    return [
        {
            "asset_id": asset["id"],
            "filename": asset["filename"],
            "content_type": asset["content_type"],
            "metadata": asset["asset_metadata"],
            "status": asset["status"],
            "version": asset["version"],
            "created_at": asset["created_at"],
            "updated_at": asset["updated_at"],
        }
        for asset in assets
    ]


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset_route(asset_id: str):
    """Get a single asset by its identifier."""
    try:
        asset = get_asset_service(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc
    return {
        "asset_id": asset["id"],
        "filename": asset["filename"],
        "content_type": asset["content_type"],
        "metadata": asset["asset_metadata"],
        "status": asset["status"],
        "version": asset["version"],
        "created_at": asset["created_at"],
        "updated_at": asset["updated_at"],
    }


@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset_route(asset_id: str, payload: AssetUpdate):
    """Update asset data and keep a new version record."""
    try:
        updated = update_asset_service(
            asset_id,
            filename=payload.filename,
            content_type=payload.content_type,
            metadata=payload.metadata,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc
    return {
        "asset_id": updated["id"],
        "filename": updated["filename"],
        "content_type": updated["content_type"],
        "metadata": updated["asset_metadata"],
        "status": updated["status"],
        "version": updated["version"],
        "created_at": updated["created_at"],
        "updated_at": updated["updated_at"],
    }


@router.patch("/{asset_id}/status", response_model=AssetRead)
def mark_asset_uploaded_route(asset_id: str):
    """Mark the asset as uploaded after the S3 upload completes."""
    try:
        updated = update_asset_service(asset_id, None, None, None, "uploaded")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc
    return {
        "asset_id": updated["id"],
        "filename": updated["filename"],
        "content_type": updated["content_type"],
        "metadata": updated["asset_metadata"],
        "status": updated["status"],
        "version": updated["version"],
        "created_at": updated["created_at"],
        "updated_at": updated["updated_at"],
    }


@router.get("/{asset_id}/versions", response_model=list[AssetVersionRead])
def get_versions_route(asset_id: str):
    """Return the version history for an asset."""
    try:
        versions = get_versions_service(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc
    return [
        {
            "version": version["version"],
            "filename": version["filename"],
            "content_type": version["content_type"],
            "metadata": version["asset_metadata"],
            "status": version["status"],
            "created_at": version["created_at"],
        }
        for version in versions
    ]


@router.delete("/{asset_id}", status_code=status.HTTP_200_OK)
def delete_asset_route(asset_id: str):
    """Delete an asset from the active list."""
    try:
        delete_asset_service(asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found") from exc
    return {"deleted": True}
