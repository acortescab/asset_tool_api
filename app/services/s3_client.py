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


def create_multipart_upload(object_key: str, content_type: str) -> str:
    """Call S3 CreateMultipartUpload and return the upload_id (or stubbed id)."""
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        import boto3

        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        resp = s3.create_multipart_upload(Bucket=AWS_S3_BUCKET, Key=object_key, ContentType=content_type)
        return resp["UploadId"]

    # stubbed upload id for local/dev
    return f"local-mpu-{object_key}"


def generate_presigned_part_url(object_key: str, upload_id: str, part_number: int, expires_in: int = 3600) -> str:
    """Generate a presigned URL for UploadPart."""
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        import boto3

        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        return s3.generate_presigned_url(
            ClientMethod="upload_part",
            Params={
                "Bucket": AWS_S3_BUCKET,
                "Key": object_key,
                "UploadId": upload_id,
                "PartNumber": part_number,
            },
            ExpiresIn=expires_in,
        )

    return f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_key}?uploadId={upload_id}&partNumber={part_number}&signature=dummy"


def complete_multipart_upload(object_key: str, upload_id: str, parts: list[dict]) -> dict:
    """Call S3 CompleteMultipartUpload. `parts` is [{'ETag': etag, 'PartNumber': n}, ...]"""
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        import boto3

        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        resp = s3.complete_multipart_upload(
            Bucket=AWS_S3_BUCKET,
            Key=object_key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        return resp

    return {"Location": f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{object_key}", "Bucket": AWS_S3_BUCKET, "Key": object_key, "ETag": "\"local-etag\""}


def abort_multipart_upload(object_key: str, upload_id: str) -> None:
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        import boto3

        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        )

        s3.abort_multipart_upload(Bucket=AWS_S3_BUCKET, Key=object_key, UploadId=upload_id)
    # otherwise noop for local/dev
