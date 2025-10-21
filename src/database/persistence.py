"""
Persistence layer for loading and saving project state
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from .client import get_db
from ..utils.retry import retry, is_retryable_error


class DatabaseError(Exception):
    """Raised when database operation fails"""
    pass


class ProjectPersistence:
    """Handle all database operations for projects"""

    @staticmethod
    @retry(max_attempts=3, exceptions=(Exception,), base_delay=2.0)
    def load_project(project_id: str) -> Optional[Dict[str, Any]]:
        """
        Load project state from database with retry logic

        Args:
            project_id: UUID of the project

        Returns:
            Project data as dictionary, or None if not found

        Raises:
            DatabaseError: If database operation fails after retries
        """
        try:
            db = get_db()
            response = db.table("projects").select("*").eq("project_id", project_id).execute()

            # Validate response
            if not hasattr(response, 'data'):
                raise DatabaseError(f"Invalid database response: missing 'data' attribute")

            if response.data and len(response.data) > 0:
                return response.data[0]

            return None

        except Exception as e:
            if is_retryable_error(e):
                raise  # Will be retried by decorator
            else:
                raise DatabaseError(f"Failed to load project {project_id}: {str(e)}") from e

    @staticmethod
    @retry(max_attempts=3, exceptions=(Exception,), base_delay=2.0)
    def create_project(
        user_id: str,
        project_name: str,
        product_description: str,
        target_budget: float
    ) -> str:
        """
        Create a new project with retry logic

        Args:
            user_id: User identifier
            project_name: Name of the project
            product_description: Description of the product
            target_budget: Target daily budget

        Returns:
            project_id: UUID of created project

        Raises:
            DatabaseError: If database operation fails after retries
        """
        try:
            db = get_db()

            project_data = {
                "user_id": user_id,
                "project_name": project_name,
                "product_description": product_description,
                "target_budget": target_budget,
                "current_phase": "initialized",
                "iteration": 0,
            }

            response = db.table("projects").insert(project_data).execute()

            # Validate response
            if not hasattr(response, 'data') or not response.data or len(response.data) == 0:
                raise DatabaseError(f"Failed to create project: empty response")

            if "project_id" not in response.data[0]:
                raise DatabaseError(f"Failed to create project: missing project_id in response")

            return response.data[0]["project_id"]

        except Exception as e:
            if is_retryable_error(e):
                raise  # Will be retried by decorator
            else:
                raise DatabaseError(f"Failed to create project: {str(e)}") from e

    @staticmethod
    @retry(max_attempts=3, exceptions=(Exception,), base_delay=2.0)
    def save_project(project_data: Dict[str, Any]) -> None:
        """
        Save/update project state with retry logic

        Args:
            project_data: Complete project state dictionary

        Raises:
            DatabaseError: If database operation fails after retries
        """
        try:
            db = get_db()

            if "project_id" not in project_data:
                raise DatabaseError("project_data must contain 'project_id'")

            project_id = project_data["project_id"]

            # updated_at will be automatically updated by trigger
            response = db.table("projects").update(project_data).eq("project_id", project_id).execute()

            # Validate response
            if not hasattr(response, 'data'):
                raise DatabaseError(f"Invalid database response: missing 'data' attribute")

        except Exception as e:
            if is_retryable_error(e):
                raise  # Will be retried by decorator
            else:
                raise DatabaseError(f"Failed to save project {project_data.get('project_id', 'unknown')}: {str(e)}") from e

    @staticmethod
    def update_project_field(project_id: str, field: str, value: Any) -> None:
        """
        Update a specific field in the project

        Args:
            project_id: UUID of the project
            field: Field name to update
            value: New value
        """
        db = get_db()

        db.table("projects").update({field: value}).eq("project_id", project_id).execute()

    @staticmethod
    @retry(max_attempts=3, exceptions=(Exception,), base_delay=2.0)
    def append_to_array_field(project_id: str, field: str, item: Any) -> None:
        """
        Append an item to an array field using atomic operation to prevent race conditions

        This method uses PostgreSQL's array_append function for atomic updates,
        preventing data loss when multiple sessions modify the same array.

        Args:
            project_id: UUID of the project
            field: Array field name
            item: Item to append

        Raises:
            DatabaseError: If database operation fails after retries
        """
        try:
            db = get_db()

            # First verify project exists
            project = ProjectPersistence.load_project(project_id)
            if not project:
                raise DatabaseError(f"Project {project_id} not found")

            # Use PostgreSQL's array append via RPC call for atomic operation
            # This prevents race conditions from concurrent updates
            try:
                # Try using Supabase RPC if available
                db.rpc('append_to_project_array', {
                    'p_project_id': project_id,
                    'p_field_name': field,
                    'p_item': item
                }).execute()
            except Exception as rpc_error:
                # Fallback: Read-modify-write with optimistic locking
                # Get current array and updated_at timestamp
                current_array = project.get(field, [])
                if current_array is None:
                    current_array = []

                updated_at = project.get('updated_at')

                # Append new item
                current_array.append(item)

                # Update with optimistic locking check
                # This will fail if another process updated the record
                response = db.table("projects").update({
                    field: current_array
                }).eq("project_id", project_id).eq("updated_at", updated_at).execute()

                # Check if update succeeded (row was modified)
                if not response.data or len(response.data) == 0:
                    raise DatabaseError(
                        f"Concurrent modification detected for project {project_id}. "
                        f"Another process updated this record. Please retry."
                    )

        except Exception as e:
            if is_retryable_error(e) or "concurrent modification" in str(e).lower():
                raise  # Will be retried by decorator
            else:
                raise DatabaseError(
                    f"Failed to append to {field} for project {project_id}: {str(e)}"
                ) from e


class SessionPersistence:
    """Handle all database operations for sessions"""

    @staticmethod
    @retry(max_attempts=3, exceptions=(Exception,), base_delay=2.0)
    def create_session(
        project_id: str,
        session_num: int,
        uploaded_files: List[Dict[str, Any]]
    ) -> str:
        """
        Create a new session with retry logic

        Args:
            project_id: UUID of the project
            session_num: Session number
            uploaded_files: List of uploaded file info

        Returns:
            session_id: UUID of created session

        Raises:
            DatabaseError: If database operation fails after retries
        """
        try:
            db = get_db()

            session_data = {
                "project_id": project_id,
                "session_num": session_num,
                "uploaded_files": uploaded_files,
                "execution_status": "running",
            }

            response = db.table("sessions").insert(session_data).execute()

            # Validate response
            if not hasattr(response, 'data') or not response.data or len(response.data) == 0:
                raise DatabaseError(f"Failed to create session: empty response")

            if "session_id" not in response.data[0]:
                raise DatabaseError(f"Failed to create session: missing session_id in response")

            return response.data[0]["session_id"]

        except Exception as e:
            if is_retryable_error(e):
                raise  # Will be retried by decorator
            else:
                raise DatabaseError(f"Failed to create session: {str(e)}") from e

    @staticmethod
    def update_session(session_id: str, updates: Dict[str, Any]) -> None:
        """
        Update session data

        Args:
            session_id: UUID of the session
            updates: Dictionary of fields to update
        """
        db = get_db()

        db.table("sessions").update(updates).eq("session_id", session_id).execute()

    @staticmethod
    def complete_session(session_id: str, status: str = "completed") -> None:
        """
        Mark session as completed

        Args:
            session_id: UUID of the session
            status: Final status ('completed' or 'failed')
        """
        db = get_db()

        db.table("sessions").update({
            "execution_status": status,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("session_id", session_id).execute()


class CyclePersistence:
    """Handle all database operations for ReAct cycles"""

    @staticmethod
    def log_cycle(
        session_id: str,
        project_id: str,
        cycle_num: int,
        node_name: str,
        thought: Optional[str] = None,
        action: Optional[Dict[str, Any]] = None,
        observation: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        llm_tokens_used: Optional[int] = None
    ) -> None:
        """
        Log a ReAct cycle

        Args:
            session_id: UUID of the session
            project_id: UUID of the project
            cycle_num: Cycle number
            node_name: Name of the node
            thought: Reasoning/thought text
            action: Action taken (as JSON)
            observation: Observation/result (as JSON)
            execution_time_ms: Execution time in milliseconds
            llm_tokens_used: Number of LLM tokens used
        """
        db = get_db()

        cycle_data = {
            "session_id": session_id,
            "project_id": project_id,
            "cycle_num": cycle_num,
            "node_name": node_name,
            "thought": thought,
            "action": action,
            "observation": observation,
            "execution_time_ms": execution_time_ms,
            "llm_tokens_used": llm_tokens_used,
        }

        db.table("react_cycles").insert(cycle_data).execute()

    @staticmethod
    def get_session_cycles(session_id: str) -> List[Dict[str, Any]]:
        """
        Get all cycles for a session

        Args:
            session_id: UUID of the session

        Returns:
            List of cycle records
        """
        db = get_db()

        response = db.table("react_cycles").select("*").eq(
            "session_id", session_id
        ).order("cycle_num").execute()

        return response.data
