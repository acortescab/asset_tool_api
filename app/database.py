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
    Base.metadata.create_all(bind=engine)
    _migrate_legacy_asset_schema()
