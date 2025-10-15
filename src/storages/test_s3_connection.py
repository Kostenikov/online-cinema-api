import asyncio

from config import get_settings
from storages import S3StorageClient


async def test_aws_s3_connection():
    """Test connection to AWS S3 bucket"""
    settings = get_settings()

    print(f"Testing connection to AWS S3...")
    print(f"Bucket: {settings.S3_BUCKET_NAME}")
    print(f"Region: {settings.S3_REGION}")

    s3_client = S3StorageClient(
        endpoint_url=settings.S3_STORAGE_ENDPOINT or None,
        access_key=settings.S3_STORAGE_ACCESS_KEY,
        secret_key=settings.S3_STORAGE_SECRET_KEY,
        bucket_name=settings.S3_BUCKET_NAME,
        region=settings.S3_REGION,
    )

    try:
        test_data = b"Hello from AWS S3!"
        test_filename = "test-connection.txt"

        print(f"\nUploading test file: {test_filename}")
        await s3_client.upload_file(test_filename, test_data)
        print("✓ Upload successful!")

        # Get URL
        url = await s3_client.get_file_url(test_filename)
        print(f"\n✓ File URL: {url}")
        print("\nConnection test completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease check:")
        print("1. AWS credentials are correct")
        print("2. Bucket exists and name is correct")
        print("3. IAM user has proper permissions")
        print("4. Region is correct")


if __name__ == "__main__":
    asyncio.run(test_aws_s3_connection())
