"""Local file manager.

In local-only demo mode, we avoid Supabase Storage entirely.

We keep the same public API (upload_file/download_file/file_exists) so the rest
of the agent can stay mostly unchanged.

Storage layout (under ADRONAUT_HOME):
- $ADRONAUT_HOME/projects/<project_id>/inputs/uploaded/<filename>

"storage_path" is a path to the stored file (absolute by default).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

from .paths import project_inputs_dir


class FileManager:
    @staticmethod
    def upload_file(local_path: str, project_id: str) -> str:
        """Copy a local file into the project storage area.

        Returns a storage_path (repo-relative) that can be used later.
        """
        src = Path(local_path).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(f"File not found: {local_path}")
        if not src.is_file():
            raise ValueError(f"Not a file: {local_path}")

        dst_dir = project_inputs_dir(project_id) / "uploaded"
        dst_dir.mkdir(parents=True, exist_ok=True)

        dst = dst_dir / src.name
        shutil.copy2(src, dst)

        # Return absolute path for robustness across working directories
        return str(dst)

    @staticmethod
    def download_file(storage_path: str, local_dir: str = "/tmp") -> str:
        """Copy from project storage into local_dir and return the local path.

        If storage_path is already an absolute path that exists, we just return it.
        """
        p = Path(storage_path)
        if p.is_absolute() and p.exists():
            return str(p)

        src = Path(storage_path).expanduser()
        if not src.is_absolute():
            # treat as relative to ADRONAUT_HOME
            from .paths import adronaut_home

            src = (adronaut_home() / storage_path).resolve()
        else:
            src = src.resolve()

        if not src.exists():
            raise FileNotFoundError(f"Stored file not found: {storage_path}")

        local_dir_p = Path(local_dir).expanduser().resolve()
        local_dir_p.mkdir(parents=True, exist_ok=True)
        dst = local_dir_p / src.name
        shutil.copy2(src, dst)
        return str(dst)

    @staticmethod
    def file_exists(storage_path: str) -> bool:
        p = Path(storage_path)
        if p.is_absolute():
            return p.exists()
        from .paths import adronaut_home

        return (adronaut_home() / storage_path).exists()

    @staticmethod
    def get_public_url(storage_path: str) -> Optional[str]:
        return None


def upload_file(local_path: str, project_id: str) -> str:
    return FileManager.upload_file(local_path, project_id)


def download_file(storage_path: str, local_dir: str = "/tmp") -> str:
    return FileManager.download_file(storage_path, local_dir)


def file_exists(storage_path: str) -> bool:
    return FileManager.file_exists(storage_path)
