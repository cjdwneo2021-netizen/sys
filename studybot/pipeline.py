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
            prompt = ("강의 일부를 핵심 개념, 구체적인 실습, 원본 질문 순서로 정리하라. "
                      "개념 이름만 나열하지 말고 입력 → 적용 규칙 → 단계별 결과를 보존하라. "
                      "코드가 있으면 원본 코드를, 표가 있으면 열 이름과 대표 행의 실제 수치를 인용하라. "
                      "DTM 같은 행렬은 행·열의 의미, 변수 선정 기준, 반복 단어의 빈도를 보존하라. "
                      "빈 학생 답안, 제공된 예시 답안, 실제 작성된 답안을 구분하라. "
                      "누락된 결과나 모순된 단계 표시는 추정으로 채우지 말고 명시하라. "
                      "설명과 예시마다 [SOURCE 실제ID]를 붙이고 원본 질문, 실패한 시도와 불확실성을 "
                      "보존하라. markdown, concepts, questions를 반환하라.\n" + text)
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
                body = json.dumps(group, ensure_ascii=False, sort_keys=True)
                prompt = ("부분 노트를 중복 없이 합쳐라. 구체적인 실습의 입력, 변환 규칙, 단계별 결과, "
                          "표의 열 이름과 대표 행 수치를 일반적인 개요로 축약하지 말고 보존하라. "
                          "주요 개념, 원본 질문, 빈 답안과 예시의 구분, 불확실성, "
                          "본문의 [SOURCE 실제ID]를 보존하라.\n" + body)
                merged.append(generator.request({**base, "stage": "reduce", "level": level, "body": body},
                                                prompt, allowed))
            partials, level = merged, level + 1
        body = json.dumps(partials, ensure_ascii=False, sort_keys=True)
        memory_instruction = (
            "제공된 이전 기억에서 실제로 관련된 내용만 '이전 강의 참고'로 표시하고 강의 ID를 붙여라. "
            if context["memory"].strip() else
            "이전 기억이 없다. '이전 강의 참고' 항목이나 이전에 배웠다는 서술을 만들지 마라. ")
        prompt = (f"강의 제목: {manifest['title']}\n"
                  "핵심 개념, 실습, 질문, 복습 체크리스트를 갖춘 한국어 공부 노트를 작성하라. "
                  "원본만으로 복습할 수 있도록 실제 입력과 단계별 변환 결과를 설명하고, "
                  "표가 있으면 대표 행의 열 이름과 수치를 포함하라. "
                  "반복 단어의 빈도와 변수 선정 과정을 설명하라. 일반적인 개요만 쓰지 마라. "
                  "빈 학생 답안은 미작성으로, 제공된 정답은 예시로 표시하라. "
                  "원본 질문을 보존하고 추가 질문은 AI 복습 질문으로 구분하라. "
                  "각 원본 설명·예시에 [SOURCE 실제ID]를 붙이고 누락·모순을 명시하라. "
                  "강의 내용과 AI 보충 설명을 표시하고 코드 수정 제안은 원본과 구분하라. "
                  + memory_instruction + "concepts에는 이번 강의의 SOURCE ID로 "
                  "뒷받침되는 개념만 넣어라.\n"
                  f"\n이전 기억:\n{context['memory']}\n\n이번 강의:\n{body}")
        note = generator.request({**base, "stage": "final", "revision": revision,
                                  "body": body, "memory": context["memory"]}, prompt, allowed)
        write_json(result_path, {"id": lecture_id, "title": manifest["title"], "revision": revision,
                                "source_fingerprint": manifest["fingerprint"], "prompt_version": PROMPT_VERSION,
                                "note": note, "sources": source_refs})
        completed.append(lecture_id)
    return completed
