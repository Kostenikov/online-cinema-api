from typing import Union

import aioboto3
from botocore.exceptions import BotoCoreError, ConnectionError, HTTPClientError, NoCredentialsError

from exceptions import S3ConnectionError, S3FileUploadError
from storages import S3StorageInterface


class S3StorageClient(S3StorageInterface):

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str = "eu-central-1",
    ):
        """
        Initialize the asynchronous S3 Storage Client using an aioboto3 Session.

        Args:
            endpoint_url (str): S3-compatible storage endpoint.
            access_key (str): Access key for authentication.
            secret_key (str): Secret key for authentication.
            bucket_name (str): Name of the bucket where files will be stored.
            region (str): AWS region for the bucket
        """
        self._endpoint_url = endpoint_url if endpoint_url else None
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket_name = bucket_name
        self._region = region

        self._session = aioboto3.Session(
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        )

    async def upload_file(self, file_name: str, file_data: Union[bytes, bytearray]) -> None:
        """
        Asynchronously upload a file to the S3-compatible storage.

        Args:
            file_name (str): The name of the file to be stored.
            file_data (Union[bytes, bytearray]): The file data in bytes.

        Raises:
            S3ConnectionError: If there is a connection error with S3.
            S3FileUploadError: If the file upload fails due to a BotoCore error.
        """
        try:
            client_kwargs = {"region_name": self._region}
            if self._endpoint_url:
                client_kwargs["endpoint_url"] = self._endpoint_url

            async with self._session.client("s3", **client_kwargs) as client:
                await client.put_object(
                    Bucket=self._bucket_name,
                    Key=file_name,
                    Body=file_data,
                    ContentType="image/jpeg",
                )
        except (ConnectionError, HTTPClientError, NoCredentialsError) as e:
            raise S3ConnectionError(f"Failed to connect to S3 storage: {str(e)}") from e
        except BotoCoreError as e:
            raise S3FileUploadError(f"Failed to upload to S3 storage: {str(e)}") from e

    async def get_file_url(self, file_name: str) -> str:
        """
        Generate a public URL for a file stored in the S3-compatible storage.

        Args:
            file_name (str): The name of the file stored in the bucket.

        Returns:
            str: The full URL to access the file.
        """
        if self._endpoint_url:
            return f"{self._endpoint_url}/{self._bucket_name}/{file_name}"
        else:
            return f"https://{self._bucket_name}.s3.{self._region}.amazonaws.com/{file_name}"
