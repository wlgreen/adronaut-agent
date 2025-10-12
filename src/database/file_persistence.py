"""
Persistence layer for uploaded files and their cached insights
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from .client import get_db


class FilePersistence:
    """Handle all database operations for uploaded_files table"""

    @staticmethod
    def save_file_record(
        project_id: str,
        storage_path: str,
        original_filename: str,
        file_type: Optional[str] = None,
        file_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a record for an uploaded file

        Args:
            project_id: UUID of the project
            storage_path: Path in Supabase Storage
            original_filename: Original filename
            file_type: Type of file (historical, experiment_results, enrichment)
            file_metadata: Metadata dict (row_count, columns, etc.)

        Returns:
            file_id: UUID of created record
        """
        db = get_db()

        file_data = {
            "project_id": project_id,
            "storage_path": storage_path,
            "original_filename": original_filename,
            "file_type": file_type,
            "file_metadata": file_metadata or {},
        }

        response = db.table("uploaded_files").insert(file_data).execute()

        return response.data[0]["file_id"]

    @staticmethod
    def get_file_record(project_id: str, storage_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file record by project_id and storage_path

        Args:
            project_id: UUID of the project
            storage_path: Path in Supabase Storage

        Returns:
            File record dict or None if not found
        """
        db = get_db()

        response = (
            db.table("uploaded_files")
            .select("*")
            .eq("project_id", project_id)
            .eq("storage_path", storage_path)
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]

        return None

    @staticmethod
    def update_file_analysis(
        project_id: str,
        storage_path: str,
        file_metadata: Dict[str, Any],
        file_type: str
    ) -> None:
        """
        Update file with analysis metadata

        Args:
            project_id: UUID of the project
            storage_path: Path in Supabase Storage
            file_metadata: Analyzed metadata (row_count, columns, date_range, etc.)
            file_type: Detected file type
        """
        db = get_db()

        update_data = {
            "file_metadata": file_metadata,
            "file_type": file_type,
            "last_analyzed_at": datetime.utcnow().isoformat(),
        }

        db.table("uploaded_files").update(update_data).eq(
            "project_id", project_id
        ).eq("storage_path", storage_path).execute()

    @staticmethod
    def cache_file_insights(
        project_id: str,
        storage_path: str,
        insights: Dict[str, Any]
    ) -> None:
        """
        Cache insights generated from this file

        Args:
            project_id: UUID of the project
            storage_path: Path in Supabase Storage
            insights: Insights dict to cache
        """
        db = get_db()

        update_data = {
            "insights_cache": insights,
            "last_analyzed_at": datetime.utcnow().isoformat(),
        }

        db.table("uploaded_files").update(update_data).eq(
            "project_id", project_id
        ).eq("storage_path", storage_path).execute()

    @staticmethod
    def get_project_files(project_id: str) -> List[Dict[str, Any]]:
        """
        Get all files for a project

        Args:
            project_id: UUID of the project

        Returns:
            List of file records
        """
        db = get_db()

        response = (
            db.table("uploaded_files")
            .select("*")
            .eq("project_id", project_id)
            .order("uploaded_at", desc=True)
            .execute()
        )

        return response.data

    @staticmethod
    def delete_file_record(project_id: str, storage_path: str) -> None:
        """
        Delete a file record

        Args:
            project_id: UUID of the project
            storage_path: Path in Supabase Storage
        """
        db = get_db()

        db.table("uploaded_files").delete().eq("project_id", project_id).eq(
            "storage_path", storage_path
        ).execute()

    @staticmethod
    def upsert_file_record(
        project_id: str,
        storage_path: str,
        original_filename: str,
        file_type: Optional[str] = None,
        file_metadata: Optional[Dict[str, Any]] = None,
        insights_cache: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Insert or update a file record

        Args:
            project_id: UUID of the project
            storage_path: Path in Supabase Storage
            original_filename: Original filename
            file_type: Type of file
            file_metadata: Metadata dict
            insights_cache: Cached insights

        Returns:
            file_id: UUID of record
        """
        db = get_db()

        # Check if exists
        existing = FilePersistence.get_file_record(project_id, storage_path)

        file_data = {
            "project_id": project_id,
            "storage_path": storage_path,
            "original_filename": original_filename,
            "file_type": file_type,
            "file_metadata": file_metadata or {},
        }

        if insights_cache:
            file_data["insights_cache"] = insights_cache
            file_data["last_analyzed_at"] = datetime.utcnow().isoformat()

        if existing:
            # Update existing record
            db.table("uploaded_files").update(file_data).eq(
                "project_id", project_id
            ).eq("storage_path", storage_path).execute()
            return existing["file_id"]
        else:
            # Insert new record
            response = db.table("uploaded_files").insert(file_data).execute()
            return response.data[0]["file_id"]
