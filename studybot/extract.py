import json
from pathlib import Path

from .storage import contained

PROMPT_VERSION = "lecture-v1"

def extract_sources(root, manifest):
    """Never execute source code. Cell order and textual error output are preserved."""
    result = []
    for entry in manifest["files"]:
        if entry.get("status") != "downloaded":
            continue
        path = contained(root, entry["path"])
        suffix = path.suffix.lower()
        def add(source_id, label, text):
            if text.strip():
                result.append({"id": source_id, "label": label, "path": entry["path"], "text": text})
        if suffix == ".ipynb":
            notebook = json.loads(path.read_text("utf-8-sig"))
            for index, cell in enumerate(notebook.get("cells", []), 1):
                if cell.get("cell_type") not in ("code", "markdown", "raw"):
                    continue
                source_id = f'{entry["id"]}:cell-{index}'
                source = cell.get("source", "")
                source = "".join(source) if isinstance(source, list) else source
                add(source_id, f'{entry["name"]} / cell {index} ({cell["cell_type"]})', source)
                for position, output in enumerate(cell.get("outputs", []), 1):
                    text = output.get("text") or output.get("data", {}).get("text/plain")
                    if output.get("output_type") == "error":
                        text = f'{output.get("ename", "")}: {output.get("evalue", "")}'
                    if isinstance(text, list):
                        text = "".join(text)
                    if text:
                        if len(text) > 1500:
                            text = text[:1500] + "\n[나머지 실행 출력은 원본에 보관]"
                        add(f"{source_id}:output-{position}",
                            f'{entry["name"]} / cell {index} output {position}', text)
        elif suffix in (".txt", ".md", ".py"):
            add(entry["id"], entry["name"], path.read_text("utf-8-sig"))
    return result

def chunks(sources, limit=6000):
    result, current = [], ""
    for source in sources:
        prefix = f'\n[SOURCE {source["id"]}] {source["label"]}\n'
        capacity = limit - len(prefix) - 1
        if capacity < 100:
            raise ValueError("Source label too long for chunk")
        for start in range(0, len(source["text"]), capacity):
            part = prefix + source["text"][start:start + capacity]
            if current and len(current) + len(part) > limit:
                result.append(current)
                current = ""
            current += part
    if current:
        result.append(current)
    return result
