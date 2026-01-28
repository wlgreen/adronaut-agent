from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List


def compute_inputs_hash(uploaded_files: List[Dict[str, Any]]) -> str:
    # Hash the metadata that identifies inputs; stable ordering.
    normalized = [
        {
            "storage_path": f.get("storage_path"),
            "original_filename": f.get("original_filename"),
        }
        for f in (uploaded_files or [])
        if isinstance(f, dict)
    ]
    blob = json.dumps(normalized, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
