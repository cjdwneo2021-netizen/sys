"""Read-only Drive v3 import. Stable snapshots are immutable."""
from datetime import datetime, timezone
import hashlib
import os
from urllib.parse import quote

from .storage import checked_id, digest, read_json, safe_name, write_bytes, write_json

FOLDER = "application/vnd.google-apps.folder"
DOC = "application/vnd.google-apps.document"
API = "https://www.googleapis.com/drive/v3"
FIELDS = "id,name,mimeType,modifiedTime,version,size,md5Checksum"
KNOWN_FIELDS = ("id", "name", "mimeType", "modifiedTime", "version", "size", "md5Checksum", "relative")

class Unstable(Exception):
    pass

class Drive:
    def __init__(self, session=None):
        if session is not None:
            self.session = session
        elif os.getenv("DRIVE_ACCESS_TOKEN"):
            import requests
            self.session = requests.Session()
            self.session.headers["Authorization"] = "Bearer " + os.environ["DRIVE_ACCESS_TOKEN"]
        else:
            import google.auth
            from google.auth.transport.requests import AuthorizedSession
            creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/drive.readonly"])
            self.session = AuthorizedSession(creds)

    def get(self, path, **params):
        response = self.session.get(API + path, params=params, timeout=60)
        response.raise_for_status()
        return response.json()

    def info(self, file_id):
        return self.get("/files/" + checked_id(file_id), fields=FIELDS, supportsAllDrives="true")

    def children(self, folder_id):
        token = None
        while True:
            params = dict(q=f"'{checked_id(folder_id)}' in parents and trashed = false",
                          fields=f"nextPageToken,files({FIELDS})", pageSize=1000,
                          supportsAllDrives="true", includeItemsFromAllDrives="true")
            if token:
                params["pageToken"] = token
            result = self.get("/files", **params)
            yield from result.get("files", [])
            token = result.get("nextPageToken")
            if not token:
                return

    def tree(self, folder_id, prefix="", depth=0):
        if depth > 12:
            raise ValueError("Folder nesting exceeds 12")
        items = []
        for item in self.children(folder_id):
            relative = prefix + item["name"]
            if item["mimeType"] == FOLDER:
                items.extend(self.tree(item["id"], relative + "/", depth + 1))
            else:
                items.append(dict(item, relative=relative))
        return sorted(items, key=lambda item: item["id"])

    def download(self, item, limit):
        if item["mimeType"] == DOC:
            path = "/files/" + checked_id(item["id"]) + "/export"
            params = {"mimeType": "text/plain"}
        else:
            path = "/files/" + checked_id(item["id"])
            params = {"alt": "media", "supportsAllDrives": "true"}
        with self.session.get(API + path, params=params, stream=True, timeout=60) as response:
            response.raise_for_status()
            parts, size = [], 0
            for part in response.iter_content(64 * 1024):
                size += len(part)
                if size > limit:
                    raise ValueError("File exceeds download limit")
                parts.append(part)
            return b"".join(parts)

def fingerprint(items, title):
    return digest({"title": title, "files": [
        {key: item[key] for key in KNOWN_FIELDS if key in item}
        for item in sorted(items, key=lambda item: item["id"])]})

def modified_time(items):
    return max((datetime.fromisoformat(item["modifiedTime"].replace("Z", "+00:00")).timestamp()
                for item in items), default=0)

def downloadable(item):
    mime = item["mimeType"]
    # Colab's application/vnd.google.colaboratory is downloadable notebook JSON.
    return not mime.startswith("application/vnd.google-apps.") or mime == DOC

def synchronize(config, drive, now=None):
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    state_path = config.root / "state/drive.json"
    state = read_json(state_path, {"observed": {}})
    if drive.info(config.folder_id)["mimeType"] != FOLDER:
        raise ValueError("DRIVE_FOLDER_ID must refer to a folder")
    imported = []
    try:
        for lecture in sorted(drive.children(config.folder_id), key=lambda item: item["id"]):
            root_file = lecture["mimeType"] != FOLDER
            lecture_id = checked_id(lecture["id"])
            items = [dict(lecture, relative=lecture["name"])] if root_file else drive.tree(lecture_id)
            if any(item["name"] == ".studybot-busy" for item in items):
                continue
            current = fingerprint(items, lecture["name"])
            previous = state["observed"].get(lecture_id, {})
            if previous.get("fingerprint") != current:
                state["observed"][lecture_id] = {"fingerprint": current, "first_seen": now}
                continue
            if now - max(previous["first_seen"], modified_time(items)) < config.idle_seconds:
                continue
            manifest_path = config.root / "materials" / lecture_id / "manifest.json"
            if read_json(manifest_path, {}).get("fingerprint") == current:
                continue
            entries, pending, total = [], {}, 0
            stable = True
            for item in items:
                entry = {"id": item["id"], "name": item["relative"], "mime_type": item["mimeType"],
                         "version": item.get("version"), "modified": item["modifiedTime"],
                         "url": "https://drive.google.com/file/d/" + quote(item["id"], safe="") + "/view"}
                if not downloadable(item) or int(item.get("size", 0)) > config.max_file_bytes:
                    entry["status"] = "link_only"
                else:
                    data = drive.download(item, config.max_file_bytes)
                    total += len(data)
                    if total > config.max_lecture_bytes:
                        raise ValueError("Lecture exceeds download limit; split the folder")
                    after = drive.info(item["id"])
                    if any(after.get(key) != item.get(key) for key in ("version", "modifiedTime", "md5Checksum")):
                        stable = False
                        break
                    local = checked_id(item["id"]) + "--" + safe_name(item["name"])
                    if item["mimeType"] == DOC:
                        local += ".txt"
                    relative = f"materials/{lecture_id}/snapshots/{current}/{local}"
                    entry.update(path=relative, sha256=hashlib.sha256(data).hexdigest(), status="downloaded")
                    pending[relative] = data
                entries.append(entry)
            if not stable:
                continue
            latest = drive.info(lecture_id)
            latest_items = [dict(latest, relative=latest["name"])] if root_file else drive.tree(lecture_id)
            if fingerprint(latest_items, latest["name"]) != current:
                continue
            for relative, data in pending.items():
                write_bytes(config.root / relative, data)
            write_json(manifest_path, {"id": lecture_id, "title": lecture["name"],
                                     "fingerprint": current, "files": entries})
            imported.append(lecture_id)
    finally:
        write_json(state_path, state)
    return imported
