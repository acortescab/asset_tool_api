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

# Coverage

![CI](https://github.com/acortescab/asset_tool_api/actions/workflows/pr-checks.yml/badge.svg)
[![codecov](https://codecov.io/gh/acortescab/asset_tool_api/graph/badge.svg)](https://codecov.io/gh/acortescab/asset_tool_api)

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
