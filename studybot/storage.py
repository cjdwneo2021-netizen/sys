"""Deterministic files and safe identifiers."""
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()

def read_json(path, default=None):
    return json.loads(path.read_text("utf-8")) if path.exists() else default

def write_bytes(path, content):
    if path.exists() and path.read_bytes() == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)

def write_text(path, content):
    write_bytes(path, content.encode("utf-8"))

def write_json(path, content):
    write_text(path, json.dumps(content, ensure_ascii=False, sort_keys=True, indent=2) + "\n")

def checked_id(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", value):
        raise ValueError("Invalid source ID")
    return value

def safe_name(value):
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"[^a-zA-Z0-9가-힣._ -]", "_", value).strip(" .")[:100] or "file"

def label(value):
    return str(value).replace("\n", " ").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")

def contained(root, relative):
    """Resolve a managed relative path without allowing escapes or absolute paths."""
    path = Path(relative)
    candidate = (root / path).resolve()
    if path.is_absolute() or not candidate.is_relative_to(root.resolve()):
        raise ValueError("Path escapes repository")
    return candidate
