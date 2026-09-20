from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssetBase(BaseModel):
    filename: str
    content_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssetCreate(AssetBase):
    pass


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
    status: str
    version: int
    created_at: datetime
    updated_at: datetime


class AssetCreateResponse(AssetRead):
    upload_url: str


class AssetVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version: int
    filename: str
    content_type: str
    metadata: dict[str, Any]
    status: str
    created_at: datetime
