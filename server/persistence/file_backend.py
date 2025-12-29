"""
File-based JSON storage backend.
Handles low-level file operations for session persistence.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

# Default data directory (relative to server/)
DEFAULT_DATA_DIR = Path(__file__).parent.parent / "data"


class FileBackend:
    """
    Low-level file operations for JSON storage.
    Thread-safe for basic operations.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.sessions_dir = self.data_dir / "sessions"
        self._ensure_directories()

    def _ensure_directories(self):
        """Create data directories if they don't exist."""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        # Sanitize session_id to prevent directory traversal
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return self.sessions_dir / f"{safe_id}.json"

    def read_json(self, path: Path) -> Optional[dict]:
        """Read a JSON file, return None if not found."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")

    def write_json(self, path: Path, data: dict) -> None:
        """Write data to a JSON file atomically."""
        # Write to temp file first, then rename (atomic on POSIX)
        temp_path = path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=self._json_serializer)
            temp_path.rename(path)
        except Exception:
            # Clean up temp file on failure
            if temp_path.exists():
                temp_path.unlink()
            raise

    def delete_file(self, path: Path) -> bool:
        """Delete a file, return True if deleted."""
        try:
            path.unlink()
            return True
        except FileNotFoundError:
            return False

    def list_files(self, directory: Path, suffix: str = ".json") -> list[str]:
        """List files in a directory with given suffix."""
        if not directory.exists():
            return []
        return [f.stem for f in directory.iterdir() if f.suffix == suffix]

    def _json_serializer(self, obj):
        """Custom JSON serializer for datetime and other types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    # =========================================================================
    # Session-specific operations
    # =========================================================================

    def read_session(self, session_id: str) -> Optional[dict]:
        """Read a session by ID."""
        return self.read_json(self._session_path(session_id))

    def write_session(self, session_id: str, data: dict) -> None:
        """Write a session by ID."""
        self.write_json(self._session_path(session_id), data)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        return self.delete_file(self._session_path(session_id))

    def list_sessions(self) -> list[str]:
        """List all session IDs."""
        return self.list_files(self.sessions_dir)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self._session_path(session_id).exists()
