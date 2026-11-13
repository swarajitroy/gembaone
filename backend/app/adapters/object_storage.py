"""Object storage adapter."""
import hashlib
from pathlib import Path


class ObjectRef:
    """Reference to stored object."""

    def __init__(self, storage_key: str, bucket: str):
        self.storage_key = storage_key
        self.bucket = bucket


class ObjectMetadata:
    """Metadata for stored object."""

    def __init__(self, content_type: str, byte_size: int, sha256_hex: str):
        self.content_type = content_type
        self.byte_size = byte_size
        self.sha256_hex = sha256_hex


class DownloadLink:
    """Signed download link."""

    def __init__(self, url: str, expires_at: str):
        self.url = url
        self.expires_at = expires_at


class ObjectStorageAdapter:
    """Object storage adapter for file storage.

    Local: file-based emulation (backend/uploads/<bucket>/<key>)
    Deployed: cloud object storage (S3, Azure Blob, GCS)
    """

    def __init__(self, base_path: str | None = None):
        """Initialize object storage adapter.

        Args:
            base_path: Base directory for local storage. Defaults to backend/uploads.
        """
        if base_path is None:
            # Default to backend/uploads directory
            backend_dir = Path(__file__).resolve().parents[2]
            base_path = str(backend_dir / "uploads")
        self.base_path = Path(base_path)

    def put_object(
        self,
        path: str,
        data: bytes,
        content_type: str,
        immutable: bool = False,
    ) -> ObjectRef:
        """Store object.

        Args:
            path: Storage path in format "bucket/key"
            data: Binary data to store
            content_type: MIME type
            immutable: Whether object is immutable

        Returns:
            ObjectRef with storage location
        """
        # Parse bucket and key from path
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError("Path must be in format 'bucket/key'")

        bucket, key = parts

        # Create directory structure
        file_path = self.base_path / bucket / key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file
        file_path.write_bytes(data)

        return ObjectRef(storage_key=key, bucket=bucket)

    def get_signed_download(self, path: str, expires_at: str) -> DownloadLink:
        """Get signed download URL.

        For local storage, returns a simple file path.
        In production, this would generate a signed URL from cloud storage.

        Args:
            path: Storage path in format "bucket/key"
            expires_at: ISO 8601 expiration timestamp

        Returns:
            DownloadLink with URL and expiration
        """
        # Parse bucket and key from path
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError("Path must be in format 'bucket/key'")

        bucket, key = parts
        file_path = self.base_path / bucket / key

        # For local storage, return file:// URL
        # In production, this would be a signed S3/Azure/GCS URL
        url = f"file://{file_path.as_posix()}"

        return DownloadLink(url=url, expires_at=expires_at)

    def get_object(self, path: str) -> bytes:
        """Retrieve object data.

        Args:
            path: Storage path in format "bucket/key"

        Returns:
            Binary data of the object

        Raises:
            FileNotFoundError: If object does not exist
        """
        # Parse bucket and key from path
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError("Path must be in format 'bucket/key'")

        bucket, key = parts
        file_path = self.base_path / bucket / key

        if not file_path.exists():
            raise FileNotFoundError(f"Object not found: {path}")

        return file_path.read_bytes()

    def stat_object(self, path: str) -> ObjectMetadata:
        """Get object metadata.

        Args:
            path: Storage path in format "bucket/key"

        Returns:
            ObjectMetadata with content type, size, and checksum
        """
        # Parse bucket and key from path
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise ValueError("Path must be in format 'bucket/key'")

        bucket, key = parts
        file_path = self.base_path / bucket / key

        if not file_path.exists():
            raise FileNotFoundError(f"Object not found: {path}")

        # Read file and compute metadata
        data = file_path.read_bytes()
        sha256_hex = hashlib.sha256(data).hexdigest()
        byte_size = len(data)

        # Infer content type from extension
        content_type = "application/octet-stream"
        suffix = file_path.suffix.lower()
        content_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
        }
        if suffix in content_type_map:
            content_type = content_type_map[suffix]

        return ObjectMetadata(
            content_type=content_type,
            byte_size=byte_size,
            sha256_hex=sha256_hex,
        )
