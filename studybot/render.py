"""Deterministic Markdown graph, README and portable download bundles."""
from io import BytesIO
import json
import os
import re
import unicodedata
from urllib.parse import quote
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from .config import Config
from .extract import PROMPT_VERSION
from .storage import digest, label, read_json, write_bytes, write_text

START, END = "<!-- studybot:start -->", "<!-- studybot:end -->"
STATUS_START, STATUS_END = "<!-- studybot:status:start -->", "<!-- studybot:status:end -->"


def operational_status(root, results, concept_count):
    operations = read_json(root / "state/operations.json", {})
    usage = read_json(root / "state/usage.json", {"days": {}})
    budget = read_json(root / "state/budget.json", {})
    run = usage.get("last_run", {})
    latest = max(operations.values(), key=lambda item: item["at"], default={})
    run_time = run.get("finished_at") or run.get("updated_at") or run.get("started_at", "")
    if run_time > latest.get("at", ""):
        latest = {"at": run_time, "settings": run.get("settings")}
    recorded = latest.get("settings") or run.get("settings")
    defaults = Config(root)
    limits = recorded or {"max_calls": defaults.max_calls, "daily_calls": defaults.daily_calls,
                          "idle_seconds": defaults.idle_seconds, "deadline_seconds": defaults.deadline_seconds}
    basis = latest.get("at") or run.get("finished_at") or run.get("started_at")
    date = (basis[:10] if basis else budget.get("date"))
    days = dict(usage["days"])
    if budget.get("date") and budget["date"] not in days:
        days[budget["date"]] = {"attempts": budget["calls"], "unknown": budget["calls"],
                                "completed": 0, "errors": 0}
    elif budget.get("date"):
        days[budget["date"]] = {**days[budget["date"]],
                                "attempts": max(budget["calls"], days[budget["date"]]["attempts"])}
    day = days.get(date, {"attempts": 0})
    attempts = day["attempts"]
    remaining = max(0, limits["daily_calls"] - attempts)
    manifests = {path.parent.name: read_json(path)
                 for path in (root / "materials").glob("*/manifest.json")}
    by_id = {result["id"]: result for result in results}
    pending = sum(lecture not in by_id or
                  manifest["fingerprint"] != by_id[lecture]["source_fingerprint"] or
                  by_id[lecture].get("prompt_version", "lecture-v1") != PROMPT_VERSION
                  for lecture, manifest in manifests.items())
    observed = read_json(root / "state/drive.json", {}).get("observed", {})
    waiting = sum(lecture not in manifests or entry["fingerprint"] != manifests[lecture]["fingerprint"]
                  for lecture, entry in observed.items())
    statuses = {"completed": "완료", "failed": "실패", "deferred": "재개 대기", "running": "진행 중"}
    reasons = {"run_limit": "실행당 자체 호출 한도", "daily_limit": "자체 일일 호출 한도",
               "time_limit": "모델 처리 시간 한도", "provider_limit": "제공업체 한도 또는 일시적 서비스 오류"}

    def operation_text(name):
        entry = operations.get(name)
        if name == "build" and run_time > (entry or {}).get("at", ""):
            entry = {"at": run_time, "status": run["status"], "count": run.get("generated")}
        if not entry:
            return "미기록"
        count = f" · {entry['count']}건" if entry.get("count") is not None else ""
        state = "완료 미확인 (실행 중 또는 중단)" if entry["status"] == "running" else statuses.get(entry["status"], entry["status"])
        value = f"{state}{count} · {entry['at']}"
        if entry.get("run_url"):
            value += f" · [실행 로그]({entry['run_url']})"
        return value

    rows = [
        ("기준 시각 (UTC)", basis or (f"{date} · 호출 기록 날짜만 보관" if date else "실행 기록 없음")),
        ("설정 출처", "최근 실행에서 저장한 설정" if recorded else "코드 기본값 · 실제 실행 설정 미기록"),
        ("모델", f"{label(recorded['provider'])} / {label(recorded['model'] or '모델명 미설정')}" if recorded else "실행 설정 미기록"),
        (f"기준일 호출 시도 ({date or '미기록'} UTC)", f"{attempts} / {limits['daily_calls']}회"),
        ("기준일 남은 자체 일일 예산", f"{remaining}회" + (" (기본 한도 기준)" if not recorded else "")),
        ("실행당 자체 호출 한도", f"{limits['max_calls']}회"),
        ("마지막 build 호출", (f"시도 {run['attempts']} · 응답 검증 완료 {run['completed']} · "
                                  f"오류 {run['errors']} · 캐시 재사용 {run['cache_hits']}회") if run else "미기록"),
        ("마지막 자료 수집", operation_text("sync")),
        ("마지막 노트 생성", operation_text("build")),
        ("마지막 build 재개 대기 사유", reasons.get(run.get("deferred_reason"), "해당 없음" if run else "미기록")),
        ("자료 처리", f"수집된 자료 {len(manifests)}건 · 생성/갱신 대기 {pending}건 · 안정성 관찰 대기 {waiting}건"),
        ("생성 결과", f"노트 {len(results)}건 · 개념 {concept_count}개 · ZIP {len(list((root / 'downloads').glob('*.zip')))}개"),
        ("안정 대기 / 모델 처리 시간 한도", f"{limits['idle_seconds']}초 / {limits['deadline_seconds']}초"),
        ("토큰·실제 요금·제공업체 잔여 한도", "미수집 · [AI Studio](https://aistudio.google.com/usage)에서 확인"),
    ]
    text = STATUS_START + "\n\n## 운영 현황\n\n"
    text += "저장된 실행 시점의 스냅샷입니다. 현재 시각의 실시간 사용량은 아닙니다.\n\n"
    text += "| 확인 항목 | 기록 |\n|---|---|\n" + "\n".join(f"| {name} | {value} |" for name, value in rows)
    text += "\n\n### 최근 호출 기록 (UTC, 최대 7일)\n\n"
    if days:
        text += "| 날짜 | 시도 | 응답 검증 완료 | 오류 | 결과 미확인 |\n|---|---:|---:|---:|---:|\n"
        for day_date in sorted(days, reverse=True)[:7]:
            item = days[day_date]
            unknown = item["attempts"] - item["completed"] - item["errors"]
            text += f"| {day_date} | {item['attempts']} | {item['completed']} | {item['errors']} | {unknown} |\n"
    else:
        text += "아직 기록된 API 호출이 없습니다.\n"
    text += ("\n호출 시도에는 한도 오류와 응답 검증 실패도 포함하며 캐시 재사용은 제외합니다. "
             "이전 기록은 시도 횟수만 복원하므로 결과 미확인으로 표시합니다. "
             "새 기록은 호출 전후에 저장하며, 호출 도중 중단되면 결과 미확인으로 남습니다. "
             "다른 앱의 호출은 포함하지 않습니다. 자체 예산은 제공업체 할당량과 별개이며 UTC 날짜가 바뀌면 초기화됩니다.\n\n")
    links = [f"[{name}]({relative})" for name, relative in (
        ("호출 기록", "state/usage.json"), ("실행 상태", "state/operations.json"))
        if (root / relative).exists()]
    text += " · ".join(links + ["[처리 체크포인트](state/)"]) + "\n\n" + STATUS_END
    return text

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
    status = operational_status(root, results, len(concepts))
    if STATUS_START in readme and STATUS_END in readme and readme.index(STATUS_START) < readme.index(STATUS_END):
        readme = readme[:readme.index(STATUS_START)] + status + readme[readme.index(STATUS_END) + len(STATUS_END):]
    elif "## 공부 노트" in readme:
        readme = readme.replace("## 공부 노트", status + "\n\n## 공부 노트", 1)
    else:
        readme += "\n\n" + status + "\n"
    if START in readme and END in readme and readme.index(START) < readme.index(END):
        readme = readme[:readme.index(START)] + generated + readme[readme.index(END) + len(END):]
    else:
        readme += "\n\n" + generated + "\n"
    write_text(path, readme)
