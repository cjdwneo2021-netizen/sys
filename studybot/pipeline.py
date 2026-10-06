import json
import re

from .extract import PROMPT_VERSION, chunks, extract_sources
from .model import Generator
from .storage import digest, read_json, write_json

def words(text):
    return set(re.findall(r"[a-z0-9_가-힣]{2,}", text.lower()))

def related_memory(root, text, excluded_id):
    query, ranked = words(text), []
    for path in sorted((root / "state/results").glob("*.json")):
        if path.stem == excluded_id:
            continue
        result = read_json(path)
        for concept in result["note"]["concepts"]:
            excerpt = concept["name"] + ": " + concept["explanation"]
            score = len(query & words(excerpt))
            if score:
                ranked.append((score, path.stem, excerpt))
    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    return "\n".join(f"[이전 강의 {lecture}] {text}" for _, lecture, text in ranked[:8])[:6000]

def generate_notes(config, generator=None):
    generator = generator or Generator(config)
    completed = []
    for path in sorted((config.root / "materials").glob("*/manifest.json")):
        manifest = read_json(path)
        lecture_id = manifest["id"]
        sources = extract_sources(config.root, manifest)
        if not sources:
            continue
        if sum(len(source["text"]) for source in sources) > config.max_source_chars:
            raise ValueError("Lecture text too long; split the lecture folder")
        semantic_sources = [{key: source[key] for key in ("id", "label", "text")} for source in sources]
        revision = digest({"title": manifest["title"], "sources": semantic_sources,
                           "provider": config.provider, "model": config.model, "prompt": PROMPT_VERSION})
        result_path = config.root / "state/results" / (lecture_id + ".json")
        source_refs = [{key: source[key] for key in ("id", "label", "path")} for source in sources]
        previous = read_json(result_path, {})
        if previous.get("revision") == revision:
            previous.update(source_fingerprint=manifest["fingerprint"], sources=source_refs)
            write_json(result_path, previous)
            continue
        allowed = {source["id"] for source in sources}
        base = {"provider": config.provider, "model": config.model, "prompt_version": PROMPT_VERSION}
        partials = []
        for text in chunks(sources, config.chunk_chars):
            prompt = ("강의 일부를 핵심 개념, 원본 실습 코드, 질문 순서로 정리하라. "
                      "실패한 시도와 불확실성을 보존하라. markdown, concepts, questions를 반환하라.\n" + text)
            partials.append(generator.request({**base, "stage": "extract", "text": text}, prompt, allowed))
        context_path = config.root / "state/contexts" / (revision + ".json")
        context = read_json(context_path)
        if context is None:
            context = {"memory": related_memory(config.root, manifest["title"] + " " +
                       " ".join(source["text"][:1000] for source in sources[:10]), lecture_id)}
            write_json(context_path, context)
        level = 0
        while len(partials) > 3:
            merged = []
            for start in range(0, len(partials), 3):
                group = partials[start:start + 3]
                if len(group) == 1:
                    merged.extend(group)
                    continue
                body = json.dumps(group, ensure_ascii=False)
                prompt = "부분 노트를 중복 없이 합치고 주요 개념, 질문, SOURCE ID를 보존하라.\n" + body
                merged.append(generator.request({**base, "stage": "reduce", "level": level, "body": body},
                                                prompt, allowed))
            partials, level = merged, level + 1
        body = json.dumps(partials, ensure_ascii=False)
        prompt = (f"강의 제목: {manifest['title']}\n"
                  "핵심 개념, 실습, 질문, 복습 체크리스트를 갖춘 한국어 공부 노트를 작성하라. "
                  "강의 내용과 AI 보충 설명을 표시하고 코드 수정 제안은 원본과 구분하라. "
                  "이전 기억은 '이전 강의 참고'로 표시하라. concepts에는 이번 강의의 SOURCE ID로 "
                  "뒷받침되는 개념만 넣어라.\n"
                  f"\n이전 기억:\n{context['memory']}\n\n이번 강의:\n{body}")
        note = generator.request({**base, "stage": "final", "revision": revision,
                                  "body": body, "memory": context["memory"]}, prompt, allowed)
        write_json(result_path, {"id": lecture_id, "title": manifest["title"], "revision": revision,
                                "source_fingerprint": manifest["fingerprint"], "note": note, "sources": source_refs})
        completed.append(lecture_id)
    return completed
