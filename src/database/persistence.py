"""
Persistence layer for loading and saving project state
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from .client import get_db


class ProjectPersistence:
    """Handle all database operations for projects"""

    @staticmethod
    def load_project(project_id: str) -> Optional[Dict[str, Any]]:
        """
        Load project state from database

        Args:
            project_id: UUID of the project

        Returns:
            Project data as dictionary, or None if not found
        """
        db = get_db()

        response = db.table("projects").select("*").eq("project_id", project_id).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]

        return None

    @staticmethod
    def create_project(
        user_id: str,
        project_name: str,
        product_description: str,
        target_budget: float
    ) -> str:
        """
        Create a new project

        Args:
            user_id: User identifier
            project_name: Name of the project
            product_description: Description of the product
            target_budget: Target daily budget

        Returns:
            project_id: UUID of created project
        """
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

        return response.data[0]["project_id"]

    @staticmethod
    def save_project(project_data: Dict[str, Any]) -> None:
        """
        Save/update project state

        Args:
            project_data: Complete project state dictionary
        """
        db = get_db()

        project_id = project_data["project_id"]

        # updated_at will be automatically updated by trigger
        db.table("projects").update(project_data).eq("project_id", project_id).execute()

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
    def append_to_array_field(project_id: str, field: str, item: Any) -> None:
        """
        Append an item to an array field (like experiment_results, config_history)

        Args:
            project_id: UUID of the project
            field: Array field name
            item: Item to append
        """
        db = get_db()

        # First get current array
        project = ProjectPersistence.load_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        current_array = project.get(field, [])
        if current_array is None:
            current_array = []

        # Append new item
        current_array.append(item)

        # Update
        db.table("projects").update({field: current_array}).eq("project_id", project_id).execute()


class SessionPersistence:
    """Handle all database operations for sessions"""

    @staticmethod
    def create_session(
        project_id: str,
        session_num: int,
        uploaded_files: List[Dict[str, Any]]
    ) -> str:
        """
        Create a new session

        Args:
            project_id: UUID of the project
            session_num: Session number
            uploaded_files: List of uploaded file info

        Returns:
            session_id: UUID of created session
        """
        db = get_db()

        session_data = {
            "project_id": project_id,
            "session_num": session_num,
            "uploaded_files": uploaded_files,
            "execution_status": "running",
        }

        response = db.table("sessions").insert(session_data).execute()

        return response.data[0]["session_id"]

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


class TestCreativePersistence:
    """Handle all database operations for test creative results"""

    @staticmethod
    def save_test_creative(
        workflow_result: Dict[str, Any],
        product_description: str,
        product_image_path: Optional[str] = None,
        project_id: Optional[str] = None,
        required_keywords: Optional[List[str]] = None,
        brand_name: Optional[str] = None
    ) -> str:
        """
        Save test creative workflow results to database.

        Args:
            workflow_result: Complete workflow result from run_test_creative_workflow
            product_description: Product description used
            product_image_path: Path to product image (optional)
            project_id: Optional project reference
            required_keywords: Keywords that were checked for
            brand_name: Brand name that was checked for

        Returns:
            test_id: UUID of created test creative record
        """
        db = get_db()

        # Extract workflow steps
        steps = workflow_result.get("workflow_steps", {})
        summary = workflow_result.get("summary", {})

        # Prepare data
        test_data = {
            "project_id": project_id,
            "product_description": product_description,
            "product_image_path": product_image_path,
            "platform": summary.get("platform", "Meta"),
            "audience": summary.get("audience"),
            "creative_style": summary.get("creative_style"),
            "step1_generation": steps.get("step1_generation", {}),
            "step2_review": steps.get("step2_review", {}),
            "step3_creative": steps.get("step3_creative", {}),
            "step4_rating": steps.get("step4_rating", {}),
            "overall_score": summary.get("final_score", 0),
            "prompt_changed": summary.get("prompt_changed_in_review", False),
            "validation_passed": summary.get("validation_passed", True),
            "has_project_context": project_id is not None,
            "context_metadata": workflow_result.get("metadata", {}),
            "required_keywords": required_keywords or [],
            "brand_name": brand_name,
            "full_result": workflow_result
        }

        response = db.table("test_creatives").insert(test_data).execute()

        return response.data[0]["test_id"]

    @staticmethod
    def load_test_creative(test_id: str) -> Optional[Dict[str, Any]]:
        """
        Load test creative result from database.

        Args:
            test_id: UUID of the test creative

        Returns:
            Test creative data as dictionary, or None if not found
        """
        db = get_db()

        response = db.table("test_creatives").select("*").eq("test_id", test_id).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]

        return None

    @staticmethod
    def get_test_creatives_by_project(project_id: str) -> List[Dict[str, Any]]:
        """
        Get all test creatives for a project.

        Args:
            project_id: UUID of the project

        Returns:
            List of test creative records
        """
        db = get_db()

        response = db.table("test_creatives").select("*").eq(
            "project_id", project_id
        ).order("created_at", desc=True).execute()

        return response.data

    @staticmethod
    def get_test_creatives_by_platform(platform: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get test creatives by platform.

        Args:
            platform: Platform name (Meta/TikTok/Google)
            limit: Maximum number of results

        Returns:
            List of test creative records
        """
        db = get_db()

        response = db.table("test_creatives").select("*").eq(
            "platform", platform
        ).order("created_at", desc=True).limit(limit).execute()

        return response.data

    @staticmethod
    def get_top_scoring_creatives(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top-scoring test creatives.

        Args:
            limit: Number of results to return

        Returns:
            List of top-scoring test creative records
        """
        db = get_db()

        response = db.table("test_creatives").select("*").order(
            "overall_score", desc=True
        ).limit(limit).execute()

        return response.data

    @staticmethod
    def get_analytics_summary() -> Dict[str, Any]:
        """
        Get analytics summary from the test_creative_analytics view.

        Returns:
            Dict with analytics by platform
        """
        db = get_db()

        response = db.table("test_creative_analytics").select("*").execute()

        # Convert to dict keyed by platform
        analytics = {}
        for row in response.data:
            platform = row.get("platform", "unknown")
            analytics[platform] = row

        return analytics
