"""S3 operations examples using Kumo."""

from dotenv import load_dotenv

from ..kumo_compat import KumoSession

load_dotenv()

_session = KumoSession()


def get_s3_client():
    """Return a Kumo-compatible S3 client."""
    return _session.client("s3")


def create_bucket(bucket_name):
    """Create an S3 bucket."""
    s3 = get_s3_client()
    s3.create_bucket(Bucket=bucket_name)
    print(f"Created bucket: {bucket_name}")


def list_buckets():
    """List all S3 buckets."""
    s3 = get_s3_client()
    response = s3.list_buckets()
    print("Existing buckets:")
    for bucket in response["Buckets"]:
        print(f"  {bucket['Name']}")


def upload_file(bucket_name, file_name, content):
    """Upload a file to an S3 bucket."""
    s3 = get_s3_client()
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=content)
    print(f"Uploaded {file_name} to {bucket_name}")


if __name__ == "__main__":
    # Example usage
    bucket_name = "test-bucket"
    create_bucket(bucket_name)
    list_buckets()
    upload_file(bucket_name, "test.txt", "Hello Kumo!")
