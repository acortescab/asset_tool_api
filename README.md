# Asset Tool API

Minimal FastAPI service for managing asset upload records and presigned S3 URLs.

## Features

- Create an asset record and receive a presigned upload URL
- Store asset metadata and status in SQLite
- Keep asset version history
- Query, update, and delete asset records
- Mark an asset as uploaded after the client finishes the S3 upload

## Tech stack

- FastAPI
- SQLAlchemy
- SQLite for the MVP
- boto3 for S3 presigned URL generation
- pytest for tests

## Why Is It Structured This Way?

The API is divided into layers to keep it simple, testable, and easy to evolve:

- `app/api` only handles requests and delegates business logic.
- `app/services` contains the upload and validation logic and coordinates with S3.
- `app/crud.py` handles data access, keeping the database isolated from the API.
- `app/models.py` y `app/schemas.py` define the data structures, avoiding mixing business rules with HTTP transport concerns.

This separation provides several benefits:

- Endpoints don't become "all-in-one" functions.
- Business logic can be tested without depending on the web server.
- S3 logic is separated from asset record storage, avoiding the need to route large files through the application.
- SQLite is sufficient for an MVP: it is easy to run, requires no external dependencies, and is well suited for development and testing.

In short, the structure prioritizes clarity and future evolution from the beginning, without introducing unnecessary complexity. For a visual overview, ver [docs/architecture.md](docs/architecture.md).

# Coverage

![CI](https://github.com/acortescab/asset_tool_api/actions/workflows/pr-checks.yml/badge.svg)

## Setup

```bash
cd /path/to/project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## Testing

```bash
pytest -q
```

## Docker

Build the image:

```bash
docker build -t asset-tool-api .
```

Run the container:

```bash
docker run -p 8000:8000 asset-tool-api
```
