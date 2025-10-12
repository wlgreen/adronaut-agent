"""
File manager for Supabase Storage integration
"""

import os
from pathlib import Path
from typing import Optional
from ..database.client import get_db


class FileManager:
    """Handle file uploads and downloads with Supabase Storage"""

    @staticmethod
    def get_bucket_name() -> str:
        """Get configured storage bucket name"""
        return os.getenv("SUPABASE_BUCKET_NAME", "campaign-files")

    @staticmethod
    def upload_file(local_path: str, project_id: str) -> str:
        """
        Upload file to Supabase Storage

        Args:
            local_path: Local file path to upload
            project_id: Project ID for organizing files

        Returns:
            storage_path: Path in Supabase Storage (e.g., "project-id/filename.csv")

        Raises:
            FileNotFoundError: If local file doesn't exist
            Exception: If upload fails
        """
        path = Path(local_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {local_path}")

        # Generate storage path: project_id/filename
        filename = path.name
        storage_path = f"{project_id}/{filename}"

        # Get Supabase client
        db = get_db()
        bucket_name = FileManager.get_bucket_name()

        # Read file content
        with open(local_path, "rb") as f:
            file_content = f.read()

        # Upload to Supabase Storage
        try:
            # Check if bucket exists, create if not
            try:
                buckets = db.storage.list_buckets()
                bucket_exists = any(b.name == bucket_name for b in buckets)

                if not bucket_exists:
                    db.storage.create_bucket(bucket_name, {"public": False})
            except Exception:
                # Bucket might already exist or we might not have list permission
                pass

            # Upload file with correct parameter format for supabase-py
            # The upload method signature: upload(path, file, file_options)
            # Note: path must be first positional argument as string
            db.storage.from_(bucket_name).upload(
                storage_path,  # path as first positional arg
                file_content,  # file as second positional arg
                {
                    "content-type": FileManager._get_content_type(filename),
                    "upsert": "true"  # Overwrite if exists
                }
            )

            return storage_path

        except Exception as e:
            error_msg = str(e)
            # If file already exists and upsert didn't work, that's okay - return the path
            if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                return storage_path
            raise Exception(f"Failed to upload file: {error_msg}")

    @staticmethod
    def download_file(storage_path: str, local_dir: str = "/tmp") -> str:
        """
        Download file from Supabase Storage to local filesystem

        Args:
            storage_path: Path in Supabase Storage
            local_dir: Local directory to download to (default: /tmp)

        Returns:
            local_path: Path to downloaded file

        Raises:
            Exception: If download fails
        """
        db = get_db()
        bucket_name = FileManager.get_bucket_name()

        # Generate local path
        filename = Path(storage_path).name
        local_path = os.path.join(local_dir, filename)

        try:
            # Download file
            response = db.storage.from_(bucket_name).download(storage_path)

            # Write to local file
            with open(local_path, "wb") as f:
                f.write(response)

            return local_path

        except Exception as e:
            raise Exception(f"Failed to download file from storage: {str(e)}")

    @staticmethod
    def file_exists(storage_path: str) -> bool:
        """
        Check if file exists in Supabase Storage

        Args:
            storage_path: Path in Supabase Storage

        Returns:
            True if file exists, False otherwise
        """
        db = get_db()
        bucket_name = FileManager.get_bucket_name()

        try:
            # List files in the directory
            folder = str(Path(storage_path).parent)
            files = db.storage.from_(bucket_name).list(folder)

            filename = Path(storage_path).name
            return any(f["name"] == filename for f in files)

        except Exception:
            return False

    @staticmethod
    def get_public_url(storage_path: str) -> Optional[str]:
        """
        Get public URL for a file (if bucket is public)

        Args:
            storage_path: Path in Supabase Storage

        Returns:
            Public URL or None
        """
        db = get_db()
        bucket_name = FileManager.get_bucket_name()

        try:
            url = db.storage.from_(bucket_name).get_public_url(storage_path)
            return url
        except Exception:
            return None

    @staticmethod
    def _get_content_type(filename: str) -> str:
        """
        Get content type based on file extension

        Args:
            filename: File name

        Returns:
            Content type string
        """
        extension = Path(filename).suffix.lower()

        content_types = {
            ".csv": "text/csv",
            ".json": "application/json",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".txt": "text/plain",
        }

        return content_types.get(extension, "application/octet-stream")


def upload_file(local_path: str, project_id: str) -> str:
    """
    Convenience function to upload a file

    Args:
        local_path: Local file path
        project_id: Project ID

    Returns:
        storage_path: Path in Supabase Storage
    """
    return FileManager.upload_file(local_path, project_id)


def download_file(storage_path: str, local_dir: str = "/tmp") -> str:
    """
    Convenience function to download a file

    Args:
        storage_path: Path in Supabase Storage
        local_dir: Local directory to download to

    Returns:
        local_path: Path to downloaded file
    """
    return FileManager.download_file(storage_path, local_dir)


def file_exists(storage_path: str) -> bool:
    """
    Convenience function to check if file exists

    Args:
        storage_path: Path in Supabase Storage

    Returns:
        True if file exists
    """
    return FileManager.file_exists(storage_path)
