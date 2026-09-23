from __future__ import annotations

from typing import Any
from datetime import datetime

from app.database import SessionLocal
from app import config
from app.services.s3_client import (
    create_multipart_upload,
    generate_presigned_upload_url,
    generate_presigned_part_url,
    complete_multipart_upload,
    abort_multipart_upload,
)
from app import crud


def create_asset_service(filename: str, content_type: str, metadata: dict[str, Any], upload_mode: str | None = None, file_size: int | None = None) -> dict:
    db = SessionLocal()
    try:
        asset = crud.create_asset(db, filename=filename, content_type=content_type, metadata=metadata)

        use_multipart = False
        if upload_mode == "multipart":
            use_multipart = True
        elif file_size and file_size > config.MULTIPART_THRESHOLD:
            use_multipart = True

        upload_url = None
        upload_id = None
        upload_mode_out = "single"
        if use_multipart:
            multipart = multipart_initiate_service(asset=asset, db=db)
            upload_id = multipart["upload_id"]
            upload_mode_out = multipart["upload_mode"]
        else:
            upload_url = generate_presigned_upload_url(object_key=f"{asset.id}/{asset.filename}", content_type=asset.content_type)

        # Compute current version without triggering lazy loads on a detached instance
        current_version = crud.get_next_asset_version(db, asset.id) - 1
        # Serialize asset into a plain object to avoid DetachedInstanceError after closing session
        asset_obj = {
            "id": asset.id,
            "filename": asset.filename,
            "content_type": asset.content_type,
            "asset_metadata": asset.asset_metadata,
            "owner": asset.owner,
            "status": asset.status,
            "version": current_version,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
        }
        return {
            "asset": asset_obj,
            "upload_url": upload_url,
            "upload_mode": upload_mode_out,
            "upload_id": upload_id,
        }
    finally:
        db.close()

def multipart_initiate_service(asset, db) -> dict:
    object_key = f"{asset.id}/{asset.filename}"
    upload_id = create_multipart_upload(object_key=object_key, content_type=asset.content_type)
    # persist session
    crud.create_upload_session(db, asset_id=asset.id, upload_id=upload_id)
    return {"upload_id": upload_id, "upload_mode": "multipart"}


def presign_part_service(asset_id: str, part_number: int, upload_id: str) -> str:
    db = SessionLocal()
    try:
        asset = crud.get_asset_or_404(db, asset_id)
        object_key = f"{asset.id}/{asset.filename}"
        return generate_presigned_part_url(object_key=object_key, upload_id=upload_id, part_number=part_number)
    finally:
        db.close()


def multipart_status_service(asset_id: str, upload_id: str | None = None) -> dict:
    db = SessionLocal()
    try:
        crud.get_asset_or_404(db, asset_id)
        q = db.query(crud.AssetUploadSession).filter(crud.AssetUploadSession.asset_id == asset_id)
        if upload_id:
            q = q.filter(crud.AssetUploadSession.upload_id == upload_id)
        session = q.first()
        if session is None:
            raise ValueError("Upload session not found")
        return {"upload_id": session.upload_id, "parts": session.parts or [], "status": session.status}
    finally:
        db.close()


def multipart_complete_service(asset_id: str, upload_id: str, parts: list[dict]) -> dict:
    db = SessionLocal()
    try:
        asset = crud.get_asset_or_404(db, asset_id)
        object_key = f"{asset.id}/{asset.filename}"
        resp = complete_multipart_upload(object_key=object_key, upload_id=upload_id, parts=parts)
        # mark asset uploaded
        updated = crud.mark_asset_uploaded(db, asset_id)
        # update session status
        db.query(crud.AssetUploadSession).filter(crud.AssetUploadSession.asset_id == asset_id, crud.AssetUploadSession.upload_id == upload_id).update({"status": "completed"})
        db.commit()
        return {"asset_id": updated.id, "status": updated.status, "s3_response": resp}
    finally:
        db.close()


def multipart_abort_service(asset_id: str, upload_id: str) -> bool:
    db = SessionLocal()
    try:
        asset = crud.get_asset_or_404(db, asset_id)
        object_key = f"{asset.id}/{asset.filename}"
        try:
            abort_multipart_upload(object_key=object_key, upload_id=upload_id)
        except Exception:
            pass
        db.query(crud.AssetUploadSession).filter(crud.AssetUploadSession.asset_id == asset_id, crud.AssetUploadSession.upload_id == upload_id).update({"status": "aborted"})
        db.commit()
        return True
    finally:
        db.close()


def list_assets_service() -> list:
    db = SessionLocal()
    try:
        assets = crud.list_assets(db)
        # serialize
        out = []
        for asset in assets:
            ver = crud.get_next_asset_version(db, asset.id) - 1
            out.append(
                {
                    "id": asset.id,
                    "filename": asset.filename,
                    "content_type": asset.content_type,
                    "asset_metadata": asset.asset_metadata,
                    "owner": asset.owner,
                    "status": asset.status,
                    "version": ver,
                    "created_at": asset.created_at,
                    "updated_at": asset.updated_at,
                }
            )
        return out
    finally:
        db.close()


def get_asset_service(asset_id: str):
    db = SessionLocal()
    try:
        asset = crud.get_asset_or_404(db, asset_id)
        ver = crud.get_next_asset_version(db, asset.id) - 1
        return {
            "id": asset.id,
            "filename": asset.filename,
            "content_type": asset.content_type,
            "asset_metadata": asset.asset_metadata,
            "owner": asset.owner,
            "status": asset.status,
            "version": ver,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
        }
    finally:
        db.close()


def get_versions_service(asset_id: str):
    db = SessionLocal()
    try:
        versions = crud.get_versions_for_asset(db, asset_id)
        out = []
        for v in versions:
            out.append({
                "version": v.version,
                "filename": v.filename,
                "content_type": v.content_type,
                "asset_metadata": v.asset_metadata,
                "status": v.status,
                "created_at": v.created_at,
            })
        return out
    finally:
        db.close()


def update_asset_service(asset_id: str, filename: str | None, content_type: str | None, metadata: dict | None, status: str | None):
    db = SessionLocal()
    try:
        updated = crud.update_asset(db, asset_id, filename=filename, content_type=content_type, metadata=metadata, status=status)
        # compute current version without lazy-loading relationship after session closed
        ver = crud.get_next_asset_version(db, updated.id) - 1
        return {
            "id": updated.id,
            "filename": updated.filename,
            "content_type": updated.content_type,
            "asset_metadata": updated.asset_metadata,
            "owner": updated.owner,
            "status": updated.status,
            "version": ver,
            "created_at": updated.created_at,
            "updated_at": updated.updated_at,
        }
    finally:
        db.close()


def delete_asset_service(asset_id: str):
    db = SessionLocal()
    try:
        crud.delete_asset(db, asset_id)
        return True
    finally:
        db.close()
