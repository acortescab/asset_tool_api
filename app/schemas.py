from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssetBase(BaseModel):
    filename: str
    content_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    owner: str | None = None


class AssetCreate(AssetBase):
    upload_mode: str | None = None
    file_size: int | None = None


class AssetUpdate(BaseModel):
    filename: str | None = None
    content_type: str | None = None
    metadata: dict[str, Any] | None = None
    status: str | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: str
    filename: str
    content_type: str
    metadata: dict[str, Any]
    owner: str | None = None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime


class AssetCreateResponse(AssetRead):
    upload_url: str | None = None
    upload_mode: str | None = None
    upload_id: str | None = None


class InitiateMultipartResponse(BaseModel):
    upload_id: str


class PresignPartRequest(BaseModel):
    upload_id: str
    part_number: int


class MultipartStatusRequest(BaseModel):
    upload_id: str | None = None


class Part(BaseModel):
    part_number: int = Field(..., alias="PartNumber")
    etag: str = Field(..., alias="ETag")


class MultipartCompleteRequest(BaseModel):
    upload_id: str
    parts: list[Part]


class AbortMultipartRequest(BaseModel):
    upload_id: str


class PresignedPartResponse(BaseModel):
    part_number: int
    presigned_url: str


class MultipartStatusResponse(BaseModel):
    upload_id: str
    parts: list[dict]
    status: str


class AssetVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version: int
    filename: str
    content_type: str
    metadata: dict[str, Any]
    status: str
    created_at: datetime
