"""LLM record/replay wrappers.

Purpose
- Make eval runs reproducible even with real models.
- Persist a trace of every LLM call (prompt + response) for debugging.

Design
- Keyed by a stable hash of (mode, task_name, system_instruction, prompt).
- Record format: JSON Lines (one object per call).
- Replay mode: load JSONL into a dict and return the previously recorded output.

This is intentionally small and dependency-free.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


def _norm(s: Optional[str]) -> str:
    return "" if s is None else str(s)


def make_call_key(*, kind: str, task_name: str, system_instruction: Optional[str], prompt: str) -> str:
    payload = json.dumps(
        {
            "kind": kind,
            "task_name": task_name,
            "system_instruction": _norm(system_instruction),
            "prompt": prompt,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class RecordingLLM:
    """Wrapper that records calls to an underlying client."""

    inner: Any
    record_path: Path

    def _append(self, obj: Dict[str, Any]) -> None:
        self.record_path.parent.mkdir(parents=True, exist_ok=True)
        with self.record_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def generate_json(self, *, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.0, task_name: str = "JSON Generation", **kwargs: Any) -> Dict[str, Any]:
        key = make_call_key(kind="json", task_name=task_name or "", system_instruction=system_instruction, prompt=prompt)
        t0 = time.time()
        out = self.inner.generate_json(prompt=prompt, system_instruction=system_instruction, temperature=temperature, task_name=task_name, **kwargs)
        dt = time.time() - t0
        self._append(
            {
                "ts": int(time.time()),
                "kind": "json",
                "key": key,
                "task_name": task_name,
                "temperature": temperature,
                "system_instruction": system_instruction,
                "prompt": prompt,
                "response": out,
                "latency_s": round(dt, 4),
            }
        )
        return out

    def generate_text(self, *, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.0, task_name: str = "Text Generation", **kwargs: Any) -> str:
        key = make_call_key(kind="text", task_name=task_name or "", system_instruction=system_instruction, prompt=prompt)
        t0 = time.time()
        out = self.inner.generate_text(prompt=prompt, system_instruction=system_instruction, temperature=temperature, task_name=task_name, **kwargs)
        dt = time.time() - t0
        self._append(
            {
                "ts": int(time.time()),
                "kind": "text",
                "key": key,
                "task_name": task_name,
                "temperature": temperature,
                "system_instruction": system_instruction,
                "prompt": prompt,
                "response": out,
                "latency_s": round(dt, 4),
            }
        )
        return out

    # Passthroughs for other methods if present
    def __getattr__(self, item: str) -> Any:
        return getattr(self.inner, item)


class ReplayLLM:
    """Replay wrapper backed by a JSONL recording."""

    def __init__(self, record_path: Path):
        self.record_path = record_path
        self._index: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if not self.record_path.exists():
            raise FileNotFoundError(f"Replay file not found: {self.record_path}")
        for line in self.record_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            obj = json.loads(line)
            k = obj.get("key")
            if k:
                self._index[k] = obj

    def generate_json(self, *, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.0, task_name: str = "JSON Generation", **kwargs: Any) -> Dict[str, Any]:
        key = make_call_key(kind="json", task_name=task_name or "", system_instruction=system_instruction, prompt=prompt)
        obj = self._index.get(key)
        if not obj:
            raise KeyError(f"Replay miss for key={key} task_name={task_name}")
        resp = obj.get("response")
        if not isinstance(resp, dict):
            raise ValueError(f"Replay response for key={key} is not a dict")
        return resp

    def generate_text(self, *, prompt: str, system_instruction: Optional[str] = None, temperature: float = 0.0, task_name: str = "Text Generation", **kwargs: Any) -> str:
        key = make_call_key(kind="text", task_name=task_name or "", system_instruction=system_instruction, prompt=prompt)
        obj = self._index.get(key)
        if not obj:
            raise KeyError(f"Replay miss for key={key} task_name={task_name}")
        resp = obj.get("response")
        if not isinstance(resp, str):
            # allow non-str by coercion
            return str(resp)
        return resp


def maybe_wrap_record_replay(client: Any) -> Any:
    """Wrap a client with replay and/or recording, controlled by env vars.

    Env vars:
    - ADRONAUT_LLM_REPLAY_PATH: path to JSONL trace to replay from
    - ADRONAUT_LLM_RECORD_PATH: path to JSONL trace to append to

    You can enable both: replay first (deterministic), record still writes what was replayed.
    """
    replay = os.getenv("ADRONAUT_LLM_REPLAY_PATH")
    record = os.getenv("ADRONAUT_LLM_RECORD_PATH")

    out = client
    if replay:
        out = ReplayLLM(Path(replay).expanduser().resolve())
    if record:
        out = RecordingLLM(out, Path(record).expanduser().resolve())
    return out
