from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def _migrate_legacy_asset_schema() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "assets" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("assets")}
    if "version" not in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE assets RENAME TO assets_legacy"))
        connection.execute(
            text(
                """
                CREATE TABLE assets (
                    id VARCHAR PRIMARY KEY,
                    filename VARCHAR NOT NULL,
                    content_type VARCHAR NOT NULL,
                    metadata JSON,
                    status VARCHAR NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    deleted BOOLEAN NOT NULL DEFAULT 0
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO assets (id, filename, content_type, metadata, status, created_at, updated_at, deleted)
                SELECT id, filename, content_type, metadata, status, created_at, updated_at, deleted
                FROM assets_legacy
                """
            )
        )
        connection.execute(text("DROP TABLE assets_legacy"))


def init_db() -> None:
    # Create all models; then ensure simple runtime migrations for SQLite
    Base.metadata.create_all(bind=engine)
    # For simple legacy migrations (SQLite) run the helper which performs renames/recreates if needed
    _migrate_legacy_asset_schema()

    # After metadata.create_all, ensure owner column exists on assets (simple ALTER TABLE)
    if DATABASE_URL.startswith("sqlite"):
        inspector = inspect(engine)
        if "assets" in inspector.get_table_names():
            columns = {column["name"] for column in inspector.get_columns("assets")}
            if "owner" not in columns:
                with engine.begin() as connection:
                    connection.execute(text("ALTER TABLE assets ADD COLUMN owner VARCHAR"))
        # Add owner to asset_versions if missing
        if "asset_versions" in inspector.get_table_names():
            av_columns = {column["name"] for column in inspector.get_columns("asset_versions")}
            if "owner" not in av_columns:
                with engine.begin() as connection:
                    connection.execute(text("ALTER TABLE asset_versions ADD COLUMN owner VARCHAR"))
        # Ensure asset_upload_sessions table exists
        if "asset_upload_sessions" not in inspector.get_table_names():
            Base.metadata.create_all(bind=engine)
