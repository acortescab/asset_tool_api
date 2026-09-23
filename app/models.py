from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class AssetUploadSession(Base):
    __tablename__ = "asset_upload_sessions"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    upload_id = Column(String, nullable=False)
    parts = Column(JSON, default=list)  # list of {part_number, etag, size, uploaded_at}
    status = Column(String, default="in_progress", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    asset = relationship("Asset")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    asset_metadata = Column("metadata", JSON, default=dict)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    versions = relationship("AssetVersion", back_populates="asset", cascade="all, delete-orphan")

    @property
    def version(self) -> int:
        return max((version.version for version in self.versions), default=0)


class AssetVersion(Base):
    __tablename__ = "asset_versions"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String, ForeignKey("assets.id"), nullable=False)
    version = Column(Integer, nullable=False)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    owner = Column(String, nullable=True)
    asset_metadata = Column("metadata", JSON, default=dict)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    asset = relationship("Asset", back_populates="versions")
