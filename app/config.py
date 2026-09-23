import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./assets.db")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "demo-assets")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# Multipart threshold (bytes) — default 10 MiB
MULTIPART_THRESHOLD = int(os.getenv("MULTIPART_THRESHOLD", 10 * 1024 * 1024))
