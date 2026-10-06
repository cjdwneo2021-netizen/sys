"""Deterministic Markdown graph, README and portable download bundles."""
from io import BytesIO
import json
import os
import re
import unicodedata
from urllib.parse import quote
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from .storage import digest, label, read_json, write_bytes, write_text

START, END = "<!-- studybot:start -->", "<!-- studybot:end -->"

def concept_key(name):
    name = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", name).strip().casefold())
    return digest(name)[:20]

def package(entries):
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            info = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, data)
    return buffer.getvalue()

def render(root):
    results = [read_json(path) for path in sorted((root / "state/results").glob("*.json"))]
    results.sort(key=lambda item: (item["title"], item["id"]))
    rows, concepts, questions = [], {}, []
    for result in results:
        lecture_id, title, note = result["id"], result["title"], result["note"]
        manifest = read_json(root / "materials" / lecture_id / "manifest.json", {})
        stale = manifest.get("fingerprint") != result["source_fingerprint"]
        status = "업데이트 대기" if stale else "보기"
        body = "# " + label(title) + "\n\n" + note["markdown"] + "\n\n## 원본 근거\n\n"
        for source in result["sources"]:
            href = "../" + quote(source["path"], safe="/")
            body += f'- [{label(source["label"])}]({href}) — \x60{source["id"]}\x60\n'
        body += "\n## 관련 개념\n\n"
        for concept in note["concepts"]:
            key = concept_key(concept["name"])
            body += f'- [{label(concept["name"])}](../memory/concepts/{key}.md)\n'
            concepts.setdefault(key, {"name": concept["name"], "mentions": []})["mentions"].append((result, concept))
        write_text(root / "notes" / (lecture_id + ".md"), body)
        repository = os.getenv("GITHUB_REPOSITORY", "")
        branch = os.getenv("GITHUB_REF_NAME", "main")
        portable = body
        if repository:
            base = f"https://github.com/{repository}/blob/{quote(branch, safe='')}/"
            portable = body.replace("](../materials/", "](" + base + "materials/").replace(
                                   "](../memory/", "](" + base + "memory/")
        bundle = package({"study-note.md": portable.encode(), "sources.json":
                          json.dumps(result["sources"], ensure_ascii=False, indent=2).encode()})
        write_bytes(root / "downloads" / (lecture_id + ".zip"), bundle)
        rows.append(f'| {label(title)} | [{status}](notes/{lecture_id}.md) | '
                    f'[원본 목록](materials/{lecture_id}/manifest.json) | '
                    f'[ZIP](downloads/{lecture_id}.zip?raw=true) |')
        questions.append(f'## [{label(title)}](../notes/{lecture_id}.md)\n\n' +
                         "\n".join("- " + question for question in note["questions"]))
    for key, concept in sorted(concepts.items()):
        text, neighbors = "# " + label(concept["name"]) + "\n\n", set()
        for result, mention in concept["mentions"]:
            text += f'## [{label(result["title"])}](../../notes/{result["id"]}.md)\n\n'
            text += mention["explanation"] + "\n\n출처: " + ", ".join(mention["source_ids"]) + "\n\n"
            neighbors.update((concept_key(c["name"]), c["name"]) for c in result["note"]["concepts"]
                             if concept_key(c["name"]) != key)
        text += "## 같은 강의에서 다룬 개념\n\n" + "\n".join(
            f"- [{label(name)}]({other}.md)" for other, name in sorted(neighbors))
        write_text(root / "memory/concepts" / (key + ".md"), text + "\n")
    for path in (root / "memory/concepts").glob("*.md"):
        if re.fullmatch(r"[0-9a-f]{20}", path.stem) and path.stem not in concepts:
            path.unlink()
    write_text(root / "memory/index.md", "# 개념 기억\n\n" + "\n".join(
        f'- [{label(value["name"])}](concepts/{key}.md)' for key, value in sorted(concepts.items())) + "\n")
    write_text(root / "memory/questions.md", "# 질문 기록\n\n" + "\n\n".join(questions) + "\n")
    table = ("| 강의 | 공부 노트 | 원본 | 다운로드 |\n|---|---|---|---|\n" +
             "\n".join(rows)) if rows else "아직 생성된 공부 노트가 없습니다."
    generated = START + "\n\n" + table + "\n\n[개념 기억](memory/index.md) · [질문 기록](memory/questions.md)\n\n" + END
    path = root / "README.md"
    readme = path.read_text("utf-8") if path.exists() else "# StudyBot\n"
    if START in readme and END in readme and readme.index(START) < readme.index(END):
        readme = readme[:readme.index(START)] + generated + readme[readme.index(END) + len(END):]
    else:
        readme += "\n\n" + generated + "\n"
    write_text(path, readme)
