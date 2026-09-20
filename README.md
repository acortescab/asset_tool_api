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

## API

### Health

```bash
GET /health
```

### Create asset

```bash
POST /assets
```

Body example:

```json
{
  "filename": "photo.jpg",
  "content_type": "image/jpeg",
  "metadata": {
    "owner": "demo",
    "category": "marketing"
  }
}
```

Response includes a presigned upload URL and the asset status.

### List assets

```bash
GET /assets
```

### Get asset

```bash
GET /assets/{asset_id}
```

### Update asset

```bash
PATCH /assets/{asset_id}
```

### Mark uploaded

```bash
PATCH /assets/{asset_id}/status
```

This is intended for the downstream SQS/Lambda workflow after the client finishes uploading to S3.

### Delete asset

```bash
DELETE /assets/{asset_id}
```

## Testing

```bash
pytest -q
```
