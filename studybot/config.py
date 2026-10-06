from dataclasses import dataclass
import os
from pathlib import Path

@dataclass(frozen=True)
class Config:
    root: Path
    folder_id: str = ""
    idle_seconds: int = 2700
    max_file_bytes: int = 10 * 1024 * 1024
    max_lecture_bytes: int = 30 * 1024 * 1024
    max_source_chars: int = 200_000
    chunk_chars: int = 6000
    max_calls: int = 8
    daily_calls: int = 32
    deadline_seconds: int = 1500
    provider: str = "gemini"
    model: str = ""

    @classmethod
    def from_env(cls, root):
        def positive(name, default):
            result = int(os.getenv(name, str(default)))
            if result < 1:
                raise ValueError(f"{name} must be positive")
            return result
        return cls(root=Path(root).resolve(), folder_id=os.getenv("DRIVE_FOLDER_ID", ""),
                   idle_seconds=positive("IDLE_SECONDS", 2700),
                   max_calls=positive("MAX_MODEL_CALLS", 8),
                   daily_calls=positive("MAX_DAILY_MODEL_CALLS", 32),
                   deadline_seconds=positive("MODEL_DEADLINE_SECONDS", 1500),
                   provider=os.getenv("MODEL_PROVIDER", "gemini"), model=os.getenv("MODEL_NAME", ""))
