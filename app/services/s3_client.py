from __future__ import annotations

from app.config import AWS_ACCESS_KEY_ID, AWS_REGION, AWS_S3_BUCKET, AWS_SECRET_ACCESS_KEY


def generate_presigned_upload_url(object_key: str, content_type: str, expires_in: int = 3600) -> str:
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        import boto3

        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        return s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": AWS_S3_BUCKET,
                "Key": object_key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )

    return (
        f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_key}"
        f"?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Expires={expires_in}"
        f"&X-Amz-SignedHeaders=content-type&X-Amz-Signature=dummy"
    )
